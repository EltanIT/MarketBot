from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


from db import employee_requests, product_requests, order_requests
from db.Enums import AppName, OrderStatus


start_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data="start_yes")],
    [InlineKeyboardButton(text="Нет", callback_data="start_not")]
])


verify_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Верифицировать", callback_data="verify_yes")],
    [InlineKeyboardButton(text="Отказать", callback_data="verify_not")]
])


help_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Помочь", callback_data="help_yes")],
    [InlineKeyboardButton(text="Нет", callback_data="help_not")]
])


create_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать заказ", callback_data='create_order')]
])


end_call = ReplyKeyboardMarkup( keyboard=[
    [KeyboardButton(text='Закончить разговор ❌')],
],
resize_keyboard=True)





cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
])

about_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Доп. оборудование", callback_data="about_product_optionally"), InlineKeyboardButton(text="Фото и видео", callback_data="about_product_media")],
    [InlineKeyboardButton(text="Заказать", callback_data="about_product_buy")],
    [InlineKeyboardButton(text="Назад", callback_data="about_product_cancel")]
])

optionally_product_accept = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data="optionally_yes")],
    [InlineKeyboardButton(text="Нет", callback_data="optionally_not")]
])




redact_product_in_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="ID", callback_data="redact_product_id")],
    [InlineKeyboardButton(text="Цена", callback_data="redact_product_price")],
    [InlineKeyboardButton(text="Колличество", callback_data="redact_product_count")],
    [InlineKeyboardButton(text="Назад", callback_data="redact_product_back")]
])

redact_optProduct_in_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="ID", callback_data="redact_optProduct_id")],
    [InlineKeyboardButton(text="Цена", callback_data="redact_optProduct_price")],
    [InlineKeyboardButton(text="Количество", callback_data="redact_optProduct_count")],
    [InlineKeyboardButton(text="Удалить", callback_data="redact_optProduct_delete")],
    [InlineKeyboardButton(text="Назад", callback_data="redact_optProduct_back")]
])

order_payment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Оплата прошла", callback_data="payment_order_yes")],
    [InlineKeyboardButton(text="Назад", callback_data="payment_order_back")]
])


redact_old_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Редактировать", callback_data="redact_old_order_redact")],
    [InlineKeyboardButton(text="Обновить статус", callback_data="redact_old_order_status")],
    [InlineKeyboardButton(text="Назад", callback_data="redact_old_order_cancel")]
])

orders_categories = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Все", callback_data="order_category_all")],
    [InlineKeyboardButton(text="Мои", callback_data="order_category_my")]
])

products_categories = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Основные", callback_data="product_category_product")],
    [InlineKeyboardButton(text="Дополнительные", callback_data="product_category_optionally")],
    [InlineKeyboardButton(text="Добавить товар", callback_data="product_category_addProduct")],
    [InlineKeyboardButton(text="Добавить доп. товар", callback_data="product_category_addOptionally")],
])

product_commands = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Название", callback_data="redact_product_name")],
    [InlineKeyboardButton(text="Описание", callback_data="redact_product_description")],
    [InlineKeyboardButton(text="Цена", callback_data="redact_product_price")],
    [InlineKeyboardButton(text="Фото", callback_data="redact_product_photo")],
    [InlineKeyboardButton(text="Видео", callback_data="redact_product_video")],
    [InlineKeyboardButton(text="Доп. товары", callback_data="redact_product_optionally")],
    [InlineKeyboardButton(text="Удалить 🗑", callback_data="redact_product_delete")],
    [InlineKeyboardButton(text="Назад", callback_data="redact_product_cancel")],

])

opt_product_commands = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Название", callback_data="redact_optionally_name")],
    [InlineKeyboardButton(text="Описание", callback_data="redact_optionally_description")],
    [InlineKeyboardButton(text="Цена", callback_data="redact_optionally_price")],
    [InlineKeyboardButton(text="Удалить 🗑", callback_data="redact_optionally_delete")],
    [InlineKeyboardButton(text="Назад", callback_data="redact_optionally_cancel")]
])









async def main_reply(user_id):

    employee = await employee_requests.getEmployeeByUserUserId(user_id)

    if not employee:
        return None
    
    busy_text = 'Принимать заявки'
    
    if employee.is_busy == False:
        busy_text = 'Не принимать заявки'

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заявки")],
            [KeyboardButton(text="Товары")],
            [KeyboardButton(text=busy_text)],
        ],
        resize_keyboard=True
        )

   
    return keyboard



async def cancel_inline(callback_data):
    return InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data=f"{callback_data}_cancel")]
])



async def back_inline(callback_data):
    return InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data=f"{callback_data}_back")]
])





async def redact_order_inline(is_payment: bool = True, data: str = 'redact_order', is_date: bool = True):
    keyboard = InlineKeyboardBuilder()


    keyboard.add(InlineKeyboardButton(text="Товар", callback_data=f'{data}_product'))
    keyboard.add(InlineKeyboardButton(text="Доп. товар", callback_data=f'{data}_optProduct'))
    keyboard.add(InlineKeyboardButton(text="Индивидуальный заказ", callback_data=f"{data}_individual"))

    if is_date:
         keyboard.add(InlineKeyboardButton(text="Дата окончания", callback_data=f'{data}_date'))
            
    
    if is_payment:
        keyboard.add(InlineKeyboardButton(text="Оплата", callback_data=f'{data}_payment'))
    elif is_payment == False:
        keyboard.add(InlineKeyboardButton(text="Отпр. заявку", callback_data=f'{data}_request'))
    else:
        keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f'{data}_cancel'))

    return keyboard.adjust(1).as_markup()



button_per_page = 10
async def orders_inline(page_num: int, user_id = None):

    employee = await employee_requests.getEmployeeByUserUserId(user_id)
    

    orders = []
    if not user_id:
        orders = await order_requests.getAllOrdersByApp(AppName.TG)
    else:
        orders = await order_requests.getAllOrdersByEmployeeId(employee.id)

    start_index = page_num * button_per_page
    end_index = min(start_index + button_per_page, len(orders))

    orders = sorted(
        orders,
        key = lambda order: order.status.value[1], 
        reverse=False
    )
    orders = orders[start_index:end_index]


    keyboard = InlineKeyboardBuilder()

    for order in orders:
        keyboard.add(InlineKeyboardButton(text=f'{order.fio[:64]} {order.status.value[2]}', callback_data=f"order_{order.id}"))

    keyboard.adjust(1)

    keyboard.row(
        InlineKeyboardButton(text=f'<< Назад', callback_data= f"page_{page_num-1}"),
        InlineKeyboardButton(text=f'Далее >>', callback_data=f"page_{page_num+1}")
    )    
    return keyboard.as_markup()



async def custom_inline(data: str, text: str = "Отмена"):

    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text=text, callback_data=data))
    return keyboard.adjust(1).as_markup()



async def order_statutes(active_status):

    statuses = [e for e in OrderStatus]

    if not statuses:
        return


    active_index = statuses.index(active_status)

    statuses = statuses[(active_index+1):]
    

    keyboard = InlineKeyboardBuilder()

    for status in statuses:
        keyboard.add(InlineKeyboardButton(text = status.value[0], callback_data=f"status_{status.name}"))
    keyboard.add(InlineKeyboardButton(text = 'назад', callback_data=f"status_cancel"))
    return keyboard.adjust(1).as_markup()