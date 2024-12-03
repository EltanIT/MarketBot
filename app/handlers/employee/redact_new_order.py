from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest
from app.config import bot

import app.kb.employee_keyboards as kb
from app.EmployeeStates import RedactOrder

from db import order_requests, employee_requests, user_requests, product_requests, optionally_product_requests
from db.Enums import OrderStatus
from .common import checkOrderProducts, clearEmployeeDB

from datetime import datetime

from app.kb.client_keyboards import main_reply
from app.kb.common import products_inline, optionally_products_inline



router = Router(name=__name__)   



@router.callback_query(RedactOrder.Individual, F.data == 'redact_individual_cancel')
async def cancel_redact_individual(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RedactOrder.Call)


    await callback.message.edit_reply_markup(
       reply_markup = await kb.redact_order_inline()
    )
   



@router.callback_query(F.data.startswith('verify'))
async def verify(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    employee = await employee_requests.getEmployeeByUserId(callback.from_user.id)
    command = callback.data.split('_')[1]
    if employee:
      await state.update_data(order_id = employee.active_order_id)
      client = await user_requests.getUserById(employee.active_client_id)
      if command == 'yes':
          
          order = await order_requests.getOrderById(employee.active_order_id)

          if not order:
             return
          
          await order_requests.updateOrderVerify(employee.active_order_id, True)
          await order_requests.updateOrderStatus(employee.active_order_id, OrderStatus.DURING_PAYMENT)


          main_message = await callback.message.edit_text(
             'Вы можете изменить заказ и провести оплату!', 
             reply_markup = await kb.redact_order_inline(),
             reply_to_message_id = callback.message.reply_to_message.message_id
          )
       

          await state.set_state(RedactOrder.Call)
   
          await state.update_data(main_msg = main_message.message_id)
          await state.update_data(order_msg = callback.message.reply_to_message.message_id)
          await state.update_data(order = order)


          await bot.send_message(client.user_id, 'Верификация пройдена ✅\n\nСкоро с вами свяжется сотрудник для осуществления оплаты')
      else:
        await order_requests.deleteOrder(employee.active_order_id)

        await clearEmployeeDB(callback.from_user.id)

        await callback.message.reply_to_message.delete()
        await bot.delete_message(
            callback.message.chat.id,
            callback.message.reply_to_message.message_id-1
        )
        await callback.message.delete()
        
        await callback.message.answer('Разговор закончен, теперь вы не можете изменять данные заказа, кроме его статуса', reply_markup = None)

        await bot.send_message(client.user_id, 'Верификация не пройдена ❌,\nзаказ не одобрен')
    







@router.callback_query(StateFilter(RedactOrder), F.data.startswith('redact_order'))
async def redact_order(callback: types.CallbackQuery, state: FSMContext):
    
    employee = await employee_requests.getEmployeeByUserId(callback.from_user.id)
    command = callback.data.split('_')[2]


    if not employee:
      await state.clear()
      return
    
    
    if command == 'product':

      await callback.message.edit_text('Что вы хотите изменить в продукте?', reply_markup = kb.redact_product_in_order)

    elif command == 'optProduct':

      await callback.message.edit_text('Что вы хотите изменить в доп. продукте?', reply_markup = kb.redact_optProduct_in_order)
    elif command == 'date':
      await state.set_state(RedactOrder.Date)

      await callback.message.edit_text(
          'Введите дату в формате: 2024-12-31 24:59:59', 
          reply_markup = await kb.custom_inline(data = 'redact_product_cancel', text = 'Назад')
      )
    
    elif command == 'payment':

      await state.set_state(RedactOrder.Payment)
      await callback.message.edit_text('Проведите оплату у клиента и подтвердите ее здесь.', reply_markup = kb.order_payment)
    elif command == 'individual':
      await state.set_state(RedactOrder.Individual)

      await callback.message.edit_text(
          'Введите название индивидуально продукта, чтобы заменить им основной продукт.', 
          reply_markup = await kb.custom_inline(data = 'redact_individual_cancel', text = 'Назад')
      )

    else:
      await state.clear()


      await callback.message.edit_text('Что нужно изменить в заказе?', reply_markup = await kb.redact_order_inline())


@router.callback_query(RedactOrder.Payment, F.data.startswith('payment_order'))
async def order_payment(callback: types.CallbackQuery, state: FSMContext):
    

    employee = await employee_requests.getEmployeeByUserId(callback.from_user.id)
    command = callback.data.split('_')[2]

    if not employee:
      return
    

    client = await user_requests.getUserById(employee.active_client_id)
    
    if command == 'yes':

      if not checkOrderProducts(employee.active_order_id):
         await callback.message.edit_text('Заказ содержит данные, которых нет в базе данных, проверьте товары', reply_markup = await kb.redact_order_inline())
         await state.set_state(RedactOrder.Call)
         return

      await state.clear()

      await order_requests.updateOrderStatus(employee.active_order_id, OrderStatus.DURING_PROCESSING)


      await clearEmployeeDB(callback.from_user.id)

      await callback.message.delete()
      await callback.message.reply_to_message.delete()
      await bot.delete_message(
         callback.message.chat.id,
         callback.message.reply_to_message.message_id-1
      )
      
      await callback.message.answer('Оплата подтверждена, разговор закончен, теперь вы не можете изменять данные заказа, кроме его статуса', 
                                       reply_markup = await kb.main_reply(callback.from_user.id))
      

      await bot.send_message(client.user_id, 
                             f'Заказ {employee.active_order_id} оплачен!\n\n'+
                             'Сейчас он находится в обработке\n'+
                             f'Время доставки: ~ 8 дней', 
                             reply_markup = main_reply)

    elif command == 'back':
      await state.set_state(RedactOrder.Call)

      await callback.message.edit_text('Что нужно изменить в заказе?', reply_markup = await kb.redact_order_inline())
  

@router.message(RedactOrder.Date)
async def redact_order_endedAt(message: types.Message, state: FSMContext):

    data = await state.get_data()
    main_msg = data['main_msg']
    
    date = None
    try:
      date = datetime.strptime(message.text, "%Y.%m.%d %H:%M:%S")
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

    await state.set_state(RedactOrder.Call)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в заказе?', 
       reply_markup = await kb.redact_order_inline()
       )
   



