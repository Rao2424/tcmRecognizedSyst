from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..db.base import Base


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)
    category_type = Column(String(50), index=True, nullable=False)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    herbs = relationship("Herb", back_populates="category")
    formulas = relationship("Formula", back_populates="category")
