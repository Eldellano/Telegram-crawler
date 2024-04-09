import datetime
import os

import psycopg2
from sqlalchemy import create_engine, select, update, func
from models import ChannelsForMessages


class DataBase:
    def __init__(self):
        self.postgres_host = os.getenv('POSTGRES_HOST')
        self.postgres_port = os.getenv('POSTGRES_PORT')
        self.postgres_db = os.getenv('POSTGRES_DB')
        self.postgres_user = os.getenv('POSTGRES_USER')
        self.postgres_pass = os.getenv('POSTGRES_PASS')

        self.engine = create_engine(
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_pass}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}",
            isolation_level="AUTOCOMMIT",
            pool_pre_ping=True,
        )

    def get_one_channel(self):
        """
        Получение одного url из таблицы url_from_files
        """

        query = (select(ChannelsForMessages).where(ChannelsForMessages.finish == False)
                 .order_by(ChannelsForMessages.id).limit(1))

        with self.engine.connect() as conn:
            result = conn.execute(query).fetchone()

            return result

    def set_channel_start(self, channel_id: int):
        """Устанавливаем start=True для начатых каналов"""

        query = update(ChannelsForMessages).where(ChannelsForMessages.id == channel_id).values(start=True)

        with self.engine.connect() as conn:
            conn.execute(query)
            # conn.commit()

    def set_channel_finish(self, channel_id: int):
        """Устанавливаем finish=True и дату для начатых каналов"""

        date = datetime.datetime.now()
        query = (update(ChannelsForMessages).where(ChannelsForMessages.id == channel_id)
                 .values(finish=True, finish_date=date))

        with self.engine.connect() as conn:
            conn.execute(query)

    def count_channels(self):
        """Получение количества не обработанных записей в таблице ChannelsForMessages"""

        query = select(func.count(ChannelsForMessages.id).filter(ChannelsForMessages.finish == False))

        with self.engine.connect() as conn:
            result = conn.execute(query)
        return result.fetchone()[0]


def save_result(message, tags):
    result_postgres_host = os.getenv('RESULT_POSTGRES_HOST')
    result_postgres_port = os.getenv('RESULT_POSTGRES_PORT')
    result_postgres_db = os.getenv('RESULT_POSTGRES_DB')
    result_postgres_user = os.getenv('RESULT_POSTGRES_USER')
    result_postgres_pass = os.getenv('RESULT_POSTGRES_PASS')

    conn = psycopg2.connect(host=result_postgres_host,
                            port=result_postgres_port,
                            # sslmode='verify-full',
                            dbname=result_postgres_db,
                            user=result_postgres_user,
                            password=result_postgres_pass,
                            target_session_attrs='read-write'
                            )

    # conn.close()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO data (base64_data, tags) VALUES (%s, %s)', (message, tags))


if __name__ == '__main__':
    db = DataBase()

    channel_id = 1
    # print(db.get_one_channel())
    # db.set_channel_start(channel_id)
    # db.set_channel_finish(channel_id)
    # print(db.count_channels())
