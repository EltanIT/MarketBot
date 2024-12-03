from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


from db import employee_requests


main_reply = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Сотрудники", callback_data="options_employees")]
])

employee_options = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить", callback_data="employees_add")],
    [InlineKeyboardButton(text="Удалить", callback_data="employees_delete")],
])

cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
])




async def employees_inline():

    employees = await employee_requests.getAllEmployee()

    keyboard = InlineKeyboardBuilder()

    for employee in employees:
        keyboard.add(InlineKeyboardButton(text=employee.name, callback_data=f"employee_{employee.id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"employee_cancel"))
    return keyboard.adjust(1).as_markup()


