import discord
from discord.ext import commands
from discord import app_commands
import time
import json
import os
import math

# Токен бота
TOKEN = "YOUR_TOKEN_HERE"
CHANNEL_ID = YOUR_CHANNEL_ID  # ID канала для вывода сообщения

# Инициализация бота с намерениями
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Путь к файлу для сохранения данных
DATA_FILE = "user_data.json"

# Словарь для хранения данных о пользователях
user_data = {}

# Уровни и их требования
LEVELS = {
    1: {"messages": 5, "voice_time": 10},
    2: {"messages": 10, "voice_time": 30},
    3: {"messages": 20, "voice_time": 60},
    10: {"messages": 50, "voice_time": 600},
}

# Загрузка данных из файла
def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            user_data = {int(key): value for key, value in raw_data.items()}
    else:
        user_data = {}

# Сохранение данных в файл
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump({str(key): value for key, value in user_data.items()}, file, ensure_ascii=False, indent=4)

# Расчет уровня пользователя
def calculate_level(user_id):
    user_stats = user_data.get(user_id, {"messages": 0, "voice_time": 0})
    messages = user_stats.get("messages", 0)
    voice_time = user_stats.get("voice_time", 0)

    current_level = 0
    for level, reqs in sorted(LEVELS.items()):
        if messages >= reqs["messages"] and voice_time >= reqs["voice_time"]:
            current_level = level
        else:
            break

    return current_level

# Функция расчета прогресса для метрики
def calculate_metric_progress(current, required):
    return min(current / required, 1.0)  # Ограничиваем максимум 100%

# Событие: обработка сообщений
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id

    if user_id not in user_data:
        user_data[user_id] = {"messages": 0, "voice_time": 0, "last_voice_time": None}

    user_data[user_id]["messages"] += 1
    save_data()

    await bot.process_commands(message)

# Событие: обновление голосового состояния
@bot.event
async def on_voice_state_update(member, before, after):
    user_id = member.id

    if user_id not in user_data:
        user_data[user_id] = {"messages": 0, "voice_time": 0, "last_voice_time": None}

    if before.channel is None and after.channel is not None:
        user_data[user_id]["last_voice_time"] = time.time()
    elif before.channel is not None and after.channel is None:
        if user_data[user_id]["last_voice_time"]:
            time_spent = time.time() - user_data[user_id]["last_voice_time"]
            user_data[user_id]["voice_time"] += time_spent / 60  # Храним в минутах
            user_data[user_id]["last_voice_time"] = None
    save_data()

# Команда: уровень пользователя
@bot.tree.command(name="level", description="Узнать уровень пользователя на сервере")
async def level(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    user_id = user.id

    if user_id not in user_data:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Данные не найдены",
                description=f"К сожалению, у нас нет данных о пользователе {user.mention}. 😢",
                color=discord.Color.red(),
            )
        )
        return

    # Получаем текущий уровень и требования для следующего уровня
    level = calculate_level(user_id)
    messages = user_data[user_id].get("messages", 0)
    voice_time = user_data[user_id].get("voice_time", 0)

    next_level = level + 1
    if next_level not in LEVELS:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Максимальный уровень достигнут",
                description=f"Вы достигли максимального уровня! 🎉",
                color=discord.Color.gold(),
            )
        )
        return

    # Требования для следующего уровня
    req_messages = LEVELS[next_level]["messages"]
    req_voice_time = LEVELS[next_level]["voice_time"]

    # Рассчитываем прогресс по сообщениям и голосовому времени
    message_progress = calculate_metric_progress(messages, req_messages)
    voice_time_progress = calculate_metric_progress(voice_time, req_voice_time)

    # Общий прогресс
    total_progress = (message_progress + voice_time_progress) / 2

    # Остаток до следующего уровня
    xp_remaining_messages = max(0, req_messages - messages)
    xp_remaining_voice = max(0, req_voice_time - voice_time)

    # Создаем прогресс-бар
    bar_length = 20  # Длина прогресс-бара
    filled_length = math.floor(bar_length * total_progress)
    progress_bar = "█" * filled_length + "-" * (bar_length - filled_length)

    # Гифка для уровня
    gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWR5MXVmeXIwZHE4aGtueTRkaXI0aTkyYzZ6M3pqa25sbzczYWFqaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/MDJ9IbxxvDUQM/giphy.gif"

    # Выбор цвета для эмбеда
    embed_color = (
        discord.Color.green() if level < 3 else
        discord.Color.orange() if level < 10 else
        discord.Color.purple()
    )

    # Создаем Embed
    embed = discord.Embed(
        title=f"🎉 Уровень пользователя {user.name} 🎉",
        description=(
            f"📈 **Уровень**: **{level}**\n"
            f"💬 **Сообщений отправлено**: **{messages}/{req_messages}**\n"
            f"🎙️ **Время в голосовых каналах**: **{voice_time:.2f}/{req_voice_time} минут**\n"
            f"\n"
            f"Прогресс до следующего уровня: \n"
            f"[{progress_bar}] {total_progress * 100:.2f}%\n\n"
            f"Осталось:\n"
            f" - **{xp_remaining_messages} сообщений**\n"
            f" - **{xp_remaining_voice:.2f} минут**\n\n"
            f"Продолжай в том же духе! 🚀"
        ),
        color=embed_color,
    )
    embed.set_thumbnail(url=user.display_avatar.url)  # Установка аватара
    embed.set_image(url=gif_url)  # Установка гифки
    embed.set_footer(
        text="Статистика обновляется автоматически ✨",
        icon_url="https://i.giphy.com/media/xTiTnxpQ3ghPiB2Hp6/giphy.gif",
    )

    await interaction.response.send_message(embed=embed)

# Событие: бот готов
@bot.event
async def on_ready():
    load_data()
    try:
        await bot.tree.sync()
        print("Команды синхронизированы.")
        print("Зарегистрированные команды:")
        for command in bot.tree.get_commands():
            print(f"- {command.name}: {command.description}")
    except Exception as e:
        print(f"Ошибка синхронизации команд: {e}")
    print(f"Бот {bot.user} успешно запущен!")

# Запуск бота
bot.run(TOKEN)
