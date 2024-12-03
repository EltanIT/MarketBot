from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.config import bot

import app.kb.client_keyboards as kb
from app.ClientStates import CreateOrderFromEmployee, EmployeeCall

from db import order_requests, employee_requests, user_requests
from db.models import Order
from db.Enums import DeliveryMethod

from typing import Optional


router = Router(name=__name__)



@router.callback_query(F.data.startswith('create_order'))
async def create_order_from_employee(callback: types.CallbackQuery, state: FSMContext):
    
    command = callback.data.split('_')[2]

    if command == 'yes':
        await state.set_state(CreateOrderFromEmployee.Fio)

        user = await user_requests.getUserByUserId(callback.from_user.id)
        if not user:
            return
        
        order = await order_requests.getOrderById(user.active_order_id)
        if not order:
            await callback.message.edit_text('Заказ не был создан, обратитесь к сотруднику')
            return
        


        short_des = (
            f'ID заказа: {order.id}\n' +
            f'Товар: {order.product_id} ({order.product_count}) {order.product_price}₽\n\n' +
            f'Доп товар: {order.optionally_product_id} ({order.optionally_product_count}) {order.optionally_product_price}₽\n\n'
        )

        await callback.message.edit_text(short_des + 'Введите ваше ФИО', reply_markup=kb.cancel)

        await state.update_data(order = order)
        await state.update_data(short_des = short_des)

        
    elif command == 'not':
        await callback.message.delete()

        employee = await employee_requests.getEmployeeWithActiveClientByClientId(callback.from_user.id)

        if not employee:
            return
        
        employee = await user_requests.getUserById(employee.user_id)
        
        await bot.send_message(
            employee.user_id,
            'Клиент отказался заполнять заявку'
        )
    
   



@router.message(StateFilter(CreateOrderFromEmployee), F.text == 'Отмена')
async def cancel_createOrder(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        'ОПЕРАЦИЯ ОТМЕНЕНА',
        reply_markup = kb.main_reply
    )
      
    await state.set_state(EmployeeCall.Call)


    employee = await employee_requests.getEmployeeWithActiveClientByClientId(message.from_user.id)

    if not employee:
        return
    
    employee = await user_requests.getUserById(employee.user_id)
    
    await bot.send_message(
        employee.user_id,
        'Клиент отменил заявку'
    )


@router.message(CreateOrderFromEmployee.Fio)
async def fio(message: types.Message, state: FSMContext):

    fio = message.text

    if not fio:
      await message.answer('Напишите ваше ФИО')


    
    data = await state.get_data()
    short_des = data['short_des']


    await state.update_data(fio = fio)
    
    await state.set_state(CreateOrderFromEmployee.PhoneNumber)
    await message.answer(
            short_des + 
            'Введите ваш номер телефона, запись должна быть в одном из форматов:\n'+
            '79998887766 \ 89998887766'
    )
    

@router.message(CreateOrderFromEmployee.PhoneNumber)
async def phoneNumber(message: types.Message, state: FSMContext):

    phone = message.text

    data = await state.get_data()
    short_des = data['short_des']

    if not phone.startswith('7') and not phone.startswith('8'):
       await message.answer(
            short_des + 
           'Неверный формат номера!! Примеры::\n'+
                         '79998887766 \ 89998887766')
       return
    if len(phone) != 11:
       await message.answer(
            short_des + 
           'Неверный формат номера!! Примеры::\n'+
                         '79998887766 \ 89998887766')
       return


    await state.update_data(phoneNumber = phone)
    
    await state.set_state(CreateOrderFromEmployee.Address)
    await message.answer(
            short_des + 
           'Введите ваш адрес, запись может выглядить так:\n'+
                         'Россия, Оренбургская обл., г. Оренбург, ул. Чкалова, д. 11')
    

@router.message(CreateOrderFromEmployee.Address)
async def address(message: types.Message, state: FSMContext):

    address = message.text


    data = await state.get_data()
    short_des = data['short_des']

    await state.update_data(address = address)
    
    await state.set_state(CreateOrderFromEmployee.AboutDelivery)
    await message.answer(
            short_des + 
           'Выберите способ доставки:', reply_markup = await kb.delivery_methods())


@router.callback_query(CreateOrderFromEmployee.AboutDelivery, F.data.startswith('delivery'))
async def delivery_method(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]

    delivery_methods = [e for e in DeliveryMethod]

    for method in delivery_methods:
      if command == method.name:
        await state.update_data(delivery = method)
        break
    
    data = await state.get_data()
    short_des = data['short_des']

    await state.set_state(CreateOrderFromEmployee.RedactOrderState)
    await callback.message.edit_text('Хотите изменить какие-то данные?\n\n' +
                                     short_des +
                                     f'ФИО: {data["fio"]}\n' +
                                     f'Адресс: {data["address"]}\n' +
                                     f'Номер телефона: {data["phoneNumber"]}\n' +
                                     f'Способ доставки: {data["delivery"].value}\n',
                                      reply_markup = kb.redact_order)
    


