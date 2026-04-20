import re

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .deps import get_db
from ..core.responses import success_response
from ..models.category import Category
from ..models.formula import Formula
from ..models.formula_herb_rel import FormulaHerbRel
from ..models.herb import Herb


router = APIRouter(prefix="/api/statistics", tags=["statistics"])


def split_keywords(text: str | None) -> list[str]:
    if not text:
        return []

    parts = re.split(r"[、，,；;。\s]+", text)
    return [item.strip() for item in parts if len(item.strip()) >= 2]


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    herb_count = db.query(func.count(Herb.id)).scalar() or 0
    formula_count = db.query(func.count(Formula.id)).scalar() or 0
    category_count = db.query(func.count(Category.id)).scalar() or 0

    return success_response(
        {
            "herbCount": herb_count,
            "formulaCount": formula_count,
            "categoryCount": category_count,
        }
    )


@router.get("/herb-efficacy")
def get_herb_efficacy_statistics(db: Session = Depends(get_db)):
    herbs = db.query(Herb.efficacy).all()
    counter: dict[str, int] = {}

    for (efficacy,) in herbs:
        for item in split_keywords(efficacy):
            counter[item] = counter.get(item, 0) + 1

    result = [
        {"name": name, "value": value}
        for name, value in sorted(counter.items(), key=lambda item: item[1], reverse=True)[:10]
    ]

    return success_response(result)


@router.get("/formula-category")
def get_formula_category_statistics(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Category.name.label("name"),
            func.count(Formula.id).label("value"),
        )
        .outerjoin(Formula, Formula.category_id == Category.id)
        .filter(Category.category_type == "formula")
        .group_by(Category.id, Category.name)
        .order_by(func.count(Formula.id).desc(), Category.id.asc())
        .all()
    )

    result = [{"name": row.name, "value": int(row.value)} for row in rows]
    return success_response(result)


@router.get("/formula-herb-top")
def get_formula_herb_top_statistics(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Herb.name.label("name"),
            func.count(FormulaHerbRel.id).label("value"),
        )
        .join(FormulaHerbRel, FormulaHerbRel.herb_id == Herb.id)
        .group_by(Herb.id, Herb.name)
        .order_by(func.count(FormulaHerbRel.id).desc(), Herb.id.asc())
        .limit(10)
        .all()
    )

    result = [{"name": row.name, "value": int(row.value)} for row in rows]
    return success_response(result)
