from db.models import async_session, Employee
from db.Enums import UserRole
from sqlalchemy import select, update, delete
import json
from typing import Optional, List
from db import user_requests
    



async def getNotBusyEmployee() -> Optional[Employee]:
    async with async_session() as session:
        employee = await session.scalar(select(Employee).where(Employee.is_busy == False))
        
        return employee
    

async def getAllEmployee() -> list['Employee']:
    async with async_session() as session:
        employees = await session.scalars(select(Employee))

        return employees.all()
    

    

async def getEmployeeById(id: int) -> Optional[Employee]:
    async with async_session() as session:
        employee = await session.scalar(select(Employee).where(Employee.id == id))
        
        return employee
    

async def getEmployeeByUserId(id: int) -> Optional[Employee]:
    async with async_session() as session:
        user = await user_requests.getUserByUserId(id)
        if not user:
            return None
        
        employee = await session.scalar(select(Employee).where(Employee.user_id == user.id))
        
        return employee
    

async def getEmployeeByUserIdId(id: int) -> Optional[Employee]:
    async with async_session() as session:
        employee = await session.scalar(select(Employee).where(Employee.user_id == id))
        
        return employee

async def getEmployeeWithActiveClientByClientId(id: int) -> Optional[Employee]:
    async with async_session() as session:
        user = await user_requests.getUserByUserId(id)
        if not user:
            return None
        
        employee = await session.scalar(select(Employee).where(Employee.active_client_id == user.id))
        return employee
    

    
    
async def updateBusyEmployee(id, is_busy: bool):
    async with async_session() as session:
        stmt = update(Employee).where(Employee.id == id).values(is_busy = is_busy)
        await session.execute(stmt)
        await session.commit()


async def updateActiveClientEmployee(id, client_id):
    async with async_session() as session:
        stmt = update(Employee).where(Employee.id == id).values(active_client_id = client_id)
        await session.execute(stmt)
        await session.commit()


async def updateActiveOrderEmployee(id, order_id):
    async with async_session() as session:
        stmt = update(Employee).where(Employee.id == id).values(active_order_id = order_id)
        await session.execute(stmt)
        await session.commit()


async def deleteEmployee(id):
    async with async_session() as session:
        stmt = delete(Employee).where(Employee.id == id)
        await session.execute(stmt)
        await session.commit()



async def createEmployee(user_id: int, username: str):
    async with async_session() as session:
        employee = await getEmployeeByUserIdId(user_id)

        if not employee:
            session.add(Employee(
                name = username,
                user_id = user_id
            ))
            await session.commit()

