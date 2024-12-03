from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.Enums import DeliveryMethod, OrderStatus
from db import order_requests, user_requests


main_reply = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Товары")],
    [KeyboardButton(text="Помощь 🆘")],
    [KeyboardButton(text="Мои заказы 📋")]
],
resize_keyboard=True)



cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
])

cancel_reply = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отмена')]
])

end_call = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Завершить разговор ❌")]
])

about_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Заказать", callback_data="about_product_buy"), InlineKeyboardButton(text="Назад", callback_data="about_product_cancel")]
])

before_ordering_change = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Доп. аппаратура", callback_data="before_ordering_additionally")],
    [InlineKeyboardButton(text="Пропустить ➡", callback_data="before_ordering_not")],
    [InlineKeyboardButton(text="Назад", callback_data="before_ordering_back")]
])

optionally_product_buy = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Купить", callback_data="selected_optionally_buy")],
    [InlineKeyboardButton(text="Назад", callback_data="selected_optionally_back")]
])


redact_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="ФИО", callback_data="redact_order_fio")],
    [InlineKeyboardButton(text="Адрес", callback_data="redact_order_address")],
    [InlineKeyboardButton(text="Номер телефона", callback_data="redact_order_phone")],
    [InlineKeyboardButton(text="Способ доставки", callback_data="redact_order_delivery")],
    [InlineKeyboardButton(text="Все в порядке ✅", callback_data="redact_order_ok")],
])


create_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data="create_order_yes")],
    [InlineKeyboardButton(text="Нет", callback_data="create_order_not")]
])


order_canceled = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отменить", callback_data="active_order_cancel")],
    [InlineKeyboardButton(text="Назад", callback_data="active_order_back")]
])


rating_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⭐", callback_data="rating_comment_1")],
    [InlineKeyboardButton(text="⭐⭐", callback_data="rating_comment_2")],
    [InlineKeyboardButton(text="⭐⭐⭐", callback_data="rating_comment_3")],
    [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rating_comment_4")],
    [InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rating_comment_5")],
    [InlineKeyboardButton(text="Отмена", callback_data="rating_comment_cancel")]
])


button_per_page = 16
async def orders_inline(user_id: int, page_num: int):

    user = await user_requests.getUserByUserId(user_id)

    if not user:
        return

    orders = await order_requests.getAllUserOrdersByUserId(user.id)

    orders = sorted(
        orders,
        key = lambda order: order.status.value[1], 
        reverse=False
    )

    start_index = page_num * button_per_page
    end_index = min(start_index + button_per_page, len(orders))

    orders = orders[start_index:end_index]



    keyboard = InlineKeyboardBuilder()

    for order in orders:
        keyboard.add(InlineKeyboardButton(text=f'{order.id} {order.status.value[2]}', callback_data=f"order_{order.id}"))
    keyboard.adjust(2)

    keyboard.row(
        InlineKeyboardButton(text=f'<< Назад', callback_data= f"page_{page_num-1}"),
        InlineKeyboardButton(text=f'Далее >>', callback_data=f"page_{page_num+1}")
    )    
    
    return keyboard.as_markup()


async def delivery_methods():

    methods = [e for e in DeliveryMethod]

    if not methods:
        return


    keyboard = InlineKeyboardBuilder()

    for method in methods:
        keyboard.add(InlineKeyboardButton(text = str(method.value) , callback_data=f"delivery_{method.name}"))
    return keyboard.adjust(1).as_markup()



async def about_delivery_inline(user_id: int):

    orders = await order_requests.getAllUserOrdersByUserId(user_id)


    keyboard = InlineKeyboardBuilder()

    for order in orders:
        keyboard.add(InlineKeyboardButton(text=str(order.id), callback_data=f"order_{order.id}"))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"cancel"))
    return keyboard.adjust(2).as_markup()



cancel_reply = ReplyKeyboardMarkup(
    resize_keyboard = True,
    keyboard = [
        [KeyboardButton(text = 'Отмена')]
    ]
)


async def cancel_inline(data: str, text: str = "Отмена"):

    keyboard = InlineKeyboardBuilder()

    data = f"{data}_cancel"
    print(data)

    keyboard.add(InlineKeyboardButton(text=text, callback_data=data))
    return keyboard.adjust(1).as_markup()




