# app/schemas.py
from pydantic import BaseModel

class HealthImpactBase(BaseModel):
    useful_features: str | None = None
    health_risks: str | None = None
    beneficial_subject: str | None = None
    usage_symptoms: str | None = None
    symptom_frequency: str | None = None
    health_precaution: str | None = None

class HealthImpactOut(HealthImpactBase):
    id: int
    class Config:
        from_attributes = True