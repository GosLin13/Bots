import swisseph as swe
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from datetime import datetime

BOT_TOKEN = ""
OPENWEATHER_API_KEY = ""
GEOCODING_API_URL = ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}

zodiac_signs = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

planet_meanings = {
    "Солнце": "Солнце определяет вашу личность, жизненную энергию и основные качества.",
    "Луна": "Луна символизирует ваши эмоции, внутренний мир и подсознание.",
    "Меркурий": "Меркурий отвечает за ваше мышление, общение и логику.",
    "Венера": "Венера представляет ваши чувства, любовь и эстетику.",
    "Марс": "Марс символизирует вашу энергию, силу и активность.",
    "Юпитер": "Юпитер связан с расширением, мудростью и успехом.",
    "Сатурн": "Сатурн отвечает за дисциплину, ответственность и ограничения."
}

def get_zodiac_sign(degrees):
    index = int(degrees // 30)
    return zodiac_signs[index]

def calculate_planet_positions(birth_date, birth_time, city_coords):
    jd = swe.julday(birth_date.year, birth_date.month, birth_date.day, birth_time.hour + birth_time.minute / 60.0)
    planets = ["Солнце", "Луна", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн"]
    positions = {}

    for planet_id, planet_name in zip(range(swe.SUN, swe.SATURN + 1), planets):
        position = swe.calc_ut(jd, planet_id)
        degrees = position[0][0] if isinstance(position[0], tuple) else position[0]
        positions[planet_name] = degrees

    return positions

async def get_coordinates(city_name):
    params = {
        "q": city_name,
        "limit": 1,
        "appid": OPENWEATHER_API_KEY
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GEOCODING_API_URL, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result:
                        lat = result[0]["lat"]
                        lon = result[0]["lon"]
                        return lat, lon
                    else:
                        return None
                else:
                    return None
    except Exception as e:
        print(f"Ошибка получения координат: {e}")
        return None

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "day", "birth_data": {}}
    await message.answer(
        "Добро пожаловать в мир астрологии! ✨\nВведите день вашего рождения (например: 01):"
    )

@dp.message()
async def process_input(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        await message.answer("Введите /start, чтобы начать.")
        return

    step = user_data[user_id]["step"]

    if step == "day":
        if not message.text.isdigit() or not (1 <= int(message.text) <= 31):
            await message.answer("Пожалуйста, введите корректный день (например: 01).")
            return
        user_data[user_id]["birth_data"]["day"] = int(message.text)
        user_data[user_id]["step"] = "month"
        await message.answer("Введите месяц вашего рождения (например: 01 или январь):")

    elif step == "month":
        try:
            if message.text.isdigit():
                month = int(message.text)
                if not (1 <= month <= 12):
                    raise ValueError
            else:
                month = datetime.strptime(message.text.lower(), "%B").month
            user_data[user_id]["birth_data"]["month"] = month
            user_data[user_id]["step"] = "year"
            await message.answer("Введите год вашего рождения (например: 2000):")
        except ValueError:
            await message.answer("Пожалуйста, введите корректный месяц (например: 01 или январь).")

    elif step == "year":
        if not message.text.isdigit() or not (1900 <= int(message.text) <= datetime.now().year):
            await message.answer("Пожалуйста, введите корректный год (например: 2000).")
            return
        user_data[user_id]["birth_data"]["year"] = int(message.text)
        user_data[user_id]["step"] = "time"
        await message.answer("Введите время вашего рождения (например: 23:15):")

    elif step == "time":
        try:
            birth_time = datetime.strptime(message.text, "%H:%M").time()
            user_data[user_id]["birth_data"]["time"] = birth_time
            user_data[user_id]["step"] = "city"
            await message.answer("Введите город вашего рождения (например: Москва):")
        except ValueError:
            await message.answer("Пожалуйста, введите корректное время (например: 23:15).")

    elif step == "city":
        city = message.text.strip()
        user_data[user_id]["birth_data"]["city"] = city

        coordinates = await get_coordinates(city)
        if not coordinates:
            await message.answer("Не удалось найти координаты для указанного города. Убедитесь, что название указано правильно.")
            return

        birth_data = user_data[user_id]["birth_data"]
        birth_date = datetime(birth_data["year"], birth_data["month"], birth_data["day"])
        birth_time = birth_data["time"]

        planet_positions = calculate_planet_positions(birth_date, birth_time, coordinates)
        response = f"Спасибо! Вот ваша натальная карта для {city} (координаты: {coordinates[0]:.2f}, {coordinates[1]:.2f}):\n"

        for planet, degrees in planet_positions.items():
            zodiac = get_zodiac_sign(degrees)
            interpretation = planet_meanings.get(planet, "Нет данных.")
            response += f"\n{planet} в знаке {zodiac} ({degrees:.2f}°):\n{interpretation}\n"

        await message.answer(response)

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
