import logging

from .base import Base
from .seed_data import seed_sample_data
from .session import SessionLocal, engine
from ..models import category, formula, formula_herb_rel, herb


logger = logging.getLogger(__name__)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_sample_data(db)
    except Exception:
        db.rollback()
        logger.exception("Failed to seed sample data.")
        raise
    finally:
        db.close()
