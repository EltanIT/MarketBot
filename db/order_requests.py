from db.models import async_session
from db.models import Order
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
from typing import Optional

from db.Enums import AppName, OrderStatus, DeliveryMethod



async def getAllOrdersByApp(appName: AppName) -> list['Order']:
    async with async_session() as session:
        orders = await session.scalars(select(Order).where(Order.app_name == appName))

        return orders.all()
    

async def getAllUserOrdersByUserId(user_id) -> list['Order']:
    async with async_session() as session:
        orders = await session.scalars(select(Order).where(Order.user_id == user_id))

        return orders.all()
    

async def getAllOrdersByEmployeeId(id) -> list['Order']:
    async with async_session() as session:
        orders = await session.scalars(select(Order).where(Order.employee_id == id))

        return orders.all()
    

async def getOrderById(id) -> Optional[Order]:
    async with async_session() as session:
        order = await session.scalar(select(Order).filter(Order.id == id))
        return order
    
async def getActiveOrderByUserId(id) -> Optional[Order]:
    async with async_session() as session:
        order = await session.scalar(select(Order).filter(Order.user_id == id and Order.status == OrderStatus.DURING_PAYMENT))
        return order
    


async def findOrderByFio(text: str) -> Optional[Order]:
    async with async_session() as session:
        order = await session.scalar(select(Order).filter(Order.fio.lower().contains(text.lower())))
        return order
    

async def createOrder(
        user_id, 
        fio: str, 
        phoneNumber: int, 
        address: str, 
        delivery_method: DeliveryMethod, 
        product_price: float, 
        opt_product_price: float,
        product_id: int, 
        optionally_product_id: int,
        product_count: int,
        optionally_product_count: int, 
        app_name: AppName, 
        createdAt: datetime
                      ) -> Order:
    async with async_session() as session:
        ended_at = createdAt
        ended_at += timedelta(days=8)

        order = Order(
                user_id=user_id,
                fio=fio,
                phone_number=phoneNumber,
                address=address,
                delivery_method=delivery_method,
                
                product_price=product_price,
                optionally_product_price=opt_product_price,

                product_id=product_id,
                optionally_product_id=optionally_product_id,

                product_count=product_count,
                optionally_product_count=optionally_product_count,

                app_name=app_name,
                created_at=createdAt,
                ended_at=ended_at
        )

        session.add(order)
        await session.commit()
        await session.refresh(order)
        # print(order.id)
        return order


async def updateOrderStatus(id, status: OrderStatus):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(status = status)
        await session.execute(stmt)
        await session.commit()

async def updateOrderFio(id, fio: str):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(fio = fio)
        await session.execute(stmt)
        await session.commit()

async def updateOrderAddress(id, address: str):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(address = address)
        await session.execute(stmt)
        await session.commit()

async def updateOrderPhoneNumber(id, number: str):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(phone_number = number)
        await session.execute(stmt)
        await session.commit()

async def updateOrderDeliveryMethod(id, method: DeliveryMethod):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(delivery_method = method)
        await session.execute(stmt)
        await session.commit()



async def updateOrderEmployee(id, employee_id: int):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(employee_id = employee_id)
        await session.execute(stmt)
        await session.commit()


async def updateOrderProductId(id, product_id: int):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(product_id = product_id)
        await session.execute(stmt)
        await session.commit()

async def updateOrderProductPrice(id, price: float):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(product_price = price)
        await session.execute(stmt)
        await session.commit()

async def updateOrderProductCount(id, count: int):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(product_count = count)
        await session.execute(stmt)
        await session.commit()

async def updateOrderEndedAt(id, date: datetime):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(ended_at = date)
        await session.execute(stmt)
        await session.commit()


async def updateOrderOptProductId(id, product_id: int):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(optionally_product_id = product_id)
        await session.execute(stmt)
        await session.commit()

async def updateOrderOptProductPrice(id, price: float):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(optionally_product_price = price)
        await session.execute(stmt)
        await session.commit()

async def updateOrderOptProductCount(id, count: int):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(optionally_product_count = count)
        await session.execute(stmt)
        await session.commit()



async def updateOrderVerify(id, is_verify: bool):
    async with async_session() as session:
        stmt = update(Order).where(Order.id == id).values(is_verify = is_verify)
        await session.execute(stmt)
        await session.commit()

async def deleteOrder(id):
    async with async_session() as session:
        stmt = delete(Order).where(Order.id == id)
        await session.execute(stmt)
        await session.commit()
