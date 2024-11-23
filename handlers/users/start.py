import requests
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from data.config import ADMINS
from loader import dp,user_db,bot


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    try:
        telegram_id=message.from_user.id
        username=message.from_user.username
        if not user_db.select_user(telegram_id=telegram_id):
            user_db.add_user(telegram_id=telegram_id,username=username)

            #foydalanuvchini sanaymiz
            count=user_db.count_users()
            text="Yangi foydalanuvchi qo'shildi\n"
            text+=f"Bazada {count}-ta foydalanuvchi bor"
            await bot.send_message(ADMINS[0],text)

    except Exception as err:
        print(err)
    await message.answer(f"Assalomu alaykum, valyuta botiga xush kelibsiz {message.from_user.full_name}!")

@dp.message_handler(commands="valyuta")
async def valyuta_course(message: types.Message):
    try:
        response = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()

        text = f"Sana: {response[0]['Date']}\n\n"
        CURRENSY = ['USD', 'EUR', 'RUB', 'GBP']  # To'g'ri kodlar
        for item in response:
            if item['Ccy'] in CURRENSY:
                text += f"1 {item['CcyNm_UZ']} ~ {item['Rate']} so'm\n"

        await message.answer(text)
    except Exception as err:
        print(f"Xatolik: {err}")
        await message.answer("Valyuta kurslarini olishda xatolik yuz berdi.")
