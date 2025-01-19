from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, String, Date
from datetime import datetime, date
import hashlib
from typing import List

class Base(DeclarativeBase):
    pass

class User(Base, UserMixin):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(String(36))
    email: Mapped[str] = mapped_column(String(36))
    password: Mapped[str] = mapped_column(String(150))

    created_on: Mapped[datetime] = mapped_column(server_default=func.now())
    last_login: Mapped[datetime] = mapped_column(server_default=func.now())


    # --- Profile Information ---
    state: Mapped[str] = mapped_column(String(2), nullable=True)
    city: Mapped[str] = mapped_column(String(64), nullable=True)

    burns: Mapped[List['Burn']] = relationship()

    def avatar(self, size):
        email_encoded = self.email.lower().encode('utf-8')
        email_hash = hashlib.sha256(email_encoded).hexdigest()
        default = 'robohash'
        return f'https://www.gravatar.com/avatar/{email_hash}?d={default}&s={size}'

    def as_dict(self):
        return {
            'username': self.username,
            'profile_url': self.avatar(64),
            'last_login': self.last_login,
            'created_on': self.created_on,
        }

    def check_pass(self, password: str):
        return check_password_hash(self.password, password)

    @staticmethod
    def hash_pass(password: str):
        return generate_password_hash(password, method='pbkdf2')



class Burn(Base):
    __tablename__ = 'burns'
    id: Mapped[int] = mapped_column(primary_key=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    location: Mapped[str] = mapped_column(String(100), nullable=True)
    time: Mapped[date] = mapped_column()
    prop: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(String(280), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location': self.location,
            'time': self.time,
            'prop': self.prop,
            'notes': self.notes,
        }
    
class PasswordReset(Base):
    __tablename__ = 'links'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    requested: Mapped[datetime] = mapped_column(server_default=func.now())
    reset_code: Mapped[str] = mapped_column(String(100))

