from pydantic import BaseModel
from typing import Optional

class PatientCreate(BaseModel):
    name: str
    age: int
    condition: str

class Patient(PatientCreate):
    patient_id: str