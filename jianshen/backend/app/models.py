from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    sex: Mapped[str] = mapped_column(String(16), default="unknown")
    age: Mapped[int] = mapped_column(Integer, default=25)
    height_cm: Mapped[float] = mapped_column(Float, default=170)
    weight_kg: Mapped[float] = mapped_column(Float, default=70)
    body_fat_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_level: Mapped[str] = mapped_column(String(32), default="medium")
    goal: Mapped[str] = mapped_column(String(16), default="maintain")
    calorie_target: Mapped[float] = mapped_column(Float, default=2200)
    protein_target: Mapped[float] = mapped_column(Float, default=140)
    carbs_target: Mapped[float] = mapped_column(Float, default=220)
    fat_target: Mapped[float] = mapped_column(Float, default=70)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LLMConfig(Base):
    __tablename__ = "llm_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    provider: Mapped[str] = mapped_column(String(32), default="openai_compatible")
    model: Mapped[str] = mapped_column(String(64), default="gpt-4o-mini")
    api_key: Mapped[str] = mapped_column(String(256), default="")
    base_url: Mapped[str] = mapped_column(String(256), default="https://api.openai.com/v1")
    parse_prompt: Mapped[str] = mapped_column(Text, default="请把饮食描述解析为食物数组并估算营养")
    advice_prompt: Mapped[str] = mapped_column(Text, default="根据摄入与目标给出饮食建议")
    enabled: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FoodEntry(Base):
    __tablename__ = "food_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(16), default="snack")
    original_text: Mapped[str] = mapped_column(Text)
    total_calories: Mapped[float] = mapped_column(Float, default=0)
    total_protein: Mapped[float] = mapped_column(Float, default=0)
    total_carbs: Mapped[float] = mapped_column(Float, default=0)
    total_fat: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items: Mapped[list[FoodItem]] = relationship("FoodItem", cascade="all, delete-orphan", back_populates="entry")


class FoodItem(Base):
    __tablename__ = "food_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("food_entry.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    grams: Mapped[float] = mapped_column(Float, default=100)
    calories: Mapped[float] = mapped_column(Float, default=0)
    protein: Mapped[float] = mapped_column(Float, default=0)
    carbs: Mapped[float] = mapped_column(Float, default=0)
    fat: Mapped[float] = mapped_column(Float, default=0)

    entry: Mapped[FoodEntry] = relationship("FoodEntry", back_populates="items")


class AdviceLog(Base):
    __tablename__ = "advice_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    advice: Mapped[str] = mapped_column(Text)
    context: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