@router.callback_query(StateFilter(CreateOrderFromEmployee.RedactOrder), F.data == 'redact_order_cancel')
async def cancel_redactOrder(callback: types.CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    short_des = data['short_des']
        

    await state.set_state(CreateOrderFromEmployee.RedactOrder)
    text = await about_order(short_des, data)
    await callback.message.edit_text(
        text,
        reply_markup = kb.redact_order
    )




@router.callback_query(F.data.startswith('redact_order'), CreateOrderFromEmployee.RedactOrderState)
async def redact_order(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[2]

    keyboard = await kb.cancel_inline(data = 'redact_order', text = 'Назад')

    if command == 'fio':
      await state.set_state(CreateOrderFromEmployee.RedactOrder.Fio)
      await callback.message.edit_text('Введите ваше ФИО', reply_markup=keyboard)
    elif command == 'address':
      await state.set_state(CreateOrderFromEmployee.RedactOrder.Address)
      await callback.message.edit_text('Введите ваш адрес, запись может выглядить так:\n'+
                         'Россия, Оренбургская обл., г. Оренбург, ул. Чкалова, д. 11', reply_markup=keyboard)
    elif command == 'phone':
      await state.set_state(CreateOrderFromEmployee.RedactOrder.PhoneNumber)
      await callback.message.edit_text('Введите ваш номер телефона, запись должна быть в одном из форматов:\n'+
                         '79998887766 \ 89998887766', reply_markup = keyboard)
    elif command == 'delivery':
      await state.set_state(CreateOrderFromEmployee.RedactOrder.AboutDelivery)
      await callback.message.edit_text('Выберите способ доставки:', reply_markup = await kb.delivery_methods())
    else:
      data = await state.get_data()
      order = await purchasing(data)
      await state.clear()

      employee = await employee_requests.getEmployeeById(order.employee_id)
      employee = await user_requests.getUserById(employee.user_id)

      await callback.message.delete()
      await bot.send_message(
         employee.user_id,
         f'Клиент <em>{order.fio}</em> заполнил данные для заказа <strong>{order.id}</strong>', 
         reply_markup = None
      )
      



@router.message(CreateOrderFromEmployee.RedactOrder.Fio)
async def redact_fio(message: types.Message, state: FSMContext):

    fio = message.text


    await state.update_data(fio = fio)

    data = await state.get_data()
    short_des = data['short_des']

    await state.set_state(CreateOrderFromEmployee.RedactOrderState)

    text = await about_order(short_des, data)
    await message.answer(
        text,
        reply_markup = kb.redact_order
    )
    
    
@router.message(CreateOrderFromEmployee.RedactOrder.PhoneNumber)
async def redact_phoneNumber(message: types.Message, state: FSMContext):

    phone = message.text

    if not phone.startswith('7') and not phone.startswith('8'):
       await message.answer('Неверный формат номера!! Примеры::\n'+
                         '79998887766 \ 89998887766', reply_markup=kb.cancel)
       return
    if len(phone) != 11:
       await message.answer('Неверный формат номера!! Примеры::\n'+
                         '79998887766 \ 89998887766', reply_markup=kb.cancel)
       return


    await state.update_data(phoneNumber = phone)

    data = await state.get_data()
    short_des = data['short_des']
    await state.set_state(CreateOrderFromEmployee.RedactOrderState)

    text = await about_order(short_des, data)
    await message.answer(
        text,
        reply_markup = kb.redact_order
    )
    

@router.message(CreateOrderFromEmployee.RedactOrder.Address)
async def redact_address(message: types.Message, state: FSMContext):

    address = message.text

    await state.update_data(address = address)

    data = await state.get_data()
    short_des = data['short_des']
    await state.set_state(CreateOrderFromEmployee.RedactOrderState)

    text = await about_order(short_des, data)
    await message.answer(
        text,
        reply_markup = kb.redact_order
    )


@router.callback_query(CreateOrderFromEmployee.RedactOrder.AboutDelivery, F.data.startswith('delivery'))
async def redact_delivery_method(callback: types.CallbackQuery, state: FSMContext):
  delivery = callback.data.split('_')[1]

  delivery_methods = [e for e in DeliveryMethod]

  for method in delivery_methods:
    if delivery == method.name:
        await state.update_data(delivery = method)
        break

  data = await state.get_data()
  short_des = data['short_des']
  await state.set_state(CreateOrderFromEmployee.RedactOrderState)

  text = await about_order(short_des, data)
  await callback.message.edit_text(
      text,
      reply_markup = kb.redact_order
  )





async def about_order(short_des: str, data) -> str:
    return(
       'Хотите изменить какие-то данные?\n\n' +
        short_des +
        f'ФИО: {data["fio"]}\n' +
        f'Адресс: {data["address"]}\n' +
        f'Номер телефона: {data["phoneNumber"]}\n' +
        f'Способ доставки: {data["delivery"].value}\n'
    )





async def purchasing(
      data
) -> Optional['Order']:

        fio = data['fio']
        phoneNumber = data['phoneNumber']
        address = data['address']
        delivery = data['delivery']

        order = data['order']

        

        if not order:
            return None

        await order_requests.updateOrderFio(order.id, fio)
        await order_requests.updateOrderAddress(order.id, address)
        await order_requests.updateOrderPhoneNumber(order.id, phoneNumber)
        await order_requests.updateOrderDeliveryMethod(order.id, delivery)


        order = await order_requests.getOrderById(order.id)

        print(order.fio)


        return order

