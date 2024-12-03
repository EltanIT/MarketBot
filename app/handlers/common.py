from db import product_requests, optionally_product_requests, user_requests




async def aboutOrderText(order) -> str:

    if not order:
      return '-'
    

    client = await user_requests.getUserById(order.user_id)
    product = await product_requests.getProductById(order.product_id)
    optionally_product = await optionally_product_requests.getOptionallyProductById(order.optionally_product_id)


    optionally_product_text = ''
    product_text = ''
    sum = (order.product_price*order.product_count)+(order.optionally_product_price*order.optionally_product_count)

    if product:
       product_text = (
          f'<strong>Товар</strong>: {product.id}, {product.name}\n' +
                                     f'Цена товара: {order.product_price}₽\n' +
                                     f'Кол-во товара: {order.product_count}\n' +
                                     f'Всего за товар: {order.product_price*order.product_count}₽\n\n'
       )


    if optionally_product:
      optionally_product_text = (
          f'<strong>Доп. товар</strong>: {optionally_product.id}, {optionally_product.name}\n' +
          f'Цена товара: {order.optionally_product_price}₽\n' +
          f'Кол-во товара: {order.optionally_product_count}\n' +
          f'Всего за доп. товары: {order.optionally_product_price*order.optionally_product_count}₽\n\n'
      )





    return (
        f'ID заказа: {order.id}\n\n'+
        f'Заказчик: {client.username}\n'+
        f'Имя заказчика: {order.fio}\n'+
        f'Адресс: {order.address}\n'+
        f'Телефон: {order.phone_number}\n\n'+

        product_text +

        optionally_product_text +

        f'<strong>Общая цена</strong>: {sum}₽\n\n' +

        f'Статус: <strong>{order.status.value[0]}</strong>\n' +
        f'Доставка: <strong>{order.delivery_method.value}</strong>\n' +
                                     
        f'Дата заказа: {order.created_at}\n' +
        f'Дата окончания заказа: {order.ended_at}'
    )




