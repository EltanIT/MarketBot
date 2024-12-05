from db.models import async_session, Product, OptionallyProduct
from db import optionally_product_requests
from sqlalchemy import select, update, delete
import json
from typing import Optional, List


async def getAllProducts() -> list['Product']:
    async with async_session() as session:
        products = await session.scalars(select(Product).where(Product.is_individual == False))

        return products.all()
    
    

async def getProductById(id: int) -> Optional[Product]:
    async with async_session() as session:
        product = await session.scalar(select(Product).where(Product.id == id))

        return product
    

async def getProductByName(name: str) -> Optional[Product]:
    async with async_session() as session:
        product = await session.scalar(select(Product).where(Product.name.like(name)))

        return product




async def updateProductName(product_id: int, name: str):
    async with async_session() as session:
        stmt = update(Product).where(Product.id == product_id).values(name = name)
        await session.execute(stmt)
        await session.commit()

async def updateProductPrice(product_id: int, price: float):
    async with async_session() as session:
        stmt = update(Product).where(Product.id == product_id).values(price = price)
        await session.execute(stmt)
        await session.commit()

async def updateProductDescription(product_id: int, des: str):
    async with async_session() as session:
        stmt = update(Product).where(Product.id == product_id).values(description = des)
        await session.execute(stmt)
        await session.commit()

async def updateProductImage(product_id: int, image: str):
    async with async_session() as session:
        stmt = update(Product).where(Product.id == product_id).values(image = image)
        await session.execute(stmt)
        await session.commit()

async def updateProductVideo(product_id: int, video: str):
    async with async_session() as session:
        stmt = update(Product).where(Product.id == product_id).values(video = video)
        await session.execute(stmt)
        await session.commit()



async def addProductOptionally(product_id: int, optionally_id: int):
    async with async_session() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        optionally = await optionally_product_requests.getOptionallyProductById(optionally_id)

        product.optionally.append(optionally)

        await session.commit()

async def deleteProductOptionally(product_id: int, optionally_id: int):
    async with async_session() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        optionally = list(filter(lambda opt: opt.id == optionally_id, product.optionally))[0] 

        product.optionally.remove(optionally)
        await session.commit()
    



async def deleteProductById(product_id: int):
    async with async_session() as session:
        stmt = delete(Product).where(Product.id == product_id)
        await session.execute(stmt)
        await session.commit()
    


# async def getAllOptionallyProductsByProductId(product_id) -> None:
#     async with async_session() as session:
#         optionallyProducts = await session.scalar(select(OptionallyProduct).where(OptionallyProduct.products == product_id))
#         return optionallyProducts
    
    

async def createProduct(name: str, description: str, price: str, image: str, video: str, optionally: list['OptionallyProduct'], is_individual: bool = False) -> Product:
    async with async_session() as session:

        product = await getProductByName(name.lower())
        product = Product(
            name=name,
            description=description,
            price=price,
            image = image,
            video = video,
            optionally=optionally,
            is_individual=is_individual
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)

        return product
