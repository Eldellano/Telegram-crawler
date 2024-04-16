import asyncio
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


def save_messages(channel_name, messages: list):
    """Ротация по полученным сообщениям, подготовка к сохранению"""

    print(f'Сохранение сообщений - {channel_name}')
    result_db = ResultDataBase()

    for message in messages:
        post = message["post"]
        comments = message["comments"]
        tag = f'{channel_name}'

        try:
            # пост только из текста
            message_text = post.content.text.text
        except AttributeError:
            try:
                # медиа пост + текстовое описание
                message_text = post.content.caption.text
            except AttributeError:
                message_text = None

        json_message = json.dumps(post.dict())
        base64_message = base64.b64encode(json_message.encode()).decode('utf-8')

        # сохранение результатов
        source_id = 2
        saved_message_id = result_db.save_result_post(message_text, base64_message, source_id, tag)

        if comments:
            comments_for_save = list()

            for comment in comments:
                try:
                    comment_text = comment.content.text.text
                except AttributeError:
                    continue

                json_comment = json.dumps(comment.dict())
                base64_comment = base64.b64encode(json_comment.encode()).decode('utf-8')

                comments_for_save.append((saved_message_id, comment_text, base64_comment))

            result_db.save_result_comment(comments_for_save)


async def get_messages(channel_name: str):
    """Получение и сохранение сообщений из канала/группы"""

    client = Tg().get_client()

    async with client:
        try:
            chat = await client.api.search_public_chat(channel_name)  # получение id и прочей инфы о чате/канале

            channel_id = chat.id
            last_message_id = chat.last_message.id
            last_message_item = chat.last_message

            all_messages = list()
            all_messages.append(last_message_item)
            message_with_comments = list()

            while True:
                print(f'{len(all_messages)=}')
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

                    for message_in_chat in all_messages:
                        # получение комментариев к посту

                        all_post_comments = list()
                        if message_in_chat.can_get_message_thread is True:
                            # print(f'Получение комментариев - {channel_name} - {last_message_id=}')
                            last_comment_id = 0

                            while True:
                                print(
                                    f'Получение комментариев - {channel_name} - {message_in_chat.id=} - {last_comment_id=}')
                                try:
                                    comments_history = await client.api.get_message_thread_history(
                                        chat_id=chat.id,
                                        message_id=message_in_chat.id,
                                        from_message_id=last_comment_id,
                                        limit=100, offset=0,
                                        request_timeout=30)

                                    if comments_history:
                                        for reply_comment in comments_history.messages:
                                            all_post_comments.append(reply_comment)
                                            last_comment_id = reply_comment.id
                                except api.errors.error.AioTDLibError as comment_error:
                                    if comment_error.message == 'Receive messages in an unexpected chat':
                                        print(f'{len(all_post_comments)=} - {comment_error=}')
                                        break
                                except asyncio.exceptions.TimeoutError:
                                    print(f'get_chat_history - TimeoutError')
                                    continue
                                finally:
                                    pass

                        all_post_comments.reverse()
                        to_save = {'post': message_in_chat,
                                   'comments': all_post_comments}

                        message_with_comments.append(to_save)
                        last_message_id = message_in_chat.id

                    if message_with_comments:
                        save_messages(channel_name, message_with_comments)
                        message_with_comments.clear()

                    all_messages.clear()

                else:
                    break

            return True

        except api.errors.error.BadRequest as channel_error:
            print(f'{channel_error.message=}')
            return False
        finally:
            pass


async def rotate():
    db = DataBase()

    count_row = db.count_channels()
    if count_row == 0:
        print('Нет телеграм каналов для обработки')

    for item in range(count_row):
        channel_data = db.get_one_channel()
        print(f'{channel_data=}')

        if channel_data:
            channel_id = channel_data[0]
            channel_name = channel_data[1]

            # установка статуса начала
            db.set_channel_start(channel_id)

            # получение сообщений
            await get_messages(channel_name)

            # установка статуса завершения
            db.set_channel_finish(channel_id)


if __name__ == '__main__':
    name = 'mudak'
    # channel_name = 'eldellano_channel_test'
    # asyncio.run(get_channel_info(name))
    # asyncio.run(get_messages(name))
    asyncio.run(rotate())
