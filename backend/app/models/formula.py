from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..db.base import Base


class Formula(Base):
    __tablename__ = "formula"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category_id = Column(
        Integer, ForeignKey("category.id"), nullable=True, index=True
    )
    composition = Column(Text, nullable=True)
    efficacy = Column(Text, nullable=True)
    indication = Column(Text, nullable=True)
    usage_method = Column(Text, nullable=True)
    source_text = Column(Text, nullable=True)
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category = relationship("Category", back_populates="formulas")
    herb_relations = relationship("FormulaHerbRel", back_populates="formula")
