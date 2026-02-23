from aiogram import F,Router
from aiogram.types import Message,CallbackQuery,InlineQuery,InlineQueryResultArticle
from aiogram.types.input_text_message_content import InputTextMessageContent
from aiogram.types.link_preview_options import LinkPreviewOptions
from aiogram.filters import CommandStart,Command
from aiogram.fsm.state import StatesGroup,State
from aiogram.fsm.context import FSMContext
from app.database.bot_base import *
from app.funcs.languages import *
from app.keyboards.user.inline_buttons import *
from aiogram.enums import ParseMode,InlineQueryResultType
import asyncio
from aiogram.types.input_media_video import InputMediaVideo
from aiogram.types.input_media_photo import InputMediaPhoto
from app.funcs.functions import *
from datetime import *
from app.keyboards.admin.keyboard_buttons import *
from aiogram.types import ReplyKeyboardRemove
from app.funcs.filters.chat_filter import ChatTypeFilter
import random
from app.keyboards.admin.keyboard_buttons import *
from aiogram.types import ChatJoinRequest
import io
from aiogram.types import InputFile
import re
import os
from config import bot_username

user_search_by_image_router = Router()

class User(StatesGroup):
    menu = State()
    search_by_image = State()

class Anime(StatesGroup):
    menu = State()

@user_search_by_image_router.message(ChatTypeFilter(chat_type=["group", "supergroup"]))
async def action(msg: Message, state: FSMContext):
    pass

@user_search_by_image_router.callback_query(F.data.startswith('c'),User.search_by_image)
async def action(call: CallbackQuery, state: FSMContext):

    await state.set_state(User.menu)
    try:
        await call.message.edit_caption(caption=act_1_lang(),reply_markup=user_act_1_clbtn(),parse_mode=ParseMode.HTML)
    except:
        await call.message.answer_photo(photo="https://img1.teletype.in/files/8e/72/8e72aa35-c0c3-4c8a-a0e3-c3a56e81073f.jpeg",caption=act_1_lang(),reply_markup=user_act_1_clbtn(),parse_mode=ParseMode.HTML)
        await call.message.delete()
            
@user_search_by_image_router.message(F.photo, User.search_by_image)
async def action(msg: Message, state: FSMContext):

    data = await state.get_data()
    message_id = data.get("message_id")

    photo = msg.photo[-1]
    file = await msg.bot.get_file(photo.file_id)
    
    os.makedirs("downloads",exist_ok=True)
    file_path = f"downloads/{photo.file_id}.jpg"

    await msg.bot.download(file, destination=file_path)
    await state.update_data(path = file_path)

    await msg.delete()
    a = await msg.answer("<b>????Anime qidirilmoqda . . .</b>",parse_mode=ParseMode.HTML)

    image = await searching_anime_by_image(file_path)

    if image != "Error" and len(image['result'])>0:
        text = "<b>???Quyidagi natijalar siz qidirgan anime bo'lishi mumkin:</b>\n\n"

        google = []
        base = []

        for i in image['result']:
            if i['anilist']['isAdult'] == False:

                title = i['anilist']['title']['english']
                if not title:
                    title = i['anilist']['title']['romaji']

                media = await search_media_base(title,"anime")
                if media:
                    for i in media:
                        google.append(f"""<b>????{i['name']}</b> - <a href="https://t.me/{bot_username}?start={i['media_id']}">????Botda</a> \n-\n""")
                else:
                    google.append(f"""<b>????{title}</b> - <a href="https://www.google.com/search?q={title.replace(' ','+')}+media">???Googleda</a> \n-\n""")

        for i in base:
            if (len(re.sub(r'<.*?>', '', text)) + len(re.sub(r'<.*?>', '', i))) < 1024:
                text += i
            else:
                break

        for i in google:
            if (len(re.sub(r'<.*?>', '', text)) + len(re.sub(r'<.*?>', '', i))) < 1024:
                text += i
            else:
                break

        b = await msg.bot.edit_message_caption(
            caption=text,
            chat_id=msg.from_user.id,
            message_id=message_id,
            parse_mode=ParseMode.HTML,
            reply_markup=user_act_2_clbtn()
        )
        await state.update_data(message_id = b.message_id)
        await a.delete()

    else:
        text = "??????<i>Siz yuborgan rasm bo'yicha hech qanday anime topilmadi. Iltimos animening boshqa kadrlari rasmini yuborib ko'ring</i>"
        b = await msg.bot.edit_message_caption(
            caption=text,
            chat_id=msg.from_user.id,
            message_id=message_id,
            parse_mode=ParseMode.HTML,
            reply_markup=user_act_2_clbtn()
        )
        await state.update_data(message_id = b.message_id)
