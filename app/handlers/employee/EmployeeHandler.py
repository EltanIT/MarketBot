from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.config import bot


import app.kb.employee_keyboards as kb
from app.EmployeeStates import ClientCall, AllOrders, RedactProduct
from app.kb.client_keyboards import end_call, main_reply

from db import employee_requests, user_requests
from .common import clearEmployeeDB


router = Router(name=__name__)


@router.message(Command('work'))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer('Доброго времени суток!\n' + 
                         'Начинаем прием заявок?',
                           reply_markup = kb.start_inline)
    





@router.callback_query(F.data.startswith('help'))
async def help(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    command = callback.data.split('_')[1]
    employee = await employee_requests.getEmployeeByUserId(callback.from_user.id)
    if employee:
      client = await user_requests.getUserById(employee.active_client_id)
      if command == 'yes':
        await state.set_state(ClientCall.Help)

        text = callback.message.text
        
        await callback.message.edit_text(text, reply_markup = kb.create_order)

        await bot.send_message(client.user_id, 'Скоро с вами свяжутся через личное сообщение', reply_markup=end_call)
      else:
        await clearEmployeeDB(callback.from_user.id)

        await bot.delete_message(
                chat_id = callback.message.chat.id,
                message_id = callback.message.reply_to_message.message_id
              )
        await callback.message.delete()

        await callback.message.answer('Вы отказали клинету, для получения новых заявко выберите функцию на клавиатуре!', reply_markup = await kb.main_reply(callback.from_user.id))
        await bot.send_message(client.user_id, 'Мы не смогли найти сотрудника, попробуйте позже')

        
        







@router.message(F.text == 'Принимать заявки')
async def redact_busy(message: types.Message, state: FSMContext):

   employee = await employee_requests.getEmployeeByUserId(message.from_user.id)
   if not employee:
      return
   
   await employee_requests.updateBusyEmployee(employee.id, False)

   await message.answer('Теперь вам могут поступать заявки', reply_markup = await kb.main_reply(message.from_user.id))


@router.message(F.text == 'Не принимать заявки')
async def redact_busy(message: types.Message, state: FSMContext):

   employee = await employee_requests.getEmployeeByUserId(message.from_user.id)
   if not employee:
      return
   
   await employee_requests.updateBusyEmployee(employee.id, True)

   await message.answer('Теперь займитесь делом', reply_markup = await kb.main_reply(message.from_user.id))









@router.message(F.text == 'Закончить разговор ❌')
async def end_call_hdl(message: types.Message, state: FSMContext):
  await state.clear()
  employee = await employee_requests.getEmployeeByUserId(message.from_user.id)
  client = await user_requests.getUserById(employee.active_client_id)
  await clearEmployeeDB(message.from_user.id)

  await message.answer('Все состояния сброшены, вам снова могут поступать заявки', reply_markup = await kb.main_reply(message.from_user.id))

  await bot.send_message(client.user_id, "Сотрудник завершил диалог.", reply_markup = main_reply)


@router.message(F.text == 'Заявки')
async def orders(message: types.Message, state: FSMContext):

  await state.clear()
  await state.set_state(AllOrders.Category)
  await message.answer('Какие заказы хотите посмотреть?', reply_markup = kb.orders_categories)


@router.message(F.text == 'Товары')
async def products(message: types.Message, state: FSMContext):

  await state.clear()
  await state.set_state(RedactProduct.Category)
  await message.answer('Выберите категорию товаров:', reply_markup = kb.products_categories)




@router.callback_query(F.data == 'cancel')
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await clearEmployeeDB(callback.from_user.id)
    await callback.message.answer('Выберите функцию:',
                         reply_markup = kb.main_reply)









@router.callback_query(F.data.startswith('start'))
async def start_work(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    command = callback.data.split('_')[1]
    employee = await employee_requests.getEmployeeByUserId(callback.from_user.id)
    if employee:
      await callback.message.delete()
      if command == 'yes':
        await employee_requests.updateBusyEmployee(employee.id, False)
        await callback.message.answer('Начинаем работу, теперь вам могут поступать запросы от клиентов', reply_markup = await kb.main_reply(callback.from_user.id))
      else:
        await employee_requests.updateBusyEmployee(employee.id, True)
        await callback.message.answer('Тогда до завтра!', reply_markup = await kb.main_reply(callback.from_user.id))
    
