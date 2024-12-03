from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import app.kb.admin_keyboards as kb

from db import employee_requests


router = Router(name=__name__)



@router.message(Command('admin'))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer('Выберите опцию',
                           reply_markup = kb.main_reply)
    

@router.callback_query(F.data.startswith('options'))
async def options(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]

    if command == 'employees':
        await callback.message.edit_text('Выберите опцию:',
                           reply_markup = kb.employee_options)
        
    

@router.callback_query(F.data.startswith('employees'))
async def employees(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]
    
    if command == 'delete':
        await callback.message.edit_text('Выберите сотрудника для удаления:',
                           reply_markup = await kb.employees_inline()) 
    elif command == 'add':
        await callback.message.edit_text('Отправьте id пользователя', reply_markup = kb.cancel)
    


@router.callback_query(F.data.startswith('employee'))
async def employee(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[1]

    if command == 'cancel':
        await callback.message.edit_text('Выберите опцию:',
                           reply_markup = kb.employee_options)
        return
    

    employee = await employee_requests.getEmployeeById(command)

    if not employee:
        return
    
    await employee_requests.deleteEmployee(employee.id)
    
    await callback.message.edit_text('Сотрудник удален!',
                           reply_markup = await kb.employees_inline())
    




@router.callback_query(F.data == 'cancel')
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.edit_text('Выберите опцию',
                           reply_markup = kb.main_reply)
  



