from sqlmodel import Field, SQLModel
from typing import Literal
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Text, Column
import pytz

from deepsleep.database.models.base import SQLModelSerializable


# 每条消息
class HistoryTable(SQLModelSerializable, table=True):
    __tablename__ = "history"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    content: str = Field(sa_column=Column(Text))
    dialog_id: str
    role: str = Literal["assistant", "system", "user"]
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))

