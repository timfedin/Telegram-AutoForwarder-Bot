from telethon.sync import TelegramClient, events
from telethon.tl.types import PeerChannel
import asyncio

# Настройки API Telegram (получить на my.telegram.org)
API_ID = 1234567  # Замените на ваш API_ID
API_HASH = 'ваш_api_hash'  # Замените на ваш API_HASH

# Сессионный файл (для авторизации)
SESSION_NAME = 'session_name'

# Настройки каналов (формат: { "ID_исходного_канала": "ID_основного_канала" })
SOURCE_TO_TARGET = {
    -1001234567890: -1001111111111,  # Из канала A → в канал X
    -1009876543210: -1002222222222,   # Из канала B → в канал Y
}

# Каналы для ключевых слов (формат: { "ключевое_слово": (ID_канала, [ID_исходных_каналов]) })
KEYWORD_CHANNELS = {
    "срочно": (-1003333333333, []),       # Для всех каналов
    "важно": (-1004444444444, []),        # Для всех каналов
    "крипто": (-1005555555555, [-1001234567890]),  # Только для канала A
    "игры": (-1006666666666, [-1009876543210]),    # Только для канала B
}

# Задержка перед пересылкой (в секундах)
DELAY_BEFORE_FORWARD = 5  # 5 секунд

# Создаем клиент Telegram
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage)
async def handler(event):
    message = event.message
    message_text = message.text.lower() if message.text else ""
    chat_id = event.chat_id

    # Проверяем, что сообщение из нужного нам канала
    if chat_id in SOURCE_TO_TARGET:
        # Добавляем задержку перед пересылкой
        await asyncio.sleep(DELAY_BEFORE_FORWARD)

        # Пересылаем в основной канал
        target_channel = SOURCE_TO_TARGET[chat_id]
        await client.send_message(target_channel, message)

        # Проверяем ключевые слова
        for keyword, (channel_id, source_channels) in KEYWORD_CHANNELS.items():
            # Если ключевое слово найдено и (канал не указан или сообщение из нужного канала)
            if keyword in message_text and (not source_channels or chat_id in source_channels):
                await client.send_message(channel_id, message)

async def main():
    await client.start()
    print("Бот запущен и слушает каналы...")
    print("Исходные каналы:", SOURCE_TO_TARGET.keys())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())