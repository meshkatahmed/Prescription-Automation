from typing import List, Optional
from pydantic import BaseModel, Field


class MedicationEntry(BaseModel):
    name: str = Field(description="Name of the medication prescribed or mentioned")
    dosage: Optional[str] = Field(None, description="Dosage of the medication (e.g. 500 mg, 10 ml)")
    frequency: Optional[str] = Field(None, description="Frequency of administration (e.g. twice daily, every 8 hours)")
    route: Optional[str] = Field(None, description="Route of administration (e.g. oral, topical, IV)")
    duration: Optional[str] = Field(
        None,
        description=(
            "Duration of treatment (e.g. 7 days, 1 week). "
            "Null means the medication is ongoing/indefinite — do NOT invent a duration if none was specified."
        )
    )
    instructions: Optional[str] = Field(None, description="Any additional patient instructions (e.g. take with food)")


class SymptomEntry(BaseModel):
    symptom: str = Field(description="Name/type of symptom (e.g. headache, fever)")
    onset: Optional[str] = Field(None, description="When the symptom started or its duration (e.g. two days ago, since yesterday)")
    severity: Optional[str] = Field(None, description="Severity of the symptom (e.g. mild, severe, 7/10)")
    descriptors: List[str] = Field(default_factory=list, description="Any descriptors or details about the symptom (e.g. throbbing, constant)")


class PatientInfo(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the patient")
    age: Optional[int] = Field(None, description="Age of the patient in years")
    gender: Optional[str] = Field(None, description="Gender of the patient as stated")
    weight: Optional[str] = Field(None, description="Weight of the patient with units (e.g. 68 kg, 150 lbs)")
    height: Optional[str] = Field(None, description="Height of the patient with units (e.g. 165 cm, 5'5\")")
    chief_complaint: Optional[str] = Field(None, description="Primary complaint / main reason for visit, in the patient's or doctor's words")
    conditions: List[str] = Field(default_factory=list, description="Pre-existing diagnosed medical conditions (e.g. hypertension, diabetes) — not symptoms")
    allergies: List[str] = Field(default_factory=list, description="Known allergies to medications or substances")
    current_medications: List[MedicationEntry] = Field(
        default_factory=list,
        description=(
            "Medications the patient was taking BEFORE this visit, as reported at intake. "
            "Do NOT include newly prescribed medications here."
        )
    )
    symptoms: List[SymptomEntry] = Field(default_factory=list, description="Symptoms the patient reports during this visit")
    vital_signs: List[str] = Field(
        default_factory=list,
        description="Vital sign readings as formatted strings (e.g. 'Blood Pressure: 130/80', 'Heart Rate: 72 bpm', 'Temperature: 98.6°F')"
    )
    follow_up_plan: Optional[str] = Field(None, description="Follow-up instructions or scheduled next visit mentioned by the doctor")


class ExtractionResult(BaseModel):
    # raw_transcript: str = Field(default="")
    patient_info: PatientInfo = Field(default_factory=PatientInfo)
    medications: List[MedicationEntry] = Field(
        default_factory=list,
        description=(
            "All medications the patient should be taking AFTER this visit: "
            "includes pre-existing medications NOT discontinued, plus newly prescribed medications. "
            "If the doctor prescribes the same drug at a new dose, use the updated parameters. "
            "Never omit a current medication unless the doctor explicitly stopped it."
        )
    )
    discontinued_medications: List[MedicationEntry] = Field(
        default_factory=list,
        description=(
            "Medications the doctor explicitly stopped or discontinued during this visit "
            "(e.g. 'stop taking X', 'discontinue X'). "
            "Do NOT add medications that were simply not mentioned."
        )
    )
    clinical_notes: List[str] = Field(default_factory=list, description="Clinical notes, observations, and recommendations from the doctor")

