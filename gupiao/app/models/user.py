from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=True)

    # 关系
    groups: Mapped[list["Group"]] = relationship(
        "Group", back_populates="user", cascade="all, delete-orphan"
    )
    stocks: Mapped[list["Stock"]] = relationship(
        "Stock", back_populates="user", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["AlertNotification"]] = relationship(
        "AlertNotification", back_populates="user", cascade="all, delete-orphan"
    )
