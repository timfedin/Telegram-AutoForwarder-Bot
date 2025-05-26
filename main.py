
import asyncio
import re
import random
import logging
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename

# === НАСТРОЙКИ ===
api_id = 12345678  # Замените на ваш API ID
api_hash = 'cadcdasd12312eawcdawd21dsaca'  # Замените на ваш API Hash
session_name = 'session_name'
# Логирование
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Основные пересылы
main_channels = {
    -1000000000000: -2000000000000, 
    -3000000000000: -4000000000000,
}

# по ключевым словам 
keyword_channels = { 
    ("слово", "словечко", "слова"): -100000200000,
    ("азбука"): -1000000200000,
}

compiled_keywords = [
    (re.compile(rf'\b({"|".join(words)})\b', flags=re.IGNORECASE), channel)
    for words, channel in keyword_channels.items()
]

client = TelegramClient(session_name, api_id, api_hash)

# Для хранения групп сообщений (альбомов)
group_buffer = defaultdict(list)
group_timers = {}

def extract_text_and_filenames(messages):
    text_parts = []
    filenames = []

    for msg in messages:
        if msg.message:
            text_parts.append(msg.message)

        if msg.media and isinstance(msg.media, MessageMediaDocument):
            for attr in msg.media.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    filenames.append(attr.file_name)

    return " ".join(text_parts + filenames)

async def process_and_forward(messages, source_id):
    dest_id = main_channels.get(source_id)
    if not dest_id:
        return

    # Основной пересыл
    try:
        await client.forward_messages(dest_id, messages)
        logging.info(f"📦 Основной пересыл: {source_id} → {dest_id}")
    except Exception as e:
        logging.error(f"❌ Ошибка в основной пересылке ({dest_id}): {e}")

    # Фильтрация по ключам
    content = extract_text_and_filenames(messages)
    found_channels = set()

    for regex, channel_id in compiled_keywords:
        if regex.search(content):
            if channel_id not in found_channels:
                try:
                    await client.forward_messages(channel_id, messages)
                    logging.info(f"🔑 Найден ключ {regex.pattern} → в {channel_id}")
                    found_channels.add(channel_id)
                except Exception as e:
                    logging.error(f"❌ Ошибка пересылки в ключевой канал ({channel_id}): {e}")

    await asyncio.sleep(random.uniform(3, 5))

async def flush_album(grouped_id, source_id):
    messages = group_buffer.pop(grouped_id, [])
    group_timers.pop(grouped_id, None)
    if messages:
        await process_and_forward(messages, source_id)

@client.on(events.NewMessage(chats=list(main_channels.keys())))
async def message_handler(event):
    msg = event.message
    grouped_id = getattr(msg, 'grouped_id', None)
    source_id = event.chat_id

    if grouped_id:
        group_buffer[grouped_id].append(msg)

        # Обновляем/создаём таймер на 1.5 сек — после прихода последнего сообщения в альбоме
        if group_timers.get(grouped_id):
            group_timers[grouped_id].cancel()

        group_timers[grouped_id] = asyncio.get_event_loop().call_later(
            1.5, lambda: asyncio.create_task(flush_album(grouped_id, source_id))
        )
    else:
        await process_and_forward([msg], source_id)

async def main():
    await client.start()
    logging.info("✅ Скрипт запущен и ждёт сообщения...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
