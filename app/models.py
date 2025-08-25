from sqlalchemy import Column, Integer, String, Text
from .db import Base

class FlipCard(Base):
    __tablename__ = "flip_card"
    id = Column(Integer, primary_key=True, index=True)
    negative_text = Column(Text, nullable=False)
    positive_text = Column(Text, nullable=False)
    tag = Column(String(32), nullable=True)

class Tip(Base):
    __tablename__ = "tip"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    mood_tag = Column(String(32), nullable=True)
