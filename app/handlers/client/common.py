from db import user_requests, employee_requests
from db.models import Employee
import asyncio

from aiogram import types
from app.config import bot
from aiogram.utils.media_group import MediaGroupBuilder


async def searchBusyEmployeeForUserId(id, username: str) -> Employee:
    user = await user_requests.createUser(id, username)
    await user_requests.updateUserIsSearchEmployee(user.id, True)
    user.is_search_employee = True

    while(user.is_search_employee):
      print(f'search Employee {user.id}')
      employee = await employee_requests.getNotBusyEmployee()
      if employee:
         await employee_requests.updateBusyEmployee(employee.id, True)
         await user_requests.updateUserIsSearchEmployee(user.id, False)
         await employee_requests.updateActiveClientEmployee(employee.id, user.id)
         print('stop search Employee')
         return employee
      await asyncio.sleep(2)
      user = await user_requests.getUserByUserId(id)

    # await user_requests.updateUserIsSearchEmployee(user.id, False)
    # await employee_requests.updateActiveClientEmployee(employee.id, None)
    # await employee_requests.updateBusyEmployee(employee.id, False)



async def sendMediaEmployee(chat_id, photo, video, text: str, message_id = None, reply_markup = None) -> types.Message:
    
    media_group = MediaGroupBuilder()
    media_group.add_photo(media = photo, has_spoiler=True)
    media_group.add_video(media = video, has_spoiler=True)

    messages = await bot.send_media_group(
        chat_id = chat_id, 
        media = media_group.build(),
        reply_to_message_id = message_id
    )
    
    lastMessage = messages[-1]

    await lastMessage.edit_caption(
       caption = text
    )
    
    return lastMessage
  

async def sendMessageEmployee(chat_id, text: str, message_id = None, reply_markup = None) -> types.Message:
    return await bot.send_message(
        chat_id = chat_id, 
        text = text,
        reply_markup = reply_markup,
        reply_to_message_id = message_id
    )
       