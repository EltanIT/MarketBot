from db.models import async_session
from db.models import OptionallyProduct
from sqlalchemy import select, update, delete
import json
from typing import Optional, List



async def getOptionallyProductById(id: int) -> Optional[OptionallyProduct]:
    async with async_session() as session:
        optionallyProduct = await session.scalar(select(OptionallyProduct).where(OptionallyProduct.id == id))

        return optionallyProduct
    

async def getAllOptionallyProducts() -> list['OptionallyProduct']:
    async with async_session() as session:
        optionallyProducts = await session.scalars(select(OptionallyProduct))

        return optionallyProducts.all()
    

async def createOptionallyProduct(name: str, description: str, price: str, media: list['str']) -> OptionallyProduct:
    async with async_session() as session:
        product = OptionallyProduct(
            name=name,
            description=description,
            price=price,
            media=json.dumps(media)
        )

        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product



async def updateOptionallyProductName(product_id: int, name: str):
    async with async_session() as session:
        stmt = update(OptionallyProduct).where(OptionallyProduct.id == product_id).values(name = name)
        await session.execute(stmt)
        await session.commit()

async def updateOptionallyProductPrice(product_id: int, price: float):
    async with async_session() as session:
        stmt = update(OptionallyProduct).where(OptionallyProduct.id == product_id).values(price = price)
        await session.execute(stmt)
        await session.commit()

async def updateOptionallyProductDescription(product_id: int, des: str):
    async with async_session() as session:
        stmt = update(OptionallyProduct).where(OptionallyProduct.id == product_id).values(description = des)
        await session.execute(stmt)
        await session.commit()

async def deleteOptionallyProductById(product_id: int):
    async with async_session() as session:
        stmt = delete(OptionallyProduct).where(OptionallyProduct.id == product_id)
        await session.execute(stmt)
        await session.commit()
