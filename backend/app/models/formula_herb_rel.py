from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from ..db.base import Base


class FormulaHerbRel(Base):
    __tablename__ = "formula_herb_rel"

    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(
        Integer, ForeignKey("formula.id"), nullable=False, index=True
    )
    herb_id = Column(
        Integer, ForeignKey("herb.id"), nullable=False, index=True
    )
    amount_desc = Column(String(100), nullable=True)
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )

    formula = relationship("Formula", back_populates="herb_relations")
    herb = relationship("Herb", back_populates="formula_relations")
