from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from app.config import bot

import app.kb.client_keyboards as kb
from app.kb.common import products_inline, optionally_products_inline
from app.ClientStates import SelectProduct, CreateOrder, EmployeeCall

from db import product_requests, optionally_product_requests, employee_requests, user_requests

from .common import searchBusyEmployeeForUserId, sendMessageEmployee
from app.kb.employee_keyboards import help_inline


router = Router(name=__name__)




@router.callback_query(StateFilter(SelectProduct.IndividualProduct), F.data == 'individual_product_cancel')
async def cancel_individualProduct(callback: types.CallbackQuery, state: FSMContext):
    
      await state.set_state(SelectProduct.Product)

      await callback.message.edit_text('Выберите товар:',
                         reply_markup = await products_inline(isBack = False))





@router.callback_query(SelectProduct.Product, F.data.startswith('product_'))
async def product(callback: types.CallbackQuery, state: FSMContext):
    
    command = callback.data.split('_')[1]


    if command == 'cancel':
      await state.clear()
      await state.set_state(SelectProduct.Product)

      await callback.message.edit_text('Выберите товар:',
                          reply_markup = await products_inline(isBack = False))
      return
    
    if command == 'individual':
      await state.set_state(SelectProduct.IndividualProduct)

      await callback.message.edit_text(f'Опишите интересующую вас разработку и я отправлю ваш запрос сотруднику для обработки',
                            reply_markup = await kb.cancel_inline(data = 'individual_product', text = 'Назад'))
      return
    
    else:
       
      product = await product_requests.getProductById(command)

      if not product:
        await callback.message.edit_text('Товар уже раскупили :(',
                              reply_markup = await kb.cancel_inline(data = 'product', text = 'Назад'))
        return
      
      await state.set_state(SelectProduct.AboutProduct)

      short_des = (
          f'{product.name}\n' +
          f'Цена: <strong>{product.price}</strong>\n\n'
      )

      await state.update_data(product_id = product.id)
      await state.update_data(short_des = short_des)


      await callback.message.delete()
      messages = await about_product_msg(product, callback.message, short_des)

      await callback.message.answer(
         text = 'Функции:',
         reply_markup = kb.about_product,
         reply_to_message_id = messages[-1].message_id
      )
      await state.update_data(
        product_messages = map(lambda m: m.message_id, messages)
      )

    

