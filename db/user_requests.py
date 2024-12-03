from db.models import async_session, User, Employee
from db.Enums import UserRole
from sqlalchemy import select, update, delete
import json
from typing import Optional, List




async def getAllEmployeesIds() -> list['int']:
    async with async_session() as session:
        employees = await session.scalars(select(User).where(User.role == UserRole.EMPLOYEE))
        fun = lambda employee: employee.user_id
        return list(map(fun, employees.all()))
    



async def getAllAdminsIds():
    async with async_session() as session:
        admins = await session.scalars(select(User).where(User.role == UserRole.ADMIN.name))

        fun = lambda admin: admin.user_id
        return map(fun, admins.all()) 

    



async def getUserById(id: int) -> Optional[User]:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == id))

        return user
    

async def getUserByUserId(id) -> Optional[User]:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == id))
        return user
    
    




async def createUser(user_id: int, username: str, role: UserRole = UserRole.CLIENT) -> User:
    async with async_session() as session:
        user = await getUserByUserId(user_id)

        if not user:
            user = User(
                user_id = user_id,
                username = username,
                role = role
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def updateUserRole(id: int, role: UserRole):
    async with async_session() as session:
        user = await getUserById(id)    
        
        if user:
            stmt = update(User).where(User.id == id).values(role = role)
            await session.execute(stmt)
            await session.commit()



async def updateUserIsSearchEmployee(id: int, value: bool):
    async with async_session() as session:
        user = await getUserById(id)    
        
        if user:
            stmt = update(User).where(User.id == id).values(is_search_employee = value)
            await session.execute(stmt)
            await session.commit()


async def updateUserActiveOrder(id: int, order_id: int):
    async with async_session() as session:
        user = await getUserById(id)    
        
        if user:
            stmt = update(User).where(User.id == id).values(active_order_id = order_id)
            await session.execute(stmt)
            await session.commit()
