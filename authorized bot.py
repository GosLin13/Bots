from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import asyncio
import os
import random


BOT_TOKEN = ""
bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

image_path = ""

user_data = {}
last_messages = {}

language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Русский"), KeyboardButton(text="English")]
    ],
    resize_keyboard=True
)

def main_menu(language):
    if language == "Русский":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти в приложение Ozon", url="")],
            [InlineKeyboardButton(text="Скачать автоматику на телефон", url="")],
            [InlineKeyboardButton(text="Перейти на сайт Стихи.ру", url="")],
            [InlineKeyboardButton(text="Техническая поддержка", callback_data="support")],
            [InlineKeyboardButton(text="Банковское приложение", callback_data="banking_app")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Go to Ozon app", url="")],
            [InlineKeyboardButton(text="Download automation on phone", url="")],
            [InlineKeyboardButton(text="Go to Stihi.ru website", url="")],
            [InlineKeyboardButton(text="Technical support", callback_data="support")],
            [InlineKeyboardButton(text="Banking app", callback_data="banking_app")]
        ])

def banking_app_menu(language):
    if language == "Русский":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Россия", callback_data="bank_russia")],
            [InlineKeyboardButton(text="Казахстан", callback_data="bank_kazakhstan")],
            [InlineKeyboardButton(text="Турция", callback_data="bank_turkey")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Russia", callback_data="bank_russia")],
            [InlineKeyboardButton(text="Kazakhstan", callback_data="bank_kazakhstan")],
            [InlineKeyboardButton(text="Turkey", callback_data="bank_turkey")]
        ])



@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if os.path.exists(image_path):
        image = FSInputFile(image_path)
        await message.answer_photo(image, caption="Привет! Добро пожаловать в наш бот!")
        new_message = await message.answer(
            "Пожалуйста, выберите язык:\nPlease choose your language:",
            reply_markup=language_keyboard
        )
        last_messages[message.from_user.id] = new_message.message_id
    else:
        await message.answer("Изображение не найдено. Проверьте путь к файлу.")


@dp.message(lambda message: message.text in ["Русский", "English"])
async def language_choice_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id in last_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_messages[user_id])
        except Exception:
            pass

    user_data[user_id] = {"language": message.text, "correct_answer": None}

    if message.text == "Русский":
        new_message = await message.answer(
            "Вы выбрали русский язык! Давайте проверим, что вы не робот.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await send_captcha(message, new_message.message_id, "Русский")
    elif message.text == "English":
        new_message = await message.answer(
            "You have selected English! Let's verify you are not a robot.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await send_captcha(message, new_message.message_id, "English")


async def send_captcha(message: types.Message, new_message_id: int, language: str):
    user_id = message.from_user.id
    num1 = random.randint(0, 100)
    num2 = random.randint(1, 100)  # Исключаем деление на 0
    operation = random.choice(["+", "-", "*", "/"])

    if operation == "+":
        correct_answer = round(num1 + num2, 1)
    elif operation == "-":
        correct_answer = round(num1 - num2, 1)
    elif operation == "*":
        correct_answer = round(num1 * num2, 1)
    elif operation == "/":
        correct_answer = round(num1 / num2, 1)

    user_data[user_id]["correct_answer"] = correct_answer

    question = f"Решите пример: {num1} {operation} {num2}" if language == "Русский" else f"Solve the problem: {num1} {operation} {num2}"

    wrong_answers = set()
    while len(wrong_answers) < 3:
        wrong = round(correct_answer + random.uniform(-10, 10), 1)
        if wrong != correct_answer:
            wrong_answers.add(wrong)
    options = list(wrong_answers) + [correct_answer]
    random.shuffle(options)

    captcha_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(option))] for option in options],
        resize_keyboard=True
    )

    new_message = await message.answer(question, reply_markup=captcha_keyboard)

    if user_id in last_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=last_messages[user_id])
        except Exception:
            pass

    last_messages[user_id] = new_message.message_id


@dp.message(lambda message: message.text.isdigit() or message.text.replace('.', '', 1).isdigit())
async def check_captcha_answer(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or "correct_answer" not in user_data[user_id]:
        return

    correct_answer = user_data[user_id].get("correct_answer")
    language = user_data[user_id].get("language", "Русский")

    try:
        user_answer = float(message.text)
    except ValueError:
        if language == "Русский":
            await message.answer("❌ Пожалуйста, выберите вариант из предложенных кнопок.")
        else:
            await message.answer("❌ Please select an option from the provided buttons.")
        return

    if user_answer == correct_answer:
        if language == "Русский":
            await message.answer("✅ Вы прошли проверку! Добро пожаловать!", reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer("✅ You have passed the verification! Welcome!", reply_markup=types.ReplyKeyboardRemove())

        user_data[user_id]["correct_answer"] = None

        await message.answer(
            "Выберите действие:" if language == "Русский" else "Choose an action:",
            reply_markup=main_menu(language)
        )
    else:
        if language == "Русский":
            await message.answer("❌ Неверный ответ. Попробуйте снова.")
        else:
            await message.answer("❌ Wrong answer. Please try again.")
        await send_captcha(message, message.message_id, language)



@dp.callback_query(lambda callback: callback.data == "banking_app")
async def banking_app_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data or "language" not in user_data[user_id]:
        await callback.message.answer("Ошибка: Вы не выбрали язык. Пожалуйста, начните сначала с команды /start." if "Русский" in user_data.get(user_id, {}).get("language", "Русский") else "Error: You have not selected a language. Please start again with the /start command.")
        return

    language = user_data[user_id]["language"]

    await callback.message.answer(
        "Выберите страну:" if language == "Русский" else "Select a country:",
        reply_markup=banking_app_menu(language)
    )


async def main():
    print("Бот запущен!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
