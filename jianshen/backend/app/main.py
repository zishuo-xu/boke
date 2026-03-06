from __future__ import annotations

from datetime import date
from pathlib import Path
import csv
import io

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .database import Base, engine, get_db, DB_PATH
from .llm import build_day_advice, parse_food_text
from .models import AdviceLog, FoodEntry, FoodItem, LLMConfig, UserProfile
from .nutrition import calc_targets, totals
from .schemas import (
    DaySummary,
    EntryCreate,
    EntryOut,
    EntryUpdate,
    FoodItemOut,
    LLMConfigIn,
    LLMConfigOut,
    ParseRequest,
    ParseResult,
    ProfileIn,
    ProfileOut,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fitness Tracker API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_defaults(db: Session) -> None:
    if not db.get(UserProfile, 1):
        targets = calc_targets(25, "male", 175, 70, "medium", "maintain")
        db.add(UserProfile(id=1, sex="male", age=25, height_cm=175, weight_kg=70, activity_level="medium", goal="maintain", **targets))
    if not db.get(LLMConfig, 1):
        db.add(LLMConfig(id=1))
    db.commit()


def to_entry_out(entry: FoodEntry) -> EntryOut:
    return EntryOut(
        id=entry.id,
        entry_date=entry.entry_date,
        meal_type=entry.meal_type,
        original_text=entry.original_text,
        items=[
            FoodItemOut(
                id=i.id,
                name=i.name,
                grams=i.grams,
                calories=i.calories,
                protein=i.protein,
                carbs=i.carbs,
                fat=i.fat,
            )
            for i in entry.items
        ],
        total_calories=entry.total_calories,
        total_protein=entry.total_protein,
        total_carbs=entry.total_carbs,
        total_fat=entry.total_fat,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@app.get("/health")
def health(db: Session = Depends(get_db)):
    ensure_defaults(db)
    return {"ok": True}


@app.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    ensure_defaults(db)
    return db.get(UserProfile, 1)


@app.put("/profile", response_model=ProfileOut)
def update_profile(payload: ProfileIn, db: Session = Depends(get_db)):
    ensure_defaults(db)
    profile = db.get(UserProfile, 1)
    auto_targets = calc_targets(payload.age, payload.sex, payload.height_cm, payload.weight_kg, payload.activity_level, payload.goal)
    profile.sex = payload.sex
    profile.age = payload.age
    profile.height_cm = payload.height_cm
    profile.weight_kg = payload.weight_kg
    profile.body_fat_rate = payload.body_fat_rate
    profile.activity_level = payload.activity_level
    profile.goal = payload.goal
    profile.calorie_target = payload.calorie_target or auto_targets["calorie_target"]
    profile.protein_target = payload.protein_target or auto_targets["protein_target"]
    profile.carbs_target = payload.carbs_target or auto_targets["carbs_target"]
    profile.fat_target = payload.fat_target or auto_targets["fat_target"]
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/llm-config", response_model=LLMConfigOut)
def get_llm_config(db: Session = Depends(get_db)):
    ensure_defaults(db)
    cfg = db.get(LLMConfig, 1)
    return LLMConfigOut(
        id=cfg.id,
        provider=cfg.provider,
        model=cfg.model,
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        parse_prompt=cfg.parse_prompt,
        advice_prompt=cfg.advice_prompt,
        enabled=bool(cfg.enabled),
        updated_at=cfg.updated_at,
    )


@app.put("/llm-config", response_model=LLMConfigOut)
def update_llm_config(payload: LLMConfigIn, db: Session = Depends(get_db)):
    ensure_defaults(db)
    cfg = db.get(LLMConfig, 1)
    cfg.provider = payload.provider
    cfg.model = payload.model
    cfg.api_key = payload.api_key
    cfg.base_url = payload.base_url
    cfg.parse_prompt = payload.parse_prompt
    cfg.advice_prompt = payload.advice_prompt
    cfg.enabled = int(payload.enabled)
    db.commit()
    db.refresh(cfg)
    return get_llm_config(db)


@app.post("/entries/parse", response_model=ParseResult)
async def parse_entry(payload: ParseRequest, db: Session = Depends(get_db)):
    ensure_defaults(db)
    return await parse_food_text(payload, db)


@app.post("/entries", response_model=EntryOut)
async def create_entry(payload: EntryCreate, db: Session = Depends(get_db)):
    ensure_defaults(db)
    summary = totals(payload.items)
    entry = FoodEntry(
        entry_date=payload.entry_date,
        meal_type=payload.meal_type,
        original_text=payload.text,
        total_calories=summary["total_calories"],
        total_protein=summary["total_protein"],
        total_carbs=summary["total_carbs"],
        total_fat=summary["total_fat"],
        items=[FoodItem(**x.model_dump()) for x in payload.items],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    db.refresh(entry, attribute_names=["items"])
    day = await get_day_summary(payload.entry_date, db)
    db.add(AdviceLog(log_date=payload.entry_date, advice=day.advice, context=day.model_dump()))
    db.commit()
    return to_entry_out(entry)


@app.get("/entries", response_model=list[EntryOut])
def list_entries(entry_date: date = Query(...), db: Session = Depends(get_db)):
    ensure_defaults(db)
    q = (
        select(FoodEntry)
        .where(FoodEntry.entry_date == entry_date)
        .options(selectinload(FoodEntry.items))
        .order_by(FoodEntry.created_at.desc())
    )
    rows = db.scalars(q).all()
    return [to_entry_out(r) for r in rows]


@app.put("/entries/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: int, payload: EntryUpdate, db: Session = Depends(get_db)):
    ensure_defaults(db)
    entry = db.get(FoodEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")

    summary = totals(payload.items)
    entry.entry_date = payload.entry_date
    entry.meal_type = payload.meal_type
    entry.original_text = payload.text
    entry.total_calories = summary["total_calories"]
    entry.total_protein = summary["total_protein"]
    entry.total_carbs = summary["total_carbs"]
    entry.total_fat = summary["total_fat"]
    entry.items.clear()
    for item in payload.items:
        entry.items.append(FoodItem(**item.model_dump()))
    db.commit()
    db.refresh(entry)
    db.refresh(entry, attribute_names=["items"])
    return to_entry_out(entry)


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    ensure_defaults(db)
    entry = db.get(FoodEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}


@app.get("/summary/day", response_model=DaySummary)
async def get_day_summary(target_date: date = Query(...), db: Session = Depends(get_db)):
    ensure_defaults(db)
    profile = db.get(UserProfile, 1)
    q = select(FoodEntry).where(FoodEntry.entry_date == target_date).options(selectinload(FoodEntry.items))
    entries = db.scalars(q).all()

    actual = {
        "actual_calories": round(sum(x.total_calories for x in entries), 1),
        "actual_protein": round(sum(x.total_protein for x in entries), 1),
        "actual_carbs": round(sum(x.total_carbs for x in entries), 1),
        "actual_fat": round(sum(x.total_fat for x in entries), 1),
    }
    by_meal: dict[str, dict[str, float]] = {}
    for m in ["breakfast", "lunch", "dinner", "snack"]:
        meal_rows = [e for e in entries if e.meal_type == m]
        by_meal[m] = {
            "calories": round(sum(x.total_calories for x in meal_rows), 1),
            "protein": round(sum(x.total_protein for x in meal_rows), 1),
            "carbs": round(sum(x.total_carbs for x in meal_rows), 1),
            "fat": round(sum(x.total_fat for x in meal_rows), 1),
        }

    draft = {
        "date": target_date,
        "target_calories": profile.calorie_target,
        "target_protein": profile.protein_target,
        "target_carbs": profile.carbs_target,
        "target_fat": profile.fat_target,
        "by_meal": by_meal,
        **actual,
    }
    advice = await build_day_advice(draft, db)
    return DaySummary(
        **draft,
        entries=[to_entry_out(e) for e in entries],
        advice=advice,
    )


@app.get("/summary/week")
async def get_week_summary(end_date: date = Query(...), db: Session = Depends(get_db)):
    ensure_defaults(db)
    days = []
    for i in range(7):
        d = date.fromordinal(end_date.toordinal() - i)
        days.append(await get_day_summary(d, db))
    return {"days": list(reversed([x.model_dump() for x in days]))}


@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    ensure_defaults(db)
    q = select(FoodEntry).options(selectinload(FoodEntry.items)).order_by(FoodEntry.entry_date.desc())
    rows = db.scalars(q).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["entry_id", "date", "meal", "text", "food", "grams", "calories", "protein", "carbs", "fat"])
    for entry in rows:
        for item in entry.items:
            writer.writerow([
                entry.id,
                entry.entry_date.isoformat(),
                entry.meal_type,
                entry.original_text,
                item.name,
                item.grams,
                item.calories,
                item.protein,
                item.carbs,
                item.fat,
            ])

    data = io.BytesIO(buf.getvalue().encode("utf-8-sig"))
    headers = {"Content-Disposition": "attachment; filename=fitness-export.csv"}
    return StreamingResponse(data, media_type="text/csv", headers=headers)


@app.get("/backup/db")
def backup_db():
    if not DB_PATH.exists():
        raise HTTPException(404, "database file not found")
    return FileResponse(DB_PATH, filename="fitness-backup.sqlite3")
