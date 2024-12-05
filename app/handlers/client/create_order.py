from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import app.kb.client_keyboards as kb
from app.kb.employee_keyboards import verify_inline, end_call
from app.ClientStates import CreateOrder, EmployeeCall, SelectProduct

from db import order_requests, product_requests, optionally_product_requests, employee_requests, user_requests
from db.models import Order
from db.Enums import DeliveryMethod, AppName
from datetime import datetime

from app.handlers.common import aboutOrderText

from typing import Optional
from .common import searchBusyEmployeeForUserId, sendMessageEmployee, sendMediaEmployee


router = Router(name=__name__)




@router.message(StateFilter(CreateOrder), F.text == 'Отмена')
async def cancel_createOrder(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    product = await product_requests.getProductById(data['product_id'])
    short_des = data['short_des']

    await state.clear()

    message = await message.answer('ОПЕРАЦИЯ ОТМЕНЕНА',
                              reply_markup = kb.main_reply)
    

    if not product:
      await message.answer('Товар уже раскупили :(',
                              reply_markup = await kb.cancel_inline(data = 'cancel', text = 'Выйти'))
      return
      
    await state.set_state(SelectProduct.BeforeOrdering)
    await state.update_data(product_id = product.id)
    await state.update_data(short_des = short_des)

    await message.answer(
          short_des +
          'Вместе с этим товаром доступны дополнительные аксессуары',
          reply_markup = kb.before_ordering_change
      )
    



@router.message(CreateOrder.ProductCount)
async def product_count(message: types.Message, state: FSMContext):

    count = message.text

    try:
       int(count)
    except ValueError:
       await message.answer('Неверный формат сообщения, вводить можно только числа')
       return

    
    await state.update_data(product_count = int(count))
    data = await state.get_data()

    short_des = data['short_des']
    try:
        if not data['optionally_product_id']:
           raise KeyError()
    except KeyError:
        await state.set_state(CreateOrder.Fio)
        await message.answer(
            short_des + 
            'Введите ваше ФИО'
        )
        return

    await message.answer(
            short_des + 
            'Сколько единиц доп. товара вы хотите заказать'
    )
    await state.set_state(CreateOrder.OptionallProductCount)


@router.message(CreateOrder.OptionallProductCount)
async def optionally_product_count(message: types.Message, state: FSMContext):

    count = message.text

    try:
       int(count)
    except ValueError:
       await message.answer('Неверный формат сообщения, вводить можно только числа')
       return
    
    await state.update_data(optionally_product_count = int(count))

    data = await state.get_data()

    short_des = data['short_des']
    
    await state.set_state(CreateOrder.Fio)
    await message.answer(
            short_des + 
            'Введите ваше ФИО')


@router.message(CreateOrder.Fio)
async def fio(message: types.Message, state: FSMContext):

    fio = message.text

    if not fio:
      await message.answer('Напишите ваше ФИО')


    
    data = await state.get_data()
    short_des = data['short_des']


    await state.update_data(fio = fio)
    
    await state.set_state(CreateOrder.PhoneNumber)
    await message.answer(
            short_des + 
           'Введите ваш номер телефона, запись должна быть в одном из форматов:\n'+
                         '79998887766 \ 89998887766'
    )
    

@router.message(CreateOrder.PhoneNumber)
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
    
    await state.set_state(CreateOrder.Address)
    await message.answer(
            short_des + 
           'Введите ваш адрес, запись может выглядить так:\n'+
                         'Россия, Оренбургская обл., г. Оренбург, ул. Чкалова, д. 11')
    

@router.message(CreateOrder.Address)
async def address(message: types.Message, state: FSMContext):

    address = message.text


    data = await state.get_data()
    short_des = data['short_des']

    await state.update_data(address = address)
    
    await state.set_state(CreateOrder.AboutDelivery)
    await message.answer(
            short_des + 
           'Выберите способ доставки:', reply_markup = await kb.delivery_methods())


@router.callback_query(CreateOrder.AboutDelivery, F.data.startswith('delivery'))
async def delivery_method(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]

    delivery_methods = [e for e in DeliveryMethod]

    for method in delivery_methods:
      if command == method.name:
        await state.update_data(delivery = method)
        break
    
    data = await state.get_data()
    short_des = data['short_des']

    await state.set_state(CreateOrder.RedactOrder)
    await callback.message.edit_text('Хотите изменить какие-то данные?\n\n' +
                                     short_des +
                                     f'ФИО: {data["fio"]}\n' +
                                     f'Адресс: {data["address"]}\n' +
                                     f'Номер телефона: {data["phoneNumber"]}\n' +
                                     f'Способ доставки: {data["delivery"].value}\n',
                                      reply_markup = kb.redact_order)
    



@router.message(CreateOrder.VerifyPhoto)
async def verify_photo(message: types.Message, state: FSMContext):

    if not message.photo:
      await message.answer('Неверный формат, отправьте 1 фотографию')


    photo = message.photo[-1]

    await state.update_data(photo_id = photo.file_id)
      
    await state.set_state(CreateOrder.VerifyVideo)
    await message.answer('Пожалуйста, не удаляйте фотографию до завершения покупки!\n\nТеперь отправьте видеозапись с вашим лицом рядом с раскрытым документом')       


@router.message(CreateOrder.VerifyVideo)
async def verify_video(message: types.Message, state: FSMContext):

      if message.photo:
        await message.delete()
        await message.answer('Неверный формат, отправьте 1 видео')
        return


      video = message.video

      await state.update_data(video_id = video.file_id)
      
      await state.set_state(EmployeeCall.Call)

      data = await state.get_data()

      from_user = message.from_user
      order = await purchasing(
            from_user,
            data
          )


      last_message = await message.answer('Ищем свободного сотрудника для дальнейшей работы..', reply_markup = kb.cancel)


      employee = await searchBusyEmployeeForUserId(from_user.id, from_user.username)

      if not employee:
         return


      user = await user_requests.getUserById(employee.user_id)
      if not user:
          await state.clear()
          await message.answer('Произошла ошибка и мы не смогли найти свободного сотрудника для дальнейшей работы.\n\n' +
                          'Попробуйте позже :)')
          return

      await order_requests.updateOrderEmployee(order.id, employee.id)
      await employee_requests.updateActiveOrderEmployee(employee.id, order.id)

      
      photo = data['photo_id']
      reply_message = await sendMediaEmployee(
        chat_id = user.user_id,
        photo = photo,
        video = video.file_id,
        text = 
          f'Клиент @{from_user.username} оформил заказ, проведите верификацию и оплату\n\n' +
          await aboutOrderText(order),
        reply_markup = end_call
      )



      await sendMessageEmployee(
        text = 'Подтверждение верификации:',
        chat_id = user.user_id,
        reply_markup = verify_inline,
        message_id = reply_message.message_id
      )

      await last_message.edit_text('Вся информация передана сотруднику, после прохождения верификации вам придет сообщение и затем с вами свяжется сотрудник', reply_markup=None)




async def purchasing(
      from_user,
      data
) -> Optional['Order']:
        
        product_id = data['product_id']
        product = await product_requests.getProductById(product_id)
        if not product:
           return None

        fio = data['fio']
        phoneNumber = data['phoneNumber']
        address = data['address']
        delivery = data['delivery']
        product_count = data['product_count']

        optionally_product_id = None
        optionally_product_count = 0

        try:
            optionally_product_id = data['optionally_product_id']
            optionally_product = await optionally_product_requests.getOptionallyProductById(optionally_product_id)
            if optionally_product:
              optionally_product_count = data['optionally_product_count']
        except KeyError:
            optionally_product_id = None


        user = await user_requests.createUser(from_user.id, from_user.username)


        order = await order_requests.createOrder(
           user.id,
           fio,
           phoneNumber,
           address,
           delivery,

           0,
           0,

           product.id,
           optionally_product_id,

           product_count,
           optionally_product_count,

           AppName.TG,
           datetime.now()
        )

        return order

