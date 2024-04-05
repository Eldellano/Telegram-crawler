import asyncio
import os

from aiotdlib import Client
from dotenv import load_dotenv

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

        cnt_messages = 0

        all_messages = list()
        all_messages.append(last_message_item)

        while True:
            messages_history = await client.api.get_chat_history(chat_id=channel_id, from_message_id=last_message_id,
                                                                 limit=100, offset=0, request_timeout=60)
            print(f'{last_message_id=}')
            # print(f'{messages_history=}')

            if messages := messages_history.messages:
                for message_in_chat in messages:
                    # print(f'{message_in_chat=}')

                    all_messages.append(message_in_chat)
                    last_message_id = message_in_chat.id
                    cnt_messages += 1
            else:
                break

        print(f'{cnt_messages=}')
        print(f'{len(all_messages)=}')
        print(f'{all_messages=}')


if __name__ == '__main__':
    channel_name = 'mudak'
    # channel_name = 'eldellano_channel_test'
    # asyncio.run(get_channel_info(channel_name))
    asyncio.run(get_messages(channel_name))
