import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

# Токен вашего бота (вставьте в кавычки или настроите через переменные)
TOKEN = "ВАШ_ТОКЕН_БОТА"

dp = Dispatcher()

# Хранилище мутов: {user_id: timestamp_окончания_мута}
muted_users = {}

def parse_time(time_str: str) -> int:
    """Конвертирует время вроде 10 (минут), 30s, 5m, 2h в секунды"""
    match = re.match(r"^(\d+)([smh]?)$", time_str.lower())
    if not match:
        return 0
    val, unit = match.groups()
    val = int(val)
    if unit == 's':  # секунды
        return val
    elif unit == 'h':  # часы
        return val * 3600
    else:  # по умолчанию или 'm' — минуты
        return val * 60

@dp.message(F.text.startswith(".mute"))
async def cmd_mute(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответьте (Reply) командой .mute на сообщение нарушителя в группе!")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("Укажите время! Пример: `.mute 10` (10 минут) или `.mute 30s`", parse_mode="Markdown")
        return

    seconds = parse_time(args[1])
    if seconds <= 0:
        await message.reply("Некорректное время! Используйте: `10s`, `5m`, `1h`", parse_mode="Markdown")
        return

    target_user = message.reply_to_message.from_user
    loop = asyncio.get_running_loop()
    muted_users[target_user.id] = loop.time() + seconds

    try:
        await message.delete()
    except Exception:
        pass

    notif = await message.answer(f"🤫 Пользователь {target_user.full_name} замучен на {args[1]}. Его сообщения будут удаляться.")
    await asyncio.sleep(5)
    try:
        await notif.delete()
    except Exception:
        pass

@dp.message()
async def check_muted_messages(message: Message, bot: Bot):
    user_id = message.from_user.id
    if user_id in muted_users:
        loop = asyncio.get_running_loop()
        if loop.time() < muted_users[user_id]:
            try:
                await message.delete()
            except Exception as e:
                print(f"Не удалось удалить сообщение: {e}")
        else:
            del muted_users[user_id]

async def main():
    bot = Bot(token=TOKEN)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
