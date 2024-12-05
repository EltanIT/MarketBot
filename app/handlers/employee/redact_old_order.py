from aiogram import types, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from app.config import bot

import app.kb.employee_keyboards as kb
from app.kb.client_keyboards import orders_inline, rating_inline
from app.kb.common import products_inline, optionally_products_inline

from db import order_requests, product_requests, optionally_product_requests, user_requests, employee_requests
from db.Enums import OrderStatus

from app.EmployeeStates import AllOrders


import datetime




router = Router(name = __name__)




@router.callback_query(AllOrders.RedactOrder.Individual, F.data == 'redact_individual_cancel')
async def cancel_redact_individual(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AllOrders.RedactOrder.Viewing)

    print('cancel')
    await callback.message.edit_text(
       text = 'Что нужно изменить в заказ?',
       reply_markup = await kb.redact_order_inline(is_payment=None, data = 'order_redact', is_date = True)
    )
   


@router.callback_query(AllOrders.Category, F.data.startswith('order_category'))
async def order_category(callback: types.CallbackQuery, state: FSMContext):
    command = callback.data.split('_')[2]

    await state.set_state(AllOrders.OrderId)
    await state.update_data(page_num = 0)
    await state.update_data(main_msg = callback.message.message_id)
    if command == 'all':
      await state.update_data(employee_id = None)

      await callback.message.edit_text(
         'Вы можете найти заказ, введя имя заказчика.\n\n' +
         'Все заказы:', 
         reply_markup = await kb.orders_inline(page_num = 0)
      )
      return
    
    elif command == 'my':
       await state.update_data(employee_id = callback.from_user.id)
       await callback.message.edit_text(
          'Вы можете найти заказ, введя имя заказчика.\n\n' +
          'Все ваши принятные заказы:', 
          reply_markup = await kb.orders_inline(page_num = 0, user_id = callback.from_user.id)
       )


@router.callback_query(AllOrders.OrderId, F.data.startswith('order'))
async def order(callback: types.CallbackQuery, state: FSMContext):
    command = callback.data.split('_')[1]

    if command == 'cancel':
       await state.set_state(AllOrders.Category)
       await callback.message.edit_text('Какие заказы хотите посмотреть?', reply_markup = kb.orders_categories)
       return
    

    await state.set_state(AllOrders.RedactOrder.Viewing)
   

    await state.update_data(order_id = command)


    order = await order_requests.getOrderById(command)


    await state.update_data(order = order)


    text = await aboutOrderText(order)
    await callback.message.edit_text(
      text,
      reply_markup = kb.redact_old_order
    )
    