@router.message(RedactOrder.Individual)
async def redact_individual_product(message: types.Message, state: FSMContext):
    data = await state.get_data()
    main_msg = data['main_msg']

    message_text = message.text
       
    
    employee = await employee_requests.getEmployeeByUserId(message.from_user.id)
    if not employee:
       return
    
    product = await product_requests.createProduct(
       name = message_text,
       description = '',
       price = 0,
       image = None,
       video = None,
       optionally = [],
       is_individual=True
    )

    
    await order_requests.updateOrderProductId(employee.active_order_id, product.id)
    await order_requests.updateOrderProductPrice(employee.active_order_id, 0)
    await order_requests.updateOrderProductCount(employee.active_order_id, 1)


    
    order = data['order']
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

    await state.set_state(RedactOrder.Call)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в заказе?', 
       reply_markup = await kb.redact_order_inline()
       )





@router.callback_query(StateFilter(RedactOrder), F.data.startswith('redact_product'))
async def redact_product(callback: types.CallbackQuery, state: FSMContext):

    employee = await employee_requests.getEmployeeByUserId(callback.from_user.id)
    command = callback.data.split('_')[2]


    if not employee:
      return
    
    if command == 'id':

      await state.set_state(RedactOrder.ProductId)

      await callback.message.edit_text('Выберите товар из списка или введите id нужного товара', reply_markup = await products_inline(False))

    elif command == 'price':

      await state.set_state(RedactOrder.ProductPrice)

      await callback.message.edit_text('Введите точную цену товара', reply_markup = await kb.cancel_inline('redact_product'))
    elif command == 'count':

      await state.set_state(RedactOrder.ProductCount)

      await callback.message.edit_text('Введите количество товара', reply_markup = await kb.cancel_inline('redact_product'))
    else:
      await callback.message.edit_text('Что нужно изменить в заказе?', reply_markup = await kb.redact_order_inline())
   
@router.callback_query(StateFilter(RedactOrder), F.data.startswith('redact_optProduct'))
async def redact_opt_product(callback: types.CallbackQuery, state: FSMContext):
    

    employee = await employee_requests.getEmployeeByUserId(callback.from_user.id)
    command = callback.data.split('_')[2]

    if not employee:
      return
    
    order = await order_requests.getOrderById(employee.active_order_id)

    if not order:
       return
    
    if command == 'id':

      await state.set_state(RedactOrder.OptionallyProductId)

      await callback.message.edit_text(
         'Выберите доп. товар из списка или введите id нужного товара',
         reply_markup = await optionally_products_inline(order.product_id)
      )

    elif command == 'price':

      await state.set_state(RedactOrder.OptionallyProductPrice)

      await callback.message.edit_text('Введите точную цену товара', reply_markup = await kb.cancel_inline('redact_optProduct'))
    elif command == 'count':

      await state.set_state(RedactOrder.OptionallyProductCount)

      await callback.message.edit_text('Введите количество товара', reply_markup = await kb.cancel_inline('redact_optProduct'))
    elif command == 'delete':
       
       data = await state.get_data()
       
       message_id = data['order_msg']

       caption = await aboutOrderText(order)
       try:
         await bot.edit_message_caption(
            chat_id = callback.message.chat.id,
            message_id = message_id,
            caption = caption
         )
       except TelegramBadRequest:
          ...
       
       await order_requests.updateOrderOptProductId(order.id, 0)
       await order_requests.updateOrderOptProductPrice(order.id, 0)
       await order_requests.updateOrderOptProductCount(order.id, 0)

       await callback.message.edit_text('Что нужно изменить в заказе?', reply_markup = await kb.redact_order_inline())
    else:

      await callback.message.edit_text('Что нужно изменить в заказе?', reply_markup = await kb.redact_order_inline())
   



