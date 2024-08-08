from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, String
import datetime

class Base(DeclarativeBase):
    pass

class User(Base, UserMixin):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(36))
    email: Mapped[str] = mapped_column(String(36))
    password: Mapped[str] = mapped_column(String(150))

    created_on: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    last_login: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    def check_pass(self, password: str):
        return check_password_hash(self.password, password)

    @staticmethod
    def hash_pass(password: str):
        return generate_password_hash(password, method='pbkdf2')

class Invited(Base):
    __tablename__ = 'invited'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(36))

db = SQLAlchemy(model_class=Base)