@router.message(AllOrders.OrderId)
async def order_msg(message: types.Message, state: FSMContext):
    text = message.text

    order = None

    try:
       order = await order_requests.getOrderById(int(text))
       if not order:
          raise ValueError()
    except ValueError:
      order = await order_requests.findOrderByFio(text)
      if not order:
         await message.delete()
         return
       
    await state.update_data(order_id = order.id)

    data = await state.get_data()
    main_msg = data['main_msg']


    text = await aboutOrderText(order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await message.delete()
    await bot.edit_message_text(
      chat_id = message.chat.id,
      message_id = main_msg,
      text = text,
      reply_markup = kb.redact_old_order
    )
    
    
@router.callback_query(AllOrders.OrderId, F.data.startswith('page'))
async def order_page(callback: types.CallbackQuery, state: FSMContext):
    page_num = int(callback.data.split('_')[1])


    if page_num < 0:
       await state.set_state(AllOrders.Category)
       await callback.message.edit_text('Какие заказы хотите посмотреть?', reply_markup = kb.orders_categories)
       return
    

    await state.update_data(page_num = page_num)


    data = await state.get_data()
    employee_id = data['employee_id']
    
   
    await callback.message.edit_reply_markup(
      reply_markup = await kb.orders_inline(page_num = page_num, user_id = employee_id)
    )
    
    


@router.callback_query(StateFilter(AllOrders.RedactOrder), F.data.startswith('redact_old_order'))
async def redact_order(callback: types.CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    
    command = callback.data.split('_')[3]
    
    if command == 'cancel':
       await state.set_state(AllOrders.OrderId)

       employee_id = data['employee_id'] 
       page_num = data['page_num']

       text = (
            'Вы можете найти заказ, введя имя заказчика.\n\n' +
            'Все ваши принятые заказы'
       )
       if not employee_id:
          text = (
            'Вы можете найти заказ, введя имя заказчика.\n\n' +
            'Все заказы в Telegram'
          )

       await callback.message.edit_text(text, reply_markup = await kb.orders_inline(page_num = page_num, user_id = employee_id))
    elif command == 'status':
    
      await state.set_state(AllOrders.ChangeStatus)

      order_id = data['order_id']

      order = await order_requests.getOrderById(order_id)

      if not order:
        return
      
      await callback.message.edit_reply_markup(reply_markup = await kb.order_statutes(order.status))

    elif command == 'redact':
       await state.set_state(AllOrders.RedactOrder.Viewing)


       order_id = data['order_id']

       order = await order_requests.getOrderById(order_id)

       if not order:
          return
       
       await state.update_data(order = order)

       await callback.message.delete()

       order_msg = await callback.message.answer(
          callback.message.text
       )

       main_msg = await callback.message.answer(
          'Что нужно изменить в заказе?',
          reply_markup = await kb.redact_order_inline(is_payment = None, data = 'order_redact', is_date = True),
          reply_to_message_id = order_msg.message_id
       )

       await state.update_data(main_msg = main_msg.message_id)
       await state.update_data(order_msg = order_msg.message_id)



@router.callback_query(AllOrders.ChangeStatus, F.data.startswith('status'))
async def redact_status(callback: types.CallbackQuery, state: FSMContext):
    
  statusName = callback.data[7:]

  data = await state.get_data()
  order_id = data['order_id']
  employee_id = data['employee_id'] 
  page_num = data['page_num']

  if statusName == 'cancel':
      
      await state.set_state(AllOrders.RedactOrder.Viewing)
    
      order = await order_requests.getOrderById(order_id)

      text = await aboutOrderText(order)
      await callback.message.edit_text(
        text,
        reply_markup = kb.redact_old_order
      )
      return

  statusNames = [e.name for e in OrderStatus]
  statuses = [e for e in OrderStatus]
  if not statusNames:
    return
  index = statusNames.index(statusName)
  status = statuses[index]

  await state.set_state(AllOrders.OrderId)
  
  await order_requests.updateOrderStatus(order_id, status)
    
  await callback.message.delete()
  main_msg = await callback.message.answer(
      f'Статус заказа {order_id} изменился, клиент уведомлен', 
      reply_markup = await kb.orders_inline(page_num = page_num, user_id = employee_id)
   )
  
  await state.update_data(main_msg = main_msg.message_id)

  order = await order_requests.getOrderById(order_id)

  client = await user_requests.getUserById(order.user_id)

  if status == OrderStatus.DELIVERED:
    await bot.send_message(
         client.user_id, f'Заказ {order.id} доставлен!\n'+
         f'Надеемся, что вам все понравилось и вы вернетесь снова!'
    )
    return


  await bot.send_message(
    client.user_id, f'Статус заказа {order_id} сменился на {status.value[0]}')


@router.callback_query(AllOrders.RedactOrder.Viewing, F.data.startswith('order_redact'))
async def redact_order_commands(callback: types.CallbackQuery, state: FSMContext):
   
    command = callback.data.split('_')[2]

    if command == 'product':
      await state.set_state(AllOrders.RedactOrder.Viewing)

      await callback.message.edit_text('Что вы хотите изменить в продукте?', reply_markup = kb.redact_product_in_order)

    elif command == 'optProduct':
      await state.set_state(AllOrders.RedactOrder.Viewing)

      await callback.message.edit_text('Что вы хотите изменить в доп. продукте?', reply_markup = kb.redact_optProduct_in_order)

    elif command == 'individual':
      await state.set_state(AllOrders.RedactOrder.Individual)

      await callback.message.edit_text(
          'Введите название индивидуально продукта, чтобы заменить им основной продукт.', 
          reply_markup = await kb.custom_inline(data = 'redact_individual_cancel', text = 'Назад')
      )
    elif command == 'date':
      await state.set_state(AllOrders.RedactOrder.Date)

      await callback.message.edit_text(
          'Введите дату в формате: 2024-12-31 24:59:59', 
          reply_markup = await kb.custom_inline(data = 'redact_product_cancel', text = 'Назад')
      )

    elif command == 'cancel':
      data = await state.get_data()

      order_msg = data['order_msg']
      order_id = data['order_id']
      employee_id = data['employee_id']

      await state.set_state(AllOrders.RedactOrder.Viewing)
      await state.update_data(order_id = order_id)
      await state.update_data(employee_id = employee_id)

      await callback.message.delete()

      await bot.edit_message_reply_markup(
         chat_id = callback.message.chat.id,
         message_id = order_msg,
         reply_markup = kb.redact_old_order
      )



@router.callback_query(StateFilter(AllOrders.RedactOrder), F.data.startswith('redact_product'))
async def redact_product(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[2]

    
    if command == 'id':

      await state.set_state(AllOrders.RedactOrder.ProductId)

      await callback.message.edit_text('Выберите товар из списка или введите id нужного товара', reply_markup = await products_inline(False))

    elif command == 'price':

      await state.set_state(AllOrders.RedactOrder.ProductPrice)

      await callback.message.edit_text('Введите точную цену товара', reply_markup = await kb.cancel_inline('redact_product'))
    elif command == 'count':

      await state.set_state(AllOrders.RedactOrder.ProductCount)

      await callback.message.edit_text('Введите количество товара', reply_markup = await kb.cancel_inline('redact_product'))
    else:
      await state.set_state(AllOrders.RedactOrder.Viewing)

      await callback.message.edit_text(
         'Что нужно изменить в заказе?', 
         reply_markup = await kb.redact_order_inline(is_payment = None, data = 'order_redact', is_date = True))
   
@router.callback_query(StateFilter(AllOrders.RedactOrder), F.data.startswith('redact_optProduct'))
async def redact_opt_product(callback: types.CallbackQuery, state: FSMContext):
    
    command = callback.data.split('_')[2]

    

    if command == 'id':

      await state.set_state(AllOrders.RedactOrder.OptionallyProductId)

      data = await state.get_data()

      order = await order_requests.getOrderById(data['order_id'])

      await callback.message.edit_text(
         'Выберите доп. товар из списка или введите id нужного товара', 
         reply_markup = await optionally_products_inline(order.product_id)
      )

    elif command == 'price':

      await state.set_state(AllOrders.RedactOrder.OptionallyProductPrice)

      await callback.message.edit_text('Введите точную цену товара', reply_markup = await kb.cancel_inline('redact_optProduct'))
    elif command == 'count':

      await state.set_state(AllOrders.RedactOrder.OptionallyProductCount)

      await callback.message.edit_text('Введите количество товара', reply_markup = await kb.cancel_inline('redact_optProduct'))
    elif command == 'delete':
       
       data = await state.get_data()
       order = await order_requests.getOrderById(data['order'].id)

       await order_requests.updateOrderOptProductId(order.id, 0)
       await order_requests.updateOrderOptProductPrice(order.id, 0)
       await order_requests.updateOrderOptProductCount(order.id, 0)

       order = await order_requests.getOrderById(order.id)


       message_id = data['order_msg']

       text = await aboutOrderText(order)

       await bot.edit_message_text(
          chat_id = callback.message.chat.id,
          message_id = message_id,
          text = text
       )

       await state.update_data(order = order)

       await callback.message.edit_text('Что нужно изменить в заказе?', reply_markup = await kb.redact_order_inline(is_payment = None, data = 'order_redact', is_date = True))

    else:
      await state.set_state(AllOrders.RedactOrder.Viewing)

      await callback.message.edit_text('Что нужно изменить в заказе?', reply_markup = await kb.redact_order_inline(is_payment = None, data = 'order_redact', is_date = True))
   

@router.message(AllOrders.RedactOrder.Individual)
async def redact_individual_product(message: types.Message, state: FSMContext):
    data = await state.get_data()
    main_msg = data['main_msg']

    message_text = message.text
       
    
    order = data['order']
    if not order:
       return
    
    product = await product_requests.createProduct(
       name = message_text,
       description = '',
       price = '0₽',
       image = None,
       video = None,
       optionally = [],
       is_individual=True
    )

    
    await order_requests.updateOrderProductId(order.id, product.id)
    await order_requests.updateOrderProductPrice(order.id, 0)
    await order_requests.updateOrderProductCount(order.id, 1)


    
    message_id = data['order_msg']
    

    order.product_id = product.id
    order.product_price = 0
    order.product_count = 1

    text = await aboutOrderText(order)

    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = message_id,
       text = text
    )

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в заказе?', 
       reply_markup = await kb.redact_order_inline(is_payment = None, data = 'order_redact', is_date = True)
       )


@router.message(AllOrders.RedactOrder.Date)
async def redact_order_endedAt(message: types.Message, state: FSMContext):

    data = await state.get_data()
    main_msg = data['main_msg']
    
    date = None
    try:
      date = datetime.datetime.strptime(message.text, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа, Введите по образцу: 2024-12-31 24:59:59',
            reply_markup = await kb.cancel_inline('redact_product')
        )
        return
       
    
    order = data['order']
    if not order:
       return
    
    await order_requests.updateOrderEndedAt(order.id, date)

    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)
    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)


    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в заказе?', 
       reply_markup = await kb.redact_order_inline(is_payment = None, data = 'order_redact', is_date = True)
       )
   



@router.message(AllOrders.RedactOrder.ProductId)
async def redact_order_ProductId(message: types.Message, state: FSMContext):
    data = await state.get_data()
    main_msg = data['main_msg']


    try:
       int(message.text)
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа, можно вводить только целочисленные числа',
            reply_markup = await products_inline(False)
        )
        return
       
    
    order = data['order']
    if not order:
       return
    
    product = await product_requests.getProductById(int(message.text))
    

    
    if not product:
       await message.delete()
       await bot.edit_message_text(
        chat_id = message.chat.id,
        message_id = main_msg,
        text = 'Товара с таким id не существует',
        reply_markup = await products_inline(False)
       )
       return
    

    await order_requests.updateOrderProductId(order.id, product.id)
    await order_requests.updateOrderProductPrice(order.id, 0)
    await order_requests.updateOrderProductCount(order.id, 1)

    message_id = data['order_msg']
    
    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в товаре?', 
       reply_markup = kb.redact_product_in_order
       )

@router.callback_query(AllOrders.RedactOrder.ProductId, F.data.startswith('product'))
async def redact_order_ProductId(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]
       


    if command == 'cancel':
       await callback.message.edit_text('Что вы хотите изменить в продукте?', reply_markup = kb.redact_product_in_order)
       return
    

    data = await state.get_data()
    order = data['order']
    

    
    product = await product_requests.getProductById(int(command))
    if not product:
       return
   
    await order_requests.updateOrderProductId(order.id, product.id)
    await order_requests.updateOrderProductPrice(order.id, 0)
    await order_requests.updateOrderProductCount(order.id, 1)

    order = await order_requests.getOrderById(order.id)

    message_id = data['order_msg']
    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = callback.message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await callback.message.edit_text('Товар выбран!\n\n' + 
                                     'Что нужно изменить в продукте?', reply_markup = kb.redact_product_in_order)
    
