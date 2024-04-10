import asyncio
import datetime
import json
import os
import base64

from aiotdlib import Client, api
from dotenv import load_dotenv

from db_works import DataBase, ResultDataBase

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")


class Tg:
    def __init__(self):
        self.client = Client(api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER)

    def get_client(self):
        return self.client


async def get_channel_info(channel_name: str) -> dict:
    """Получение общей информации о канале/группе"""

    client = Tg().get_client()
    async with client:
        chat = await client.api.search_public_chat(channel_name)  # получение id и прочей инфы о чате/канале

        chat_data = {
            'channel_id': chat.id,
            'title': chat.title,
            'photo': chat.photo,
            'last_message': chat.last_message
        }

        return chat_data


async def get_messages(channel_name: str):
    """Получение сообщений из канала/группы"""

    client = Tg().get_client()

    async with client:
        try:
            chat = await client.api.search_public_chat(channel_name)  # получение id и прочей инфы о чате/канале

            # chat_data = {
            #     'channel_id': chat.id,
            #     'title': chat.title,
            #     'photo': chat.photo,
            #     'last_message': chat.last_message
            # }

            channel_id = chat.id
            last_message_id = chat.last_message.id
            last_message_item = chat.last_message

            all_messages = list()
            all_messages.append(last_message_item)

            while True:
                print(f'Получение сообщений - {channel_name} - {last_message_id=}')
                try:
                    messages_history = await client.api.get_chat_history(chat_id=channel_id,
                                                                         from_message_id=last_message_id,
                                                                         limit=100, offset=0, request_timeout=60)
                except asyncio.exceptions.TimeoutError:
                    print(f'get_chat_history - TimeoutError')
                    continue

                if messages := messages_history.messages:
                    for message_in_chat in messages:
                        all_messages.append(message_in_chat)
                        last_message_id = message_in_chat.id


                else:
                    break

            return all_messages

        except api.errors.error.BadRequest as channel_error:
            print(f'{channel_error.message=}')
            return None


async def rotate():
    db = DataBase()
    result_db = ResultDataBase()

    count_row = db.count_channels()
    if count_row == 0:
        print('Нет телеграм каналов для обработки')

    for item in range(count_row):
        channel_data = db.get_one_channel()
        print(f'{channel_data=}')

        if channel_data:
            channel_id = channel_data[0]
            channel_name = channel_data[1]

            db.set_channel_start(channel_id)
            if result := await get_messages(channel_name):
                for message in result:
                    print(f'Сохранение сообщений - {channel_name}')

                    try:
                        message_text = message.content.text.text
                    except AttributeError:
                        message_text = None

                    json_message = json.dumps(message.dict())
                    base64_message = base64.b64encode(json_message.encode()).decode('utf-8')

                    # today = datetime.datetime.today().strftime('%d.%m.%Y')
                    # tag = f'tg_{channel_name}_{today}'

                    # сохранение результатов
                    source_id = 2
                    result_db.save_result(message_text, base64_message, source_id)

            # установка статуса завершения
            db.set_channel_finish(channel_id)


if __name__ == '__main__':
    channel_name = 'mudak'
    # channel_name = 'eldellano_channel_test'
    # asyncio.run(get_channel_info(channel_name))
    # asyncio.run(get_messages(channel_name))
    asyncio.run(rotate())
