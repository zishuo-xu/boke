from __future__ import annotations

import json
import re
from datetime import date

import httpx
from sqlalchemy.orm import Session

from .models import LLMConfig
from .nutrition import estimate_item, totals
from .schemas import FoodItemIn, ParseRequest, ParseResult

MEAL_MAP = {
    "早餐": "breakfast",
    "午餐": "lunch",
    "晚餐": "dinner",
    "加餐": "snack",
}


async def parse_food_text(payload: ParseRequest, db: Session) -> ParseResult:
    meal_type = payload.meal_type or infer_meal_type(payload.text)
    cfg = db.get(LLMConfig, 1)
    if cfg and cfg.enabled and cfg.api_key:
        result = await call_llm_parse(payload, cfg)
        if result:
            return ParseResult(meal_type=meal_type, **result)

    items = fallback_parse(payload.text)
    data = totals(items)
    return ParseResult(meal_type=meal_type, items=items, **data)


def infer_meal_type(text: str) -> str:
    for zh, meal in MEAL_MAP.items():
        if zh in text:
            return meal
    return "snack"


def fallback_parse(text: str) -> list[FoodItemIn]:
    chunks = re.split(r"[，,、+\n]", text)
    items: list[FoodItemIn] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        grams = 100.0
        m = re.search(r"(\d+(?:\.\d+)?)\s*(g|克)", chunk)
        if m:
            grams = float(m.group(1))
            name = chunk[: m.start()].strip() or "自定义食物"
        else:
            name = re.sub(r"(早餐|午餐|晚餐|加餐|吃了|我吃了)", "", chunk).strip() or "自定义食物"
        items.append(estimate_item(name, grams))
    return items or [estimate_item("自定义食物", 100)]


async def call_llm_parse(payload: ParseRequest, cfg: LLMConfig) -> dict | None:
    prompt = (
        f"{cfg.parse_prompt}\n"
        "输出 JSON：{items:[{name,grams,calories,protein,carbs,fat}]}，不要额外文本。\n"
        f"用户输入: {payload.text}"
    )
    headers = {"Authorization": f"Bearer {cfg.api_key}"}
    body = {
        "model": cfg.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(f"{cfg.base_url.rstrip('/')}/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        raw_items = data.get("items", [])
        items = [FoodItemIn(**x) for x in raw_items]
        tt = totals(items)
        return {"items": items, **tt}
    except Exception:
        return None


async def build_day_advice(day_summary: dict, db: Session) -> str:
    cfg = db.get(LLMConfig, 1)
    gap_text = (
        f"热量差值: {round(day_summary['target_calories'] - day_summary['actual_calories'], 1)} kcal, "
        f"蛋白差值: {round(day_summary['target_protein'] - day_summary['actual_protein'], 1)} g"
    )

    if cfg and cfg.enabled and cfg.api_key:
        prompt = f"{cfg.advice_prompt}\n数据: {json.dumps(day_summary, ensure_ascii=False)}"
        headers = {"Authorization": f"Bearer {cfg.api_key}"}
        body = {
            "model": cfg.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.post(f"{cfg.base_url.rstrip('/')}/chat/completions", headers=headers, json=body)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

    if day_summary["actual_protein"] < day_summary["target_protein"]:
        return f"蛋白摄入偏低。{gap_text}。下一餐建议增加鸡胸肉/鸡蛋/豆腐。"
    if day_summary["actual_calories"] > day_summary["target_calories"]:
        return f"今日热量偏高。{gap_text}。下一餐建议减少主食，补充高纤蔬菜。"
    return f"整体摄入接近目标。{gap_text}。保持当前节奏并保证饮水。"