@router.message(RedactOrder.ProductId)
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
    

    order = data['order']
    
    await order_requests.updateOrderProductId(order.id, int(message.text))
    await order_requests.updateOrderProductPrice(order.id, product.price)
    await order_requests.updateOrderProductCount(order.id, 1)

    message_id = data['order_msg']
    
    order = await order_requests.getOrderById(order.id)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = message.chat.id,
            message_id = message_id,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в товаре?', 
       reply_markup = kb.redact_product_in_order
       )

@router.callback_query(RedactOrder.ProductId, F.data.startswith('product'))
async def redact_order_ProductId(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]
       


    if command == 'cancel':
       await callback.message.edit_text('Что вы хотите изменить в продукте?', reply_markup = kb.redact_product_in_order)
       return

    data = await state.get_data()
    order = data['order']
    
    product = await product_requests.getProductById(int(command))
    await order_requests.updateOrderProductId(order.id, product.id)
    await order_requests.updateOrderProductPrice(order.id, product.price)
    await order_requests.updateOrderProductCount(order.id, 1)

    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = callback.message.chat.id,
            message_id = message_id,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

    await callback.message.edit_text('Товар выбран!\n\n' + 
                                     'Что нужно изменить в продукте?', reply_markup = kb.redact_product_in_order)
    
@router.message(RedactOrder.ProductPrice)
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
    
    await order_requests.updateOrderProductPrice(order.id, float(message.text))


    
    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = message.chat.id,
            message_id = message_id,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в продукте?', 
       reply_markup = kb.redact_product_in_order
       )
   
@router.message(RedactOrder.ProductCount)
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
    
    await order_requests.updateOrderProductCount(order.id, int(message.text))

    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = message.chat.id,
            message_id = message_id,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в продукте?', 
       reply_markup = kb.redact_product_in_order
       )
      




@router.message(RedactOrder.OptionallyProductId)
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
            reply_markup = await optionally_products_inline(order.active_product_id)
        )
        return
    

    product = await optionally_product_requests.getOptionallyProductById(int(message.text))

    if not product:
       await message.delete()
       await bot.edit_message_text(
        chat_id = message.chat.id,
        message_id = main_msg,
        text = 'Товара с таким id не существует',
        reply_markup = await optionally_products_inline(order.active_product_id)
       )
       return
    
    
    await order_requests.updateOrderOptProductId(order.id, product.id)
    await order_requests.updateOrderOptProductPrice(order.id, product.price)
    await order_requests.updateOrderOptProductCount(order.id, 1)



    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = message.chat.id,
            message_id = message_id,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. продукте?', 
       reply_markup = kb.redact_optProduct_in_order
       )
     
@router.callback_query(RedactOrder.OptionallyProductId, F.data.startswith('optionally'))
async def redact_order_OptProductId(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]


    if command == 'back':
       await callback.message.edit_text('Что вы хотите изменить в доп. продукте?', reply_markup = kb.redact_optProduct_in_order)
       return

    data = await state.get_data()
    order = data['order']
    
    product = await optionally_product_requests.getOptionallyProductById(int(command))
    await order_requests.updateOrderOptProductId(order.id, product.id)
    await order_requests.updateOrderOptProductPrice(order.id, product.price)
    await order_requests.updateOrderOptProductCount(order.id, 1)


    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = callback.message.chat.id,
            message_id = message_id,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

    await callback.message.edit_text('Доп. товар выбран!\n\n' + 
                                     'Что нужно изменить в доп. продукте?', reply_markup = kb.redact_optProduct_in_order)
    
@router.message(RedactOrder.OptionallyProductPrice)
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
    
    await order_requests.updateOrderOptProductPrice(order.id, float(message.text))

    message_id = data['order_msg']

    order = await order_requests.getOrderById(order.id)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = message.chat.id,
            message_id = message_id,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. продукте?', 
       reply_markup = kb.redact_optProduct_in_order
       )
       
@router.message(RedactOrder.OptionallyProductCount)
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
    
    await order_requests.updateOrderOptProductCount(order.id, int(message.text))

    order_msg = data['order_msg']

    order.optionally_product_count = int(message.text)

    caption = await aboutOrderText(order)

    try:
         await bot.edit_message_caption(
            chat_id = message.chat.id,
            message_id = order_msg,
            caption = caption
         )
    except TelegramBadRequest:
      ...

    await state.update_data(order = order)

    await state.set_state(RedactOrder.Call)

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
        f'Дата окончания заказа: {ended_at}'
    )



