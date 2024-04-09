import os
from datetime import datetime

from sqlalchemy import Boolean, DateTime
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import create_engine
from sqlalchemy.sql import expression

from dotenv import load_dotenv

load_dotenv()


class Base(DeclarativeBase):
    pass


class ChannelsForMessages(Base):
    __tablename__ = "channels"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    start: Mapped[bool] = mapped_column(Boolean(), server_default=expression.false())
    finish: Mapped[bool] = mapped_column(Boolean(), server_default=expression.false())
    finish_date: Mapped[datetime] = mapped_column(DateTime(), nullable=True)


def migrate():
    postgres_host = os.getenv('POSTGRES_HOST')
    postgres_port = os.getenv('POSTGRES_PORT')
    postgres_db = os.getenv('POSTGRES_DB')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_pass = os.getenv('POSTGRES_PASS')

    engine = create_engine(
        f"postgresql+psycopg2://{postgres_user}:{postgres_pass}@{postgres_host}:{postgres_port}/{postgres_db}",
        isolation_level="SERIALIZABLE"
    )

    Base.metadata.create_all(engine)


if __name__ == "__main__":
    migrate()
