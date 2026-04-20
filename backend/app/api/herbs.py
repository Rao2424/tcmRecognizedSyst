from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .deps import get_db
from ..core.responses import success_response
from ..models.herb import Herb


router = APIRouter(prefix="/api/herbs", tags=["herbs"])


def serialize_herb_list_item(herb: Herb) -> dict:
    return {
        "id": herb.id,
        "name": herb.name,
        "alias": herb.alias,
        "categoryId": herb.category_id,
        "categoryName": herb.category.name if herb.category else None,
        "efficacy": herb.efficacy,
        "indication": herb.indication,
    }


def serialize_herb_detail(herb: Herb) -> dict:
    return {
        "id": herb.id,
        "name": herb.name,
        "alias": herb.alias,
        "categoryId": herb.category_id,
        "categoryName": herb.category.name if herb.category else None,
        "natureFlavor": herb.nature_flavor,
        "meridianTropism": herb.meridian_tropism,
        "efficacy": herb.efficacy,
        "indication": herb.indication,
        "usageMethod": herb.usage_method,
        "precaution": herb.precaution,
        "sourceText": herb.source_text,
        "createdAt": herb.created_at.isoformat() if herb.created_at else None,
        "updatedAt": herb.updated_at.isoformat() if herb.updated_at else None,
    }


@router.get("")
def list_herbs(
    keyword: str | None = Query(default=None, description="名称/别名/功效关键词"),
    category_id: int | None = Query(default=None, alias="categoryId"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(Herb).options(joinedload(Herb.category))

    if keyword:
        like_keyword = f"%{keyword.strip()}%"
        query = query.filter(
            (Herb.name.like(like_keyword))
            | (Herb.alias.like(like_keyword))
            | (Herb.efficacy.like(like_keyword))
            | (Herb.indication.like(like_keyword))
        )

    if category_id is not None:
        query = query.filter(Herb.category_id == category_id)

    total = query.count()
    items = (
        query.order_by(Herb.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return success_response(
        {
            "list": [serialize_herb_list_item(item) for item in items],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
            },
        }
    )


@router.get("/{herb_id}")
def get_herb_detail(herb_id: int, db: Session = Depends(get_db)):
    herb = (
        db.query(Herb)
        .options(joinedload(Herb.category))
        .filter(Herb.id == herb_id)
        .first()
    )

    if not herb:
        raise HTTPException(status_code=404, detail="药材不存在")

    return success_response(serialize_herb_detail(herb))
