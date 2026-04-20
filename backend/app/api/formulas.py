from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .deps import get_db
from ..core.responses import success_response
from ..models.formula import Formula


router = APIRouter(prefix="/api/formulas", tags=["formulas"])


def serialize_formula_list_item(formula: Formula) -> dict:
    return {
        "id": formula.id,
        "name": formula.name,
        "categoryId": formula.category_id,
        "categoryName": formula.category.name if formula.category else None,
        "efficacy": formula.efficacy,
        "indication": formula.indication,
    }


def serialize_formula_detail(formula: Formula) -> dict:
    herb_items = []
    for relation in formula.herb_relations:
        herb_items.append(
            {
                "id": relation.herb.id if relation.herb else None,
                "name": relation.herb.name if relation.herb else None,
                "amountDesc": relation.amount_desc,
            }
        )

    return {
        "id": formula.id,
        "name": formula.name,
        "categoryId": formula.category_id,
        "categoryName": formula.category.name if formula.category else None,
        "composition": formula.composition,
        "efficacy": formula.efficacy,
        "indication": formula.indication,
        "usageMethod": formula.usage_method,
        "sourceText": formula.source_text,
        "herbs": herb_items,
        "createdAt": formula.created_at.isoformat() if formula.created_at else None,
        "updatedAt": formula.updated_at.isoformat() if formula.updated_at else None,
    }


@router.get("")
def list_formulas(
    keyword: str | None = Query(default=None, description="名称/功效/主治关键词"),
    category_id: int | None = Query(default=None, alias="categoryId"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(Formula).options(joinedload(Formula.category))

    if keyword:
        like_keyword = f"%{keyword.strip()}%"
        query = query.filter(
            (Formula.name.like(like_keyword))
            | (Formula.efficacy.like(like_keyword))
            | (Formula.indication.like(like_keyword))
        )

    if category_id is not None:
        query = query.filter(Formula.category_id == category_id)

    total = query.count()
    items = (
        query.order_by(Formula.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return success_response(
        {
            "list": [serialize_formula_list_item(item) for item in items],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
            },
        }
    )


@router.get("/{formula_id}")
def get_formula_detail(formula_id: int, db: Session = Depends(get_db)):
    formula = (
        db.query(Formula)
        .options(
            joinedload(Formula.category),
            joinedload(Formula.herb_relations).joinedload("herb"),
        )
        .filter(Formula.id == formula_id)
        .first()
    )

    if not formula:
        raise HTTPException(status_code=404, detail="方剂不存在")

    return success_response(serialize_formula_detail(formula))
