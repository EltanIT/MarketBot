from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import product_requests, optionally_product_requests





async def products_inline(isIndividualButtonEnabled: bool = True, isBack: bool = True):

    products = await product_requests.getAllProducts()

    keyboard = InlineKeyboardBuilder()
    

    for product in products:
        keyboard.add(InlineKeyboardButton(text=product.name, callback_data=f"product_{product.id}"))

    if isIndividualButtonEnabled:
        keyboard.add(InlineKeyboardButton(text="Индивидуальный заказ", callback_data=f"product_individual"))

    if isBack:
        keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"product_cancel"))

    return keyboard.adjust(1).as_markup()


async def optionally_products_inline(product_id: int = None):

    optionallies = []

    if not product_id:
        optionallies = await optionally_product_requests.getAllOptionallyProducts()
    else:
        product = await product_requests.getProductById(product_id)
        if product:
            optionallies = product.optionally


    keyboard = InlineKeyboardBuilder()

    for optionally in optionallies:
        keyboard.add(InlineKeyboardButton(text=optionally.name, callback_data=f"optionally_{optionally.id}"))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"optionally_back"))
    return keyboard.adjust(1).as_markup()

