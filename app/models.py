from sqlalchemy import Column, Integer, String, Text
from .db import Base
from BackendMentalHelp.app.db import Base
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


class HealthImpact(Base):
    __tablename__ = "Health_impact"
    id = Column(Integer, primary_key=True, index=True)
    useful_features = Column(String(255), index=True)
    health_risks = Column(String(255), index=True)
    beneficial_subject = Column(String(255), index=True)
    usage_symptoms = Column(String(255), index=True)
    symptom_frequency = Column(String(255), index=True)
    health_precaution = Column(String(255), index=True)
