from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.config import bot

import app.kb.client_keyboards as kb

from app.ClientStates import RedactOldOrder

from db import product_requests, optionally_product_requests, order_requests, employee_requests, user_requests
from db.Enums import OrderStatus


router = Router(name=__name__)

@router.callback_query(RedactOldOrder.OrderId, F.data.startswith('order_'))
async def order(callback: types.CallbackQuery, state: FSMContext):
    command = callback.data.split('_')[1]

    await state.update_data(order_id = command)

    order = await order_requests.getOrderById(command)

    await state.set_state(RedactOldOrder.AboutOrder)

    text = await aboutOrderText(order)
    await callback.message.edit_text(
       text,
       reply_markup = kb.order_canceled
    )
    

@router.message(RedactOldOrder.OrderId)
async def order_msg(message: types.Message, state: FSMContext):
    text = message.text

    order = None

    try:
       order = await order_requests.getOrderById(int(text))
       if not order:
          raise ValueError()
    except ValueError:
      await message.delete()
      return
         
       
    await state.update_data(order_id = order.id)

    data = await state.get_data()
    main_msg = data['main_msg']


    text = await aboutOrderText(order)

    await state.set_state(RedactOldOrder.AboutOrder)

    await message.delete()
    await bot.edit_message_text(
      chat_id = message.chat.id,
      message_id = main_msg,
      text = text,
      reply_markup = kb.order_canceled
    )
    
    
@router.callback_query(StateFilter(RedactOldOrder), F.data.startswith('page'))
async def order_page(callback: types.CallbackQuery, state: FSMContext):
    page_num = int(callback.data.split('_')[1])


    if page_num < 0:
       await state.set_state(RedactOldOrder.OrderId)
       await callback.message.edit_text('Ваши заказы:', reply_markup = await kb.orders_inline(callback.from_user.id, 0))
       return
    

    await state.update_data(page_num = page_num)
   
    await callback.message.edit_reply_markup(
      reply_markup = await kb.orders_inline(page_num = page_num, user_id = callback.from_user.id)
    )
    
   

@router.callback_query(RedactOldOrder.AboutOrder, F.data.startswith('active_order'))
async def cancel_activeOrder(callback: types.CallbackQuery, state: FSMContext):
    
    command = callback.data.split('_')[2]
    data = await state.get_data()
    page_num = data['page_num']
    order_id = data['order_id']
    main_msg = data['main_msg']


   
    if command == 'back':
      await state.set_state(RedactOldOrder.OrderId)
      await callback.message.edit_text(f'Ваши заказы:',
                           reply_markup = await kb.orders_inline(callback.from_user.id, page_num))
      return
    
    await state.clear()
    await state.set_state(RedactOldOrder.OrderId)

    await state.update_data(page_num = page_num)
    await state.update_data(main_msg = main_msg)
    
    order = await order_requests.getOrderById(order_id)
    
    if not order:
       await callback.message.edit_text(
          'Такого заказа не существует',
          reply_markup = await kb.orders_inline(callback.from_user.id, page_num)
       )


    if (order.status == OrderStatus.DURING_PROCESSING 
        or order.status == OrderStatus.DURING_PAYMENT
        or order.status == OrderStatus.DURING_VERIFY
    ) :
      await order_requests.updateOrderStatus(order.id, OrderStatus.CANCEL)
      await callback.message.edit_text('Заказ отменен', reply_markup = await kb.orders_inline(callback.from_user.id, page_num))


      employee = await employee_requests.getEmployeeById(order.employee_id)

      if not employee:
         return
      
      user = await user_requests.getUserById(employee.user_id)

      if not user:
         return
      
      await bot.send_message(user.user_id, f'Заказ {order.id} отменен клиентом {order.fio}: {callback.from_user.username}!!')
    else:
      await callback.message.edit_text('Вы не можете отменить заказ, так как он уже отправлен или отменен', reply_markup = await kb.orders_inline(callback.from_user.id, page_num))




async def aboutOrderText(order) -> str:

    if not order:
      return '-'
    

    client = await user_requests.getUserById(order.user_id)
    product = await product_requests.getProductById(order.product_id)
    optionally_product = await optionally_product_requests.getOptionallyProductById(order.optionally_product_id)


    optionally_product_text = ''
    product_text = ''
    sum = (order.product_price*order.product_count)+(order.optionally_product_price*order.optionally_product_count)

    if product:
       product_text = (
          f'<strong>Товар</strong>: {product.id}, {product.name}\n' +
                                     f'Цена товара: {order.product_price}₽\n' +
                                     f'Кол-во товара: {order.product_count}\n' +
                                     f'Всего за товар: {order.product_price*order.product_count}₽\n\n'
       )


    if optionally_product:
      optionally_product_text = (
          f'<strong>Доп. товар</strong>: {optionally_product.id}, {optionally_product.name}\n' +
          f'Цена товара: {order.optionally_product_price}₽\n' +
          f'Кол-во товара: {order.optionally_product_count}\n' +
          f'Всего за доп. товары: {order.optionally_product_price*order.optionally_product_count}₽\n\n'
      )



    created_at = order.created_at.strftime('%Y-%m-%d %H:%M:%S')
    ended_at = order.ended_at.strftime('%Y-%m-%d %H:%M:%S')
    return (
        f'ID заказа: {order.id}\n\n'+
        f'Заказчик: {client.username}\n'+
        f'Имя заказчика: {order.fio}\n'+
        f'Адресс: {order.address}\n'+
        f'Телефон: {order.phone_number}\n\n'+

        product_text +

        optionally_product_text +

        f'<strong>Общая цена</strong>: {sum}₽\n\n' +

        f'Статус: <strong>{order.status.value[0]}</strong>\n' +
        f'Доставка: <strong>{order.delivery_method.value}</strong>\n' +
                                     
        f'Дата заказа: {created_at}\n' +
        f'Дата окончания заказа: {ended_at}'
    )



