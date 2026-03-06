from __future__ import annotations

from typing import Iterable

from .schemas import FoodItemIn

ACTIVITY_FACTOR = {
    "sedentary": 1.2,
    "light": 1.375,
    "medium": 1.55,
    "heavy": 1.725,
    "athlete": 1.9,
}


FOOD_DB = {
    "鸡胸肉": (165, 31, 0, 3.6),
    "米饭": (116, 2.6, 25.9, 0.3),
    "鸡蛋": (144, 12.8, 1.7, 8.8),
    "牛奶": (54, 3.4, 5, 3),
    "香蕉": (93, 1.4, 22.8, 0.2),
    "燕麦": (389, 16.9, 66.3, 6.9),
    "牛肉": (250, 26, 0, 15),
    "三文鱼": (208, 20, 0, 13),
    "西兰花": (34, 2.8, 6.6, 0.4),
    "豆腐": (76, 8, 1.9, 4.8),
}


def calc_targets(age: int, sex: str, height_cm: float, weight_kg: float, activity_level: str, goal: str) -> dict[str, float]:
    if sex.lower() in {"male", "m", "男"}:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    tdee = bmr * ACTIVITY_FACTOR.get(activity_level, 1.55)

    if goal == "cut":
        calories = tdee - 400
        protein = weight_kg * 2.0
        fat = weight_kg * 0.8
    elif goal == "bulk":
        calories = tdee + 300
        protein = weight_kg * 1.8
        fat = weight_kg * 1.0
    else:
        calories = tdee
        protein = weight_kg * 1.6
        fat = weight_kg * 0.9

    carbs = max((calories - protein * 4 - fat * 9) / 4, 0)
    return {
        "calorie_target": round(calories, 1),
        "protein_target": round(protein, 1),
        "carbs_target": round(carbs, 1),
        "fat_target": round(fat, 1),
    }


def totals(items: Iterable[FoodItemIn]) -> dict[str, float]:
    cals = sum(x.calories for x in items)
    p = sum(x.protein for x in items)
    carbs = sum(x.carbs for x in items)
    fat = sum(x.fat for x in items)
    return {
        "total_calories": round(cals, 1),
        "total_protein": round(p, 1),
        "total_carbs": round(carbs, 1),
        "total_fat": round(fat, 1),
    }


def estimate_item(name: str, grams: float) -> FoodItemIn:
    base = FOOD_DB.get(name, (120, 6, 12, 4))
    ratio = grams / 100
    return FoodItemIn(
        name=name,
        grams=grams,
        calories=round(base[0] * ratio, 1),
        protein=round(base[1] * ratio, 1),
        carbs=round(base[2] * ratio, 1),
        fat=round(base[3] * ratio, 1),
    )
