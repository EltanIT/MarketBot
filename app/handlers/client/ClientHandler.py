from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from app.config import bot
from aiogram.filters import Command

import app.kb.client_keyboards as kb
from app.kb.common import products_inline
from app.kb.employee_keyboards import help_inline, main_reply, end_call
from app.ClientStates import SelectProduct, EmployeeCall, RedactOldOrder

from db import employee_requests, user_requests
from .common import searchBusyEmployeeForUserId, sendMessageEmployee


router = Router(name=__name__)


@router.callback_query(F.data == 'cancel')
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    
    await state.clear()

    await clearAllClientStates(callback.from_user.id)

    await state.set_state(SelectProduct.Product)

    await callback.message.delete()
    await callback.message.answer('Выберите товар:',
                         reply_markup = await products_inline(isBack = False))   

@router.message(F.text == 'Отмена')
async def cancel(message: types.Message, state: FSMContext):
    
    message1 = await message.answer('ОПЕРАЦИЯ ОТМЕНЕНА',
                              reply_markup = kb.main_reply)
    
    await state.clear()

    await clearAllClientStates(message.from_user.id)

    await state.set_state(SelectProduct.Product)

    await message.delete()

    await message.answer('Выберите товар:',
                         reply_markup = await products_inline(isBack = False))
    


@router.message(EmployeeCall.DescriptionProduct)
async def help_msg(message: types.Message, state: FSMContext):
    
    employee = await employee_requests.getEmployeeWithActiveClientByClientId(message.from_user.id)

    if employee:
       await employee_requests.updateActiveClientEmployee(employee.id, None)
    
    text = message.text
    
    await state.set_state(EmployeeCall.Call)

    await message.answer('Мы уже ищем свободного сотрудника, готового вам помочь.\n\n' +
                         'Пожалуйста, ожидайте..',
                          reply_markup = kb.cancel,
                          reply_to_message_id = message.message_id)
  

    employee = await searchBusyEmployeeForUserId(message.from_user.id, message.from_user.username)

    if not employee:
      return
    
    user = await user_requests.getUserById(employee.user_id)
    if not user:
        await state.clear()
        await message.answer('Произошла ошибка и мы не смогли найти свободного сотрудника для консультации.\n\n' +
                         'Попробуйте позже :)')
        return


    from_user = message.from_user
    message = await sendMessageEmployee(
       chat_id = user.user_id,
       text = text,
       reply_markup = end_call
    )

    await sendMessageEmployee(
       chat_id = user.user_id,
       text = 
        f'Клиенту @{from_user.username} нужна помощь с выбором товара\n\n' +
        f'ID пользователя: {from_user.id}\n' +
        f'Имя пользователя: {from_user.first_name} {from_user.last_name}',
       message_id = message.message_id,
       reply_markup = help_inline     
    )
    
@router.message(F.text == 'Помощь 🆘')
async def help(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(EmployeeCall.DescriptionProduct)

    await message.answer('Если вы не знаете, что именно вам нужно или не смогли найти нужный товар, то я могу помочь вам!\n\n' +
                         'Опишите то, что вы ищете в следующем сообщении.',
                           reply_markup = kb.cancel)
    
@router.message(F.text == 'Мои заказы 📋')
async def my_orders(message: types.Message, state: FSMContext):
    await state.clear()

    await state.set_state(RedactOldOrder.OrderId)
    await state.update_data(page_num = 0)

    message = await message.answer(f'Ваши заказы:',
                           reply_markup = await kb.orders_inline(message.from_user.id, 0))
    
    await state.update_data(main_msg = message.message_id)
    
@router.message(F.text == 'Товары')
async def my_orders(message: types.Message, state: FSMContext):
    await state.clear()

    await clearAllClientStates(message.from_user.id)

    await state.set_state(SelectProduct.Product)

    await message.answer('Выберите товар:',
                         reply_markup = await products_inline(isBack = False))
    




@router.message(F.text == 'Завершить разговор ❌')
async def call_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    
    employee = await employee_requests.getEmployeeWithActiveClientByClientId(message.from_user.id)

    if employee:
      await employee_requests.updateActiveClientEmployee(employee.id, None)
      await employee_requests.updateActiveOrderEmployee(employee.id, None)
      await employee_requests.updateBusyEmployee(employee.id, False)

    await clearAllClientStates(message.from_user.id)
    
   

    await state.set_state(SelectProduct.Product)

    await message.answer('Разговор завершен', reply_markup=kb.main_reply)
    await message.answer('Выберите товар:',
                         reply_markup = await products_inline(isBack = False))
    
    
    employee_user = await user_requests.getUserById(employee.id)
    await bot.send_message(employee_user.user_id, "Пользователь завершил диалог, вы больше не можете изменять заказ", reply_markup=await main_reply(employee_user.user_id))



@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    print(f'{message.from_user}')
    await state.clear()

    await clearAllClientStates(message.from_user.id)

    await state.set_state(SelectProduct.Product)

    await message.answer('Приветствую!\n'+
                         'Я робот консультант магазина "Чкаловские Беркуты"🦅.' +
                         'Помогу выбрать Вам нужный товар и оформить заказ.😋\n\n' +
                         'тех.поддержка: @failxz',
                           reply_markup = kb.main_reply)
    await message.answer('Выберите товар:',
                         reply_markup = await products_inline(isBack = False))
    


@router.message()
async def remove_message(message: types.Message, state: FSMContext):
  print(message)
  await message.delete()



async def clearAllClientStates(user_id):
   user = await user_requests.getUserByUserId(user_id)
   if user:
      await user_requests.updateUserIsSearchEmployee(user.id, False)
    
