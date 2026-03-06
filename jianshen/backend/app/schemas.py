from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


MealType = Literal["breakfast", "lunch", "dinner", "snack"]
GoalType = Literal["cut", "bulk", "maintain"]
ActivityType = Literal["sedentary", "light", "medium", "heavy", "athlete"]


class ProfileIn(BaseModel):
    sex: str = "unknown"
    age: int = Field(ge=10, le=120)
    height_cm: float = Field(gt=50, lt=260)
    weight_kg: float = Field(gt=20, lt=500)
    body_fat_rate: float | None = Field(default=None, ge=1, le=70)
    activity_level: ActivityType = "medium"
    goal: GoalType = "maintain"
    calorie_target: float | None = None
    protein_target: float | None = None
    carbs_target: float | None = None
    fat_target: float | None = None


class ProfileOut(ProfileIn):
    id: int
    updated_at: datetime


class LLMConfigIn(BaseModel):
    provider: str = "openai_compatible"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    parse_prompt: str
    advice_prompt: str
    enabled: bool = False


class LLMConfigOut(LLMConfigIn):
    id: int
    updated_at: datetime


class FoodItemIn(BaseModel):
    name: str
    grams: float = Field(gt=0)
    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)


class FoodItemOut(FoodItemIn):
    id: int


class ParseRequest(BaseModel):
    text: str = Field(min_length=1)
    meal_type: MealType | None = None
    entry_date: date | None = None


class ParseResult(BaseModel):
    meal_type: MealType
    items: list[FoodItemIn]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float


class EntryCreate(BaseModel):
    text: str
    meal_type: MealType
    entry_date: date
    items: list[FoodItemIn]


class EntryUpdate(BaseModel):
    meal_type: MealType
    entry_date: date
    text: str
    items: list[FoodItemIn]


class EntryOut(BaseModel):
    id: int
    entry_date: date
    meal_type: MealType
    original_text: str
    items: list[FoodItemOut]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    created_at: datetime
    updated_at: datetime


class DaySummary(BaseModel):
    date: date
    target_calories: float
    target_protein: float
    target_carbs: float
    target_fat: float
    actual_calories: float
    actual_protein: float
    actual_carbs: float
    actual_fat: float
    by_meal: dict[str, dict[str, float]]
    entries: list[EntryOut]
    advice: str
