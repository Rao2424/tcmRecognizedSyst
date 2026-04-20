from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..db.base import Base


class Herb(Base):
    __tablename__ = "herb"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    alias = Column(String(255), nullable=True)
    category_id = Column(
        Integer, ForeignKey("category.id"), nullable=True, index=True
    )
    nature_flavor = Column(String(255), nullable=True)
    meridian_tropism = Column(String(255), nullable=True)
    efficacy = Column(Text, nullable=True)
    indication = Column(Text, nullable=True)
    usage_method = Column(Text, nullable=True)
    precaution = Column(Text, nullable=True)
    source_text = Column(Text, nullable=True)
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category = relationship("Category", back_populates="herbs")
    formula_relations = relationship("FormulaHerbRel", back_populates="herb")