@router.callback_query(SelectProduct.AboutProduct, F.data.startswith('about_product'))
async def about_product(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    short_des = data['short_des']

    command = callback.data.split('_')[2]


    product_messages = data['product_messages']

    await bot.delete_messages(
      callback.message.chat.id,
      product_messages
    )

    if command == 'buy':
      await state.set_state(SelectProduct.BeforeOrdering)

      await callback.message.edit_text(
          short_des +
          'Вместе с этим товаром доступны дополнительные аксессуары',
          reply_markup = kb.before_ordering_change
      )

    elif command == 'cancel':
      await state.set_state(SelectProduct.Product)

      await callback.message.edit_text(
         'Доступные товары:',
          reply_markup = await products_inline(isBack = False))
      


@router.callback_query(SelectProduct.BeforeOrdering, F.data.startswith('before_ordering'))
async def before_ordering(callback: types.CallbackQuery, state: FSMContext):

    
    data = await state.get_data()
    product = await product_requests.getProductById(data['product_id'])

    if not product:
      await state.set_state(SelectProduct.Product)
      await callback.message.edit_text('Такого товара нет,\n\nВыберите товар:',
                         reply_markup = await products_inline(isBack = False))
      return
    
    
    short_des = (
          f'{product.name}\n' +
          f'Цена: <strong>{product.price}</strong>\n\n'
    )
    await state.update_data(short_des = short_des)

    command = callback.data.split('_')[2]


    if command == 'back':
      await state.set_state(SelectProduct.AboutProduct)

      await state.update_data(product_id = product.id)

      await callback.message.delete()
      messages = await about_product_msg(product, callback.message, short_des)

      await callback.message.answer(
         text = 'Функции:',
         reply_markup = kb.about_product,
         reply_to_message_id = messages[-1].message_id
      )

      await state.update_data(
        product_messages = map(lambda m: m.message_id, messages)
      )
      return
    

    if command == "additionally":
       await state.set_state(SelectProduct.OptionallyProduct)

       await callback.message.edit_text(
          short_des + 
          'Вот вся доступная доп. аппаратура для данного товара:',
          reply_markup = await optionally_products_inline(product.id)
       )
    elif command == 'not':
        await state.set_state(CreateOrder.ProductCount)
        await state.update_data(optionally_product_id = None)

        await callback.message.delete()
        await callback.message.answer(
          short_des + 
          f'Сколько единиц товара вы хотите заказать?',
          reply_markup = kb.cancel_reply
        )
        


@router.callback_query(SelectProduct.OptionallyProduct, F.data.startswith('optionally'))
async def optionally(callback: types.CallbackQuery, state: FSMContext):

    data = await state.get_data()

    short_des = data['short_des']

    command = callback.data.split('_')[1]


    if command == 'back':
        await state.set_state(SelectProduct.BeforeOrdering)
      
        await callback.message.edit_text(
          short_des +
          'Вместе с этим товаром доступны дополнительные аксессуары',
          reply_markup = kb.before_ordering_change
        )
        return
    

    await state.update_data(optionally_product_id = int(command))

    optionally_product = await optionally_product_requests.getOptionallyProductById(command)

    if not optionally_product:
      return
      
    await callback.message.edit_text(
       f'{optionally_product.name}\n' +
       f'Цена: {optionally_product.price}\n\n' +
       f'Описание:\n{optionally_product.description}',
       reply_markup = kb.optionally_product_buy)


@router.callback_query(SelectProduct.OptionallyProduct, F.data.startswith('selected_optionally'))
async def select_optionally(callback: types.CallbackQuery, state: FSMContext):

    data = await state.get_data()

    product = await product_requests.getProductById(data['product_id'])
    short_des = data['short_des']

    command = callback.data.split('_')[2]


    if command == 'back':
       await state.set_state(SelectProduct.OptionallyProduct)

       await callback.message.edit_text(
          short_des + 
          'Вот вся доступная доп. аппаратура для данного товара:',
          reply_markup = await optionally_products_inline(product.id)
       )
       return
    
    if command == 'buy':
        await state.set_state(CreateOrder.ProductCount)

        data = await state.get_data()
        short_des = data['short_des']

        optionally_product_id = data['optionally_product_id']

        optionally_product = await optionally_product_requests.getOptionallyProductById(optionally_product_id)

        if not optionally_product:
          await callback.message.edit_text('Извините, но товар закончился')
          return
      
        short_des += (
           f'{optionally_product.name}\n' +
           f'Цена: {optionally_product.price}₽\n\n'
        )

        await state.update_data(short_des = short_des)

        await callback.message.delete()
        await callback.message.answer(
           short_des + 
           f'Сколько единиц основного товара вы хотите заказать?',
           reply_markup = kb.cancel_reply
        )
        



@router.message(SelectProduct.IndividualProduct)
async def individual_product(message: types.Message, state: FSMContext):

    employee = await employee_requests.getEmployeeWithActiveClientByClientId(message.from_user.id)

    if employee:
       await employee_requests.updateActiveClientEmployee(employee.id, None)
    
    text = message.text
    
    await state.set_state(EmployeeCall.Call)
    
    await message.answer('Мы уже ищем свободного сотрудника, готового вам помочь.\n\n' +
                         'Пожалуйста, ожидайте..',
                          reply_markup = kb.cancel)

    
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
       text = text
    )

    await sendMessageEmployee(
       chat_id = user.user_id,
       text = 
        f'Клиенту @{from_user.username} нужна помощь с индивидуальным заказом\n\n' +
        f'ID пользователя: {from_user.id}\n' +
        f'Имя пользователя: {from_user.first_name} {from_user.last_name}',
       message_id = message.message_id,
       reply_markup = help_inline     
    )


    

async def about_product_msg(product, message: types.Message, short_des: str) -> list[types.Message]:
    media_group = []


    media_group.append(
      types.InputMediaVideo(
           media = product.video
      )
    )
   
    media_group.append(
      types.InputMediaPhoto(
           media = product.image
      )
    )
    
      
       

    messages = await bot.send_media_group(
      chat_id = message.chat.id, 
      media = media_group
    )
  
    await messages[-1].edit_caption(
       caption = (
          short_des +
          f'Описание:\n{product.description}'
       )
    )

    return messages