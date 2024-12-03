from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import app.kb.client_keyboards as kb
from app.ClientStates import CreateOrder

from db.Enums import DeliveryMethod

from app.ClientStates import RedactOrder


router = Router(name=__name__)




@router.callback_query(StateFilter(RedactOrder), F.data == 'redact_order_cancel')
async def cancel_redactOrder(callback: types.CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    short_des = data['short_des']
        

    await state.set_state(CreateOrder.RedactOrder)
    text = await about_order(short_des, data)
    await callback.message.edit_text(
        text,
        reply_markup = kb.redact_order
    )




@router.callback_query(F.data.startswith('redact_order'), CreateOrder.RedactOrder)
async def redact_order(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[2]

    keyboard = await kb.cancel_inline(data = 'redact_order', text = 'Назад')

    if command == 'fio':
      await state.set_state(RedactOrder.Fio)
      await callback.message.edit_text('Введите ваше ФИО', reply_markup=keyboard)
    elif command == 'address':
      await state.set_state(RedactOrder.Address)
      await callback.message.edit_text('Введите ваш адрес, запись может выглядить так:\n'+
                         'Россия, Оренбургская обл., г. Оренбург, ул. Чкалова, д. 11', reply_markup=keyboard)
    elif command == 'phone':
      await state.set_state(RedactOrder.PhoneNumber)
      await callback.message.edit_text('Введите ваш номер телефона, запись должна быть в одном из форматов:\n'+
                         '79998887766 \ 89998887766', reply_markup = keyboard)
    elif command == 'delivery':
      await state.set_state(RedactOrder.AboutDelivery)
      await callback.message.edit_text('Выберите способ доставки:', reply_markup = await kb.delivery_methods())
    else:
      await state.set_state(CreateOrder.VerifyPhoto)
      await callback.message.delete()
      await callback.message.answer(
         'Отправьте фотографию документа удостоверяющего личность, чтобы можно было разглядеть фотографию, номер и другие данные\n\n' +
         '<strong>Внимание!</strong> Фото и видео выших документов нужны для проверки сотрудником вашей личности, эти данных не будут сохраняться или передаваться 3-им лицам', 
         reply_markup = None
      )
      



@router.message(RedactOrder.Fio)
async def redact_fio(message: types.Message, state: FSMContext):

    fio = message.text


    await state.update_data(fio = fio)

    data = await state.get_data()
    short_des = data['short_des']

    await state.set_state(CreateOrder.RedactOrder)
    await message.answer(
       'Хотите изменить какие-то данные?\n\n' +
        short_des +
        f'ФИО: {data["fio"]}\n' +
        f'Адресс: {data["address"]}\n' +
        f'Номер телефона: {data["phoneNumber"]}\n' +
        f'Способ доставки: {data["delivery"]}\n',
        reply_markup = kb.redact_order
    )
    
    
@router.message(RedactOrder.PhoneNumber)
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
    await state.set_state(CreateOrder.RedactOrder)
    await message.answer(
       'Хотите изменить какие-то данные?\n\n' +
        short_des +
        f'ФИО: {data["fio"]}\n' +
        f'Адресс: {data["address"]}\n' +
        f'Номер телефона: {data["phoneNumber"]}\n' +
        f'Способ доставки: {data["delivery"]}\n',
        reply_markup = kb.redact_order
    )
    

@router.message(RedactOrder.Address)
async def redact_address(message: types.Message, state: FSMContext):

    address = message.text

    await state.update_data(address = address)

    data = await state.get_data()
    short_des = data['short_des']
    await state.set_state(CreateOrder.RedactOrder)
    await message.answer(
       'Хотите изменить какие-то данные?\n\n' +
        short_des +
        f'ФИО: {data["fio"]}\n' +
        f'Адресс: {data["address"]}\n' +
        f'Номер телефона: {data["phoneNumber"]}\n' +
        f'Способ доставки: {data["delivery"]}\n',
        reply_markup = kb.redact_order
    )


@router.callback_query(RedactOrder.AboutDelivery, F.data.startswith('delivery'))
async def redact_delivery_method(callback: types.CallbackQuery, state: FSMContext):
  delivery = callback.data.split('_')[1]

  delivery_methods = [e for e in DeliveryMethod]

  for method in delivery_methods:
    if delivery == method.name:
        await state.update_data(delivery = method)
        break

  data = await state.get_data()
  short_des = data['short_des']
  await state.set_state(CreateOrder.RedactOrder)

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

