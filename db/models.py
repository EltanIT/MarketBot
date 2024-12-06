from typing import Any
from sqlalchemy import BigInteger, DateTime, Integer, Float, String, Boolean, ForeignKey, Table, Column, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from db.Enums import OrderStatus, UserRole, AppName, DeliveryMethod
from app.config import bot

import os

engine = create_async_engine(url='sqlite+aiosqlite:///db/db.sqlite3')
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key = True)
    user_id = mapped_column(BigInteger)
    username = mapped_column(String)
    role = mapped_column(Enum(UserRole), default=UserRole.CLIENT)
    is_search_employee = mapped_column(Boolean, default=False)
    active_order_id = mapped_column(Integer, ForeignKey('orders.id'))
    


class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key = True)
    user_id = mapped_column(Integer, ForeignKey('users.id'))

    name = mapped_column(String)

    rating = mapped_column(Float, default = 0.0)
    is_busy = mapped_column(Boolean, default = True)
    
    active_order_id = mapped_column(Integer, ForeignKey('orders.id'))
    active_client_id = mapped_column(Integer, ForeignKey('users.id'))


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key = True)
    user_id = mapped_column(Integer, ForeignKey("users.id"))

    fio = mapped_column(String)
    phone_number = mapped_column(Integer)
    address = mapped_column(String)
    delivery_method = mapped_column(Enum(DeliveryMethod))

    product_id = mapped_column(Integer, ForeignKey("products.id"))
    optionally_product_id = mapped_column(Integer, ForeignKey("optionally_products.id"))

    product_count = mapped_column(Integer)
    optionally_product_count = mapped_column(Integer)

    product_price = mapped_column(Float)
    optionally_product_price = mapped_column(Float)

    app_name = mapped_column(Enum(AppName))
    status = mapped_column(Enum(OrderStatus), default = OrderStatus.DURING_VERIFY)

    is_verify = mapped_column(Boolean, default=False)

    created_at = mapped_column(DateTime)
    ended_at = mapped_column(DateTime)

    employee_id = mapped_column(Integer, ForeignKey('employees.id'))



ProductOptionallyProduct = Table(
    'ProductOptionallyProduct',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key = True),
    Column('optionally_id', Integer, ForeignKey('optionally_products.id'), primary_key = True)
    )

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key = True)
    name = mapped_column(String)
    description = mapped_column(String)
    price = mapped_column(String)
    image = mapped_column(String)
    video = mapped_column(String)
    is_individual = mapped_column(Boolean, default = False)
    optionally: Mapped[list["OptionallyProduct"]] = relationship(secondary = ProductOptionallyProduct, back_populates='products', lazy='subquery')


class OptionallyProduct(Base):
    __tablename__ = 'optionally_products'

    id: Mapped[int] = mapped_column(primary_key = True)
    name = mapped_column(String)
    description = mapped_column(String)
    price = mapped_column(String)
    media = mapped_column(String)
    products: Mapped[list["Product"]] = relationship(secondary = ProductOptionallyProduct, back_populates='optionally')

    def __init__(self, name, description, price, media):
        self.name = name
        self.description = description
        self.price = price
        self.media = media

    def __str__(self):
        return f'id: {self.id}, name: {self.name}, price: {self.price}'




async def async_main():
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)

        # Если нужно сбросить бд, раскомментировать метод ниже.
        # await create_default_db()


        # Если нужно добавить нового сотрудника, то добавьте новый метод с id и username пользователя, а после перезапустите бота
        await addEmployee(6725589384, '@minigunbro')
        await addEmployee(6392239816, '@agregat_nicola')
        
        # Админов нет, есть только сотрудники
        # admins = await user_requests.getAllAdminsIds()
        # bot.admins_list = admins

        employees = await user_requests.getAllEmployeesIds()
        bot.employees_list = employees
           
       





from db import product_requests, optionally_product_requests, user_requests, employee_requests
async def create_default_db():
    await optionally_product_requests.createOptionallyProduct(
        'Выносные антенны радиоуправления',
        'Здесь будет описание товара',
        '2500.0₽',
        ['https://avatars.mds.yandex.net/i?id=f51a6635fc9f4b0ed4a5a6ffe057ea6d6ac220e4-6844425-images-thumbs&n=13']
    )
    await optionally_product_requests.createOptionallyProduct(
        'Аппаратура управления',
        'Здесь будет описание товара',
        '1499.99₽',
        ['https://avatars.mds.yandex.net/i?id=f51a6635fc9f4b0ed4a5a6ffe057ea6d6ac220e4-6844425-images-thumbs&n=13']
    )

    await optionally_product_requests.createOptionallyProduct(
        'Средства визуального контроля',
        'Здесь будет описание товара',
        '13990.0₽',
        ['https://avatars.mds.yandex.net/i?id=f51a6635fc9f4b0ed4a5a6ffe057ea6d6ac220e4-6844425-images-thumbs&n=13']
    )
    

    op1 = await optionally_product_requests.getOptionallyProductById(1)
    op2 = await optionally_product_requests.getOptionallyProductById(2)
    op3 = await optionally_product_requests.getOptionallyProductById(3)

    await product_requests.createProduct(
        "FPV дрон «Стужа»🚁",
        description='7-ми дюймовый дрон из текстолита.\n' +
                    'Масса дрона с АКБ - 1,6кг\n' +
                    'Максимальная скорость - 200 км/ч\n' +
                    'Грузоподъёмность - 2,5 кг\n' +
                    'Частота видеосигнала - 5.8 GHz\n' +
                    'Управление - ELRS\n\n' +

                    '*точную цену озвучит сотрудник, который свяжется с вами после заказа',
        price = '50000.0₽',
        image = 'AgACAgIAAxkBAAIe32dQaNHYJm3Y_Apmr8282StTt69fAALp5zEbgGSASlOrucrwMecvAQADAgADeQADNgQ',
        video =  'BAACAgIAAxkBAAIdIWdO-uidzB0MSfjorHclb7eJJqs4AAInYgACjdl5SuO-CCEJIeP7NgQ',
        optionally=[
            op1
        ]
    )
    await product_requests.createProduct(
        "Гусеничная платформа «Прометей»",
        description="1. Очень крутой 2. Быстрый\n\n" +
                    '*точную цену озвучит сотрудник, который свяжется с вами после заказа',
        price='52200.0₽',
        image = 'AgACAgIAAxkBAAIdJGdO-3eG5NWK3XZJwhE9K4CIoPyQAAKb7DEbjdl5Shr0WEmq5bRxAQADAgADeQADNgQ',
        video =  'BAACAgIAAxkBAAIdImdO-0BDJFjddVXPCx92ztW2CZSaAAIsYgACjdl5StDb747ZBPCdNgQ',
        optionally=[
            op1, op2, op3
        ]
    )
    await product_requests.createProduct(
        'Прибор РЭБ "Радио Нянь"',
        description="Мега крутое средство",
        price='23242.99₽',
        image = 'AgACAgIAAxkBAAIcvGdO7ko8IETUGBybE9WQHlIuJqprAAJI7DEbjdl5SqYc5lYxzocRAQADAgADeQADNgQ',
        video =  'BAACAgIAAxkBAAIdI2dO-1u5z1x7QDSUYFO422FhuQSmAAIuYgACjdl5SsQK61pvn8qMNgQ',
        optionally=[
            op2
        ]
    )

    # await user_requests.createUser(1464474322, '@geor_i', UserRole.ADMIN)



async def addEmployee(id, username):
    user = await user_requests.createUser(id, username, UserRole.EMPLOYEE)
    await employee_requests.createEmployee(user.id, username)


