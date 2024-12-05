from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from app.config import bot

import app.kb.employee_keyboards as kb
from app.kb.common import products_inline, optionally_products_inline

from db import product_requests, optionally_product_requests
from db.models import Product, OptionallyProduct

from app.EmployeeStates import RedactProduct





router = Router(name = __name__)





@router.callback_query(RedactProduct.Category, F.data.startswith('product_category'))
async def product_category(callback: types.CallbackQuery, state: FSMContext):
    command = callback.data.split('_')[2]

    await state.update_data(main_msg = callback.message.message_id)
    
    if command == 'product':
      await state.set_state(RedactProduct.SelectProduct)

      await callback.message.edit_text(
         'Все товары:', 
         reply_markup = await products_inline(isIndividualButtonEnabled=False)
      )
      return
    elif command == 'optionally':
       await state.set_state(RedactProduct.SelectOptProduct)

       await callback.message.edit_text(
         'Все доп. товары:', 
         reply_markup = await optionally_products_inline()
      )
    elif command == 'addProduct':
       
       product1 = await product_requests.getProductById(1)

       product = await product_requests.createProduct(
          name = '-',
          description = '',
          price = '0₽',
          image = product1.image,
          video = product1.video,
          optionally = [],
          is_individual = False
       )


       await state.set_state(RedactProduct.SelectProduct)

       await callback.message.delete()
       messages = await sendProductMedia(product, callback.message)
       
       product_msg = messages[-1]

       caption = await aboutProductText(product)
       await product_msg.edit_caption(
         caption = caption
       )

       main_msg = await callback.message.answer(
          'Что хотите изменить в товаре?',
          reply_markup = kb.product_commands,
          reply_to_message_id = product_msg.message_id
       )

       await state.update_data(product = product)
       await state.update_data(product_msg = product_msg.message_id)
       await state.update_data(main_msg = main_msg.message_id)
       await state.update_data(product_messages = map(lambda m: m.message_id, messages))
    elif command == 'addOptionally':
       
       product = await optionally_product_requests.createOptionallyProduct(
          name = '-',
          description = '',
          price = 0,
          media = []
       )

       await state.set_state(RedactProduct.SelectOptProduct)

       await callback.message.delete()

       text = await aboutOptionallyText(product)
       product_msg = await callback.message.answer(
          text
       )

       main_msg = await callback.message.answer(
          'Что хотите изменить в товаре?',
          reply_markup = kb.opt_product_commands,
          reply_to_message_id = product_msg.message_id
       )

       await state.update_data(product = product)
       await state.update_data(product_msg = product_msg.message_id)
       await state.update_data(main_msg = main_msg.message_id)



@router.callback_query(RedactProduct.SelectProduct, F.data.startswith('product'))
async def product(callback: types.CallbackQuery, state: FSMContext):
    command = callback.data.split('_')[1]

    if command == 'cancel':
       await state.set_state(RedactProduct.Category)
       await callback.message.edit_text('Выберите категорию товаров:', reply_markup = kb.products_categories)
       return
    

    product = await product_requests.getProductById(command)
    if not product:
       await state.set_state(RedactProduct.SelectProduct)
       await callback.message.edit_text(
           'Такого товара нет', 
           reply_markup = await products_inline(False)
       )
       return
    

    await callback.message.delete()
    messages = await sendProductMedia(product, callback.message)

    product_msg = messages[-1]

    caption = await aboutProductText(product)
    await product_msg.edit_caption(
      caption = caption
    )

    main_msg = await callback.message.answer(
      'Что хотите изменить в товаре?',
      reply_markup = kb.product_commands,
      reply_to_message_id = product_msg.message_id
    )

    await state.set_state(RedactProduct.SelectProduct)

    await state.update_data(product = product)
    await state.update_data(product_msg = product_msg.message_id)
    await state.update_data(main_msg = main_msg.message_id)
    await state.update_data(product_messages = map(lambda m: m.message_id, messages))
    
@router.callback_query(RedactProduct.SelectOptProduct, F.data.startswith('optionally'))
async def optionally(callback: types.CallbackQuery, state: FSMContext):
    command = callback.data.split('_')[1]

    if command == 'back':
       await state.set_state(RedactProduct.Category)
       await callback.message.edit_text('Выберите категорию товаров:', reply_markup = kb.products_categories)
       return
    

    product = await optionally_product_requests.getOptionallyProductById(command)
    if not product:
       await state.set_state(RedactProduct.SelectOptProduct)
       await callback.message.edit_text(
           'Такого товара нет', 
           reply_markup = await optionally_products_inline()
       )
       return
    

    await callback.message.delete()

    text = await aboutOptionallyText(product)
    product_msg = await callback.message.answer(
       text = text
    )

    main_msg = await callback.message.answer(
      'Что хотите изменить в доп. товаре?',
      reply_markup = kb.opt_product_commands,
      reply_to_message_id = product_msg.message_id
    )

    await state.set_state(RedactProduct.SelectOptProduct)

    await state.update_data(product = product)
    await state.update_data(product_msg = product_msg.message_id)
    await state.update_data(main_msg = main_msg.message_id)
    await state.update_data(product = product)
    