@router.message(AllOrders.RedactOrder.ProductPrice)
async def redact_order_ProductPrice(message: types.Message, state: FSMContext):

    data = await state.get_data()
    main_msg = data['main_msg']
    
    try:
       float(message.text)
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа, можно вводить только целочисленные и с плавающей точкой числа',
            reply_markup = await kb.cancel_inline('redact_product')
        )
        return
       
    
    order = data['order']
    if not order:
       return
    
    await order_requests.updateOrderProductPrice(order.id, float(message.text))


    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)


    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в продукте?', 
       reply_markup = kb.redact_product_in_order
       )
    
@router.message(AllOrders.RedactOrder.ProductCount)
async def redact_order_ProductCount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    main_msg = data['main_msg']
    
    try:
       int(message.text)
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа, можно вводить только целочисленные числа',
            reply_markup = await kb.cancel_inline('redact_product')
        )
        return
    
    order = data['order']
    if not order:
       return
    
    await order_requests.updateOrderProductCount(order.id, int(message.text))


    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в продукте?', 
       reply_markup = kb.redact_product_in_order
       )
      




@router.message(AllOrders.RedactOrder.OptionallyProductId)
async def redact_order_OptProductId(message: types.Message, state: FSMContext):

    data = await state.get_data()
    main_msg = data['main_msg']
    order = data['order']

    try:
       int(message.text)
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа, можно вводить только целочисленные числа',
            reply_markup = await optionally_products_inline(order.active_product_id, 'cancel')
        )
        return
    
    order = data['order']
    if not order:
       return
    

    product = await optionally_product_requests.getOptionallyProductById(int(message.text))

    if not product:
       await message.delete()
       await bot.edit_message_text(
        chat_id = message.chat.id,
        message_id = main_msg,
        text = 'Товара с таким id не существует',
        reply_markup = await optionally_products_inline(order.active_product_id, 'cancel')
       )
       return
    
    await order_requests.updateOrderOptProductId(order.id, product.id)
    await order_requests.updateOrderOptProductPrice(order.id, 0)
    await order_requests.updateOrderOptProductCount(order.id, 1)
    
    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. продукте?', 
       reply_markup = kb.redact_optProduct_in_order
       )
     
@router.callback_query(AllOrders.RedactOrder.OptionallyProductId, F.data.startswith('optionally'))
async def redact_order_OptProductId(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]

    if command == 'back':
       await callback.message.edit_text('Что вы хотите изменить в доп. продукте?', reply_markup = kb.redact_optProduct_in_order)
       return
    
    command = int(command)


    data = await state.get_data()
    
    order = data['order']
    if not order:
       return
    
    product = await optionally_product_requests.getOptionallyProductById(int(command))
    await order_requests.updateOrderOptProductId(order.id, product.id)
    await order_requests.updateOrderOptProductPrice(order.id, 0)
    await order_requests.updateOrderOptProductCount(order.id, 1)

    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = callback.message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await callback.message.edit_text('Доп. товар выбран!\n\n' + 
                                     'Что нужно изменить в доп. продукте?', reply_markup = kb.redact_optProduct_in_order)
    
@router.message(AllOrders.RedactOrder.OptionallyProductPrice)
async def redact_order_OptProductPrice(message: types.Message, state: FSMContext):

    data = await state.get_data()
    main_msg = data['main_msg']
    
    try:
       float(message.text)
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа, можно вводить только целочисленные и с плавающей точкой числа',
            reply_markup = await kb.cancel_inline('redact_optProduct')
        )
        return
    
    
    order = data['order']
    if not order:
       return
    
    await order_requests.updateOrderOptProductPrice(order.id, float(message.text))

    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = message_id,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. продукте?', 
       reply_markup = kb.redact_optProduct_in_order
       )
       
@router.message(AllOrders.RedactOrder.OptionallyProductCount)
async def redact_order_OptProductCount(message: types.Message, state: FSMContext):

    data = await state.get_data()
    main_msg = data['main_msg']
    
    try:
       int(message.text)
    except ValueError:
        await message.delete()
        await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа, можно вводить только целочисленные числа',
            reply_markup = await kb.cancel_inline('redact_optProduct')
        )
        return
    
    
    order = data['order']
    if not order:
       return
    
    await order_requests.updateOrderOptProductCount(order.id, int(message.text))

    order_msg = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    text = await aboutOrderText(order)

    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = order_msg,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(order = order)

    await state.set_state(AllOrders.RedactOrder.Viewing)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. продукте?', 
       reply_markup = kb.redact_optProduct_in_order
       )
      



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
        f'Дата окончания заказа: {ended_at}')