@router.callback_query(StateFilter(RedactProduct), F.data.startswith('redact_product'))
async def product_commands(callback: types.CallbackQuery, state: FSMContext):

    command = callback.data.split('_')[2]

    if command == 'cancel':
      data = await state.get_data()
      product_messages = data['product_messages']

      await bot.delete_messages(
         callback.message.chat.id,
         product_messages
      )


      await state.set_state(RedactProduct.SelectProduct)

      await callback.message.edit_text(
         'Все товары:', 
         reply_markup = await products_inline(isIndividualButtonEnabled = False))
      return
    
    if command == 'back':
      await state.set_state(RedactProduct.SelectProduct)

      await callback.message.edit_text(
         'Что хотите изменить в товаре?',
          reply_markup = kb.product_commands
      )
      return

    
    if command == 'name':

      await state.set_state(RedactProduct.ProductName)

      await callback.message.edit_text('Введите название товара', reply_markup = await kb.back_inline('redact_product'))
    elif command == 'price':

      await state.set_state(RedactProduct.ProductPrice)

      await callback.message.edit_text('Введите цену товара', reply_markup = await kb.back_inline('redact_product'))
    elif command == 'description':

      await state.set_state(RedactProduct.ProductDes)

      await callback.message.edit_text('Введите описание товара', reply_markup = await kb.back_inline('redact_product'))
    elif command == 'optionally':
       
       await state.set_state(RedactProduct.ProductOpt)

       await callback.message.edit_text(
          'Выберите нужные доп. товары или если такие уже есть нажмите чтобы их убрать', 
          reply_markup = await optionally_products_inline()
       )
    elif command == 'photo':
       await state.set_state(RedactProduct.Image)

       await callback.message.edit_text(
          'Отправьте новое фото товара', 
          reply_markup = await kb.back_inline('redact_product')
       )
    elif command == 'video':
       await state.set_state(RedactProduct.Video)

       await callback.message.edit_text(
          'Отправьте новое видео товара', 
          reply_markup = await kb.back_inline('redact_product')
       )
    elif command == 'delete':
       
      data = await state.get_data()
      product_messages = data['product_messages']

      product = data['product']
      if not product:
         return
      
      await product_requests.deleteProductById(product.id)

      await bot.delete_messages(
         callback.message.chat.id,
         product_messages
      )

      await state.set_state(RedactProduct.SelectProduct)

      await callback.message.edit_text(
         'Все товары:', 
         reply_markup = await products_inline(isIndividualButtonEnabled = False))
    
   
@router.callback_query(StateFilter(RedactProduct), F.data.startswith('redact_optionally'))
async def optionally_commands(callback: types.CallbackQuery, state: FSMContext):
    command = callback.data.split('_')[2]

    if command == 'cancel':
      data = await state.get_data()
      product_msg = data['product_msg']

      await bot.delete_message(
         callback.message.chat.id,
         product_msg
      )

      await state.set_state(RedactProduct.SelectOptProduct)

      await callback.message.edit_text(
         'Все доп. товары:', 
         reply_markup = await optionally_products_inline())
      return
    
    if command == 'back':
      await state.set_state(RedactProduct.SelectOptProduct)

      await callback.message.edit_text(
         'Что хотите изменить в товаре?',
          reply_markup = kb.opt_product_commands
      )
      return
    
    
    if command == 'name':

      await state.set_state(RedactProduct.OptProductName)

      await callback.message.edit_text('Введите название доп. товара', reply_markup = await kb.back_inline('redact_optionally'))

    elif command == 'price':

      await state.set_state(RedactProduct.OptProductPrice)

      await callback.message.edit_text('Введите цену доп. товара', reply_markup = await kb.back_inline('redact_optionally'))
    elif command == 'description':

      await state.set_state(RedactProduct.OptProductDes)

      await callback.message.edit_text('Введите описание доп. товара', reply_markup = await kb.back_inline('redact_optionally'))
    elif command == 'delete':
      data = await state.get_data()
      product_msg = data['product_msg']
      product = data['product']

      if not product:
         return

      await optionally_product_requests.deleteOptionallyProductById(product.id)

      await bot.delete_message(
         callback.message.chat.id,
         product_msg
      )

      await state.set_state(RedactProduct.SelectOptProduct)

      await callback.message.edit_text(
         'Все доп. товары:', 
         reply_markup = await optionally_products_inline())
   





@router.message(RedactProduct.ProductName)
async def redact_productName(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    product = data['product']
    if not product:
       return
    
    name = message.text
    await product_requests.updateProductName(product.id, name)
    product = await product_requests.getProductById(product.id)

    product_msg = data['product_msg']
    text = await aboutProductText(product)
    try:
      await bot.edit_message_caption(
         chat_id = message.chat.id,
         message_id = product_msg,
         caption = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(product = product)

    await state.set_state(RedactProduct.SelectProduct)

    main_msg = data['main_msg']
    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в товаре?', 
       reply_markup = kb.product_commands
    )

@router.message(RedactProduct.ProductPrice)
async def redact_productPrice(message: types.Message, state: FSMContext):
   
    data = await state.get_data()
    main_msg = data['main_msg']
    
    product = data['product']
    if not product:
       return
    
    await product_requests.updateProductPrice(product.id, message.text)
    product = await product_requests.getProductById(product.id)

    product_msg = data['product_msg']
    text = await aboutProductText(product)
    try:
      await bot.edit_message_caption(
         chat_id = message.chat.id,
         message_id = product_msg,
         caption = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(product = product)

    await state.set_state(RedactProduct.SelectProduct)

    
    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в товаре?', 
       reply_markup = kb.product_commands
    )

@router.message(RedactProduct.ProductDes)
async def redact_productDescription(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    product = data['product']
    if not product:
       return
    
    description = message.text
    await product_requests.updateProductDescription(product.id, description)
    product = await product_requests.getProductById(product.id)

    product_msg = data['product_msg']
    text = await aboutProductText(product)
    try:
      await bot.edit_message_caption(
         chat_id = message.chat.id,
         message_id = product_msg,
         caption = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(product = product)

    await state.set_state(RedactProduct.SelectProduct)

    main_msg = data['main_msg']
    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в товаре?', 
       reply_markup = kb.product_commands
    )

@router.callback_query(RedactProduct.ProductOpt, F.data.startswith('optionally'))
async def redact_productOptionally(callback: types.CallbackQuery, state: FSMContext):
    
    command = callback.data.split('_')[1]

    if command == 'back':
       await state.set_state(RedactProduct.SelectProduct)
       await callback.message.edit_text(
         text = 'Что нужно изменить в товаре?', 
         reply_markup = kb.product_commands
       )
       return
    
    
    
    
    optionally = await optionally_product_requests.getOptionallyProductById(command)
    if not optionally:
       return
    
    data = await state.get_data()
    
    product = data['product']
    if not product:
       return
    
    a = list(filter(lambda opt: opt.id == optionally.id, product.optionally))
    if len(a) > 0:
       await product_requests.deleteProductOptionally(product.id, optionally.id)
    else:
       await product_requests.addProductOptionally(product.id, optionally.id)

    product = await product_requests.getProductById(product.id)

    product_msg = data['product_msg']
    text = await aboutProductText(product)
    try:
      await bot.edit_message_caption(
         chat_id = callback.message.chat.id,
         message_id = product_msg,
         caption = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(product = product)

@router.message(RedactProduct.Image)
async def redact_productImage(message: types.Message, state: FSMContext):
    
    data = await state.get_data()
    main_msg = data['main_msg']
    
    if not message.photo:
      await message.delete()
      await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа. Отправьте 1 фото товара',
            reply_markup = await kb.cancel_inline('redact_product')
        )
      return
    
    product = data['product']
    if not product:
       return
    
    photo = message.photo[-1]

    await product_requests.updateProductImage(product.id, photo.file_id)
    product = await product_requests.getProductById(product.id)

    product_messages = data['product_messages']

    await bot.delete_messages(
         chat_id = message.chat.id,
         message_ids = product_messages
    )

    await message.delete()
    await bot.delete_message(
      chat_id = message.chat.id,
      message_id = main_msg
    )
    
    messages = await sendProductMedia(product, message)
       
    product_msg = messages[-1]

    caption = await aboutProductText(product)
    await product_msg.edit_caption(
     caption = caption
    )

    main_msg = await message.answer(
       'Что хотите изменить в товаре?',
       reply_markup = kb.product_commands,
       reply_to_message_id = product_msg.message_id
    )

    await state.update_data(product_msg = product_msg.message_id)
    await state.update_data(main_msg = main_msg.message_id)
    await state.update_data(product_messages = map(lambda m: m.message_id, messages))

    await state.set_state(RedactProduct.SelectProduct)

@router.message(RedactProduct.Video)
async def redact_productVideo(message: types.Message, state: FSMContext):
    
    data = await state.get_data()
    main_msg = data['main_msg']
    
    if not message.video:
      await message.delete()
      await bot.edit_message_text(
            chat_id = message.chat.id,
            message_id = main_msg,
            text = 'Неверный формат ответа. Отправьте 1 видео товара',
            reply_markup = await kb.cancel_inline('redact_product')
        )
      return
    
    product = data['product']
    if not product:
       return
    
    video = message.video

    
    await product_requests.updateProductVideo(product.id, video.file_id)
    product = await product_requests.getProductById(product.id)

    product_messages = data['product_messages']

    await bot.delete_messages(
         chat_id = message.chat.id,
         message_ids = product_messages
    )
    await message.delete()
    await bot.delete_message(
      chat_id = message.chat.id,
      message_id = main_msg
    )


    messages = await sendProductMedia(product, message)
       
    product_msg = messages[-1]

    caption = await aboutProductText(product)
    await product_msg.edit_caption(
     caption = caption
    )

    main_msg = await message.answer(
       'Что хотите изменить в товаре?',
       reply_markup = kb.product_commands,
       reply_to_message_id = product_msg.message_id
    )

    await state.update_data(product_msg = product_msg.message_id)
    await state.update_data(main_msg = main_msg.message_id)
    await state.update_data(product_messages = map(lambda m: m.message_id, messages))

    await state.set_state(RedactProduct.SelectProduct)




@router.message(RedactProduct.OptProductName)
async def redact_opt_productName(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    product = data['product']
    if not product:
       return
    
    name = message.text
    await optionally_product_requests.updateOptionallyProductName(product.id, name)
    product = await optionally_product_requests.getOptionallyProductById(product.id)

    product_msg = data['product_msg']
    text = await aboutOptionallyText(product)
    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = product_msg,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(product = product)

    await state.set_state(RedactProduct.SelectOptProduct)

    main_msg = data['main_msg']
    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. товаре?', 
       reply_markup = kb.opt_product_commands
    )

@router.message(RedactProduct.OptProductPrice)
async def redact_opt_productPrice(message: types.Message, state: FSMContext):
   
    data = await state.get_data()
    main_msg = data['main_msg']
    
    product = data['product']
    if not product:
       return
    
    await optionally_product_requests.updateOptionallyProductPrice(product.id, message.text)
    product = await optionally_product_requests.getOptionallyProductById(product.id)

    product_msg = data['product_msg']
    text = await aboutOptionallyText(product)
    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = product_msg,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(product = product)

    await state.set_state(RedactProduct.SelectOptProduct)

    
    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. товаре?', 
       reply_markup = kb.opt_product_commands
    )

@router.message(RedactProduct.OptProductDes)
async def redact_opt_productDescription(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    product = data['product']
    if not product:
       return
    
    description = message.text
    await optionally_product_requests.updateOptionallyProductDescription(product.id, description)
    product = await optionally_product_requests.getOptionallyProductById(product.id)

    product_msg = data['product_msg']
    text = await aboutOptionallyText(product)
    try:
      await bot.edit_message_text(
         chat_id = message.chat.id,
         message_id = product_msg,
         text = text
      )
    except TelegramBadRequest:
       ...

    await state.update_data(product = product)

    await state.set_state(RedactProduct.SelectOptProduct)

    main_msg = data['main_msg']
    await message.delete()
    await bot.edit_message_text(
       chat_id = message.chat.id,
       message_id = main_msg,
       text = 'Что нужно изменить в доп. товаре?', 
       reply_markup = kb.opt_product_commands
    )





async def sendProductMedia(product: Product, message: types.Message) -> list[types.Message]:
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

   
  
   messages = await bot.send_media_group(chat_id = message.chat.id, media = media_group)

   return messages



async def aboutProductText(product: Product) -> str:
   if not product:
      return '-'


   optionally_product_text = ''

   product_text = (
          f'<strong>Товар</strong>: {product.id}, {product.name}\n' +
          f'<strong>Цена</strong>: {product.price}\n\n' +
          f'<strong>Описание</strong>:\n{product.description}\n\n'
       )
       

   for optionally in product.optionally:
      optionally_product_text += (
            f'ID: {optionally.id}, {optionally.name}\n'
         )
      


   return (
       product_text +
       '<strong>Доп. товары</strong>:\n\n' +
       optionally_product_text
   )

async def aboutOptionallyText(product: OptionallyProduct) -> str:
   if not product:
      return '-'

   return (
          f'<strong>Товар</strong>: {product.id}, {product.name}\n' +
          f'<strong>Цена</strong>: {product.price}₽\n\n' +
          f'<strong>Описание</strong>:\n{product.description}'
       )
   