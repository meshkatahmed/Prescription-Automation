import re
from typing import List, Optional

from ..schemas import (
    ExtractionResult,
    MedicationEntry,
    PatientInfo,
    SymptomEntry,
)
from ..utils.transcript_utils import TranscriptSegment, parse_transcript


class RegexExtractor:
    """Regex-based extractor for parsing transcript segments using pre-defined patterns."""

    def __init__(self) -> None:
        self._age_pattern = re.compile(r"\b(\d{1,3})(?:\s*|-)?(?:years?|yrs?)(?:\s+old)?\b", flags=re.IGNORECASE)
        self._gender_pattern = re.compile(r"\b(male|female|man|woman|boy|girl)\b", flags=re.IGNORECASE)
        self._weight_pattern = re.compile(r"\b(\d{2,3}\.?\d*)\s*(?:kg|kilograms|lbs|pounds)\b", flags=re.IGNORECASE)
        self._height_pattern = re.compile(r"\b(\d{1,3}(?:\.\d+)?)(?:\s*(?:cm|centimeters|inches|in))\b", flags=re.IGNORECASE)
        self._medication_pattern = re.compile(
            r"\b([A-Za-z]+)\s+(\d+\s*(?:mg|mcg|g|units|ml|tablet|capsule)s?)\b",
            flags=re.IGNORECASE,
        )
        self._symptom_patterns = [
            re.compile(r"\b(headache|cough|fever|nausea|vomiting|pain|dizziness|fatigue|rash|shortness of breath|sob)\b", flags=re.IGNORECASE),
            re.compile(r"\b(chest pain|abdominal pain|back pain|joint pain|stomach pain)\b", flags=re.IGNORECASE),
        ]
        self._name_pattern = re.compile(
            r"\b(?:my name is|patient(?:\'s)? name(?: is)?|patient name:?|name:)\s*([A-Za-z]{2,}(?:\s+[A-Za-z]{2,})?)\b",
            flags=re.IGNORECASE
        )

    def extract(self, raw_transcript: str) -> ExtractionResult:
        segments = parse_transcript(raw_transcript)
        result = ExtractionResult(raw_transcript=raw_transcript)

        patient_text = self._segments_by_speaker(segments, "Patient")
        doctor_text = self._segments_by_speaker(segments, "Doctor")
        all_text = "\n".join(segment.text for segment in segments)

        result.patient_info = self._extract_patient_info(all_text, patient_text=patient_text)
        result.medications = self._extract_medications(all_text)
        result.clinical_notes = self._extract_clinical_notes(segments)

        return result

    def _segments_by_speaker(self, segments: List[TranscriptSegment], speaker: str) -> str:
        return " ".join(segment.text for segment in segments if segment.speaker.lower() == speaker.lower())

    def _extract_patient_info(self, text: str, patient_text: str = "") -> PatientInfo:
        info = PatientInfo()
        age_match = self._age_pattern.search(text)
        if age_match:
            try:
                info.age = int(age_match.group(1))
            except ValueError:
                pass

        gender_match = self._gender_pattern.search(text)
        if gender_match:
            info.gender = gender_match.group(1).lower()

        weight_match = self._weight_pattern.search(text)
        if weight_match:
            info.weight = weight_match.group(0)

        height_match = self._height_pattern.search(text)
        if height_match:
            info.height = height_match.group(0)

        # Name extraction
        name_match = self._name_pattern.search(text)
        if name_match:
            name_raw = name_match.group(1).strip()
            words = name_raw.split()
            clean_words = []
            for word in words:
                if word.lower() in ["and", "is", "a", "an", "the", "i", "with", "was", "for"]:
                    break
                clean_words.append(word)
            if clean_words:
                info.name = " ".join(clean_words).title()

        info.chief_complaint = self._extract_chief_complaint(text)
        info.symptoms = self._extract_symptoms(text)
        info.conditions = self._extract_conditions(text)
        info.allergies = self._extract_allergies(text)

        # Extract current medications from patient text
        med_source = patient_text if patient_text else text
        info.current_medications = self._extract_current_medications(med_source)

        info.vital_signs = self._extract_vital_signs(text)
        info.follow_up_plan = self._extract_follow_up_plan(text)
        return info

    def _extract_chief_complaint(self, text: str) -> Optional[str]:
        match = re.search(r"\b(chief complaint|main issue|today is|here because)\b(.+?)(?:\.|$)", text, flags=re.IGNORECASE)
        if match:
            return match.group(2).strip()
        return None

    def _extract_symptoms(self, text: str) -> List[SymptomEntry]:
        symptoms: List[SymptomEntry] = []
        seen: set[str] = set()
        for pattern in self._symptom_patterns:
            for match in pattern.finditer(text):
                symptom = match.group(0).lower()
                if symptom not in seen:
                    seen.add(symptom)
                    symptoms.append(SymptomEntry(symptom=symptom))
        return symptoms

    def _extract_conditions(self, text: str) -> List[str]:
        conditions: List[str] = []
        seen: set[str] = set()

        # 1. Match from explicit history/diagnosis patterns
        phrase_pattern = re.compile(
            r"\b(?:history of|diagnosed with|suffers? from|suffer from|has a history of|pmh|past medical history|medical history)(?:\s*(?:is|of|for|with))?\s*([^.\n]+)",
            flags=re.IGNORECASE
        )
        for match in phrase_pattern.finditer(text):
            parts = re.split(r",|\band\b|\bor\b|\bas well as\b", match.group(1), flags=re.IGNORECASE)
            for part in parts:
                clean_part = part.strip()
                if clean_part and len(clean_part.split()) <= 4:
                    clean_lower = clean_part.lower()
                    if clean_lower not in seen and clean_lower not in ["any", "none", "no", "nothing"]:
                        seen.add(clean_lower)
                        conditions.append(clean_part)

        # 2. Match known conditions list
        known_conditions = [
            "diabetes", "hypertension", "asthma", "arthritis", "depression", "anxiety", 
            "gerd", "copd", "hyperlipidemia", "thyroid disease", "hypothyroidism", "hyperthyroidism",
            "cancer", "heart disease", "migraine", "migraines", "stroke", "kidney disease", "chronic pain"
        ]
        for cond in known_conditions:
            if re.search(rf"\b{cond}\b", text, flags=re.IGNORECASE):
                if cond.lower() not in seen:
                    seen.add(cond.lower())
                    conditions.append(cond)
                    
        return conditions

    def _extract_allergies(self, text: str) -> List[str]:
        allergies: List[str] = []
        seen: set[str] = set()
        patterns = [
            re.compile(r"\ballergic to\s+([^.\n]+)", flags=re.IGNORECASE),
            re.compile(r"\ballerg(?:y|ies)(?:\s+to)?\s*(?::|is|are)?\s*([^.\n]+)", flags=re.IGNORECASE),
        ]
        for pattern in patterns:
            for match in pattern.finditer(text):
                raw_allergies = re.split(r",|\band\b|\bor\b|\bas well as\b", match.group(1), flags=re.IGNORECASE)
                for item in raw_allergies:
                    item_clean = item.strip()
                    if item_clean:
                        clause_match = re.split(r"\b(?:but|since|which|that|when|because)\b", item_clean, flags=re.IGNORECASE)
                        item_clean = clause_match[0].strip()
                        if item_clean and item_clean.lower() not in ["none", "no", "no known allergies", "nka", "nothing"]:
                            if item_clean.lower() not in seen and len(item_clean.split()) <= 3:
                                seen.add(item_clean.lower())
                                allergies.append(item_clean)
        return allergies

    def _parse_medication_details(self, sentence: str, name: str, dosage: str) -> MedicationEntry:
        freq_pattern = re.compile(
            r"\b((?:once|twice|three|four|\d)\s*(?:times?\s*(?:a|per)\s*(?:day|daily|week)|daily|every\s*(?:\d+|six|eight|twelve|24)\s*(?:hours?|hrs?)|at bedtime|as needed|prn))\b",
            flags=re.IGNORECASE
        )
        freq_match = freq_pattern.search(sentence)
        frequency = freq_match.group(1).strip() if freq_match else None

        route_pattern = re.compile(
            r"\b(oral|po|by mouth|topical|sublingual|iv|im|subcutaneous|injection|inhaled)\b",
            flags=re.IGNORECASE
        )
        route_match = route_pattern.search(sentence)
        route = route_match.group(1).strip() if route_match else None

        duration_pattern = re.compile(
            r"\b(?:for\s+)?(\d+\s*(?:days?|weeks?|months?))\b",
            flags=re.IGNORECASE
        )
        duration_match = duration_pattern.search(sentence)
        duration = duration_match.group(1).strip() if duration_match else None

        instructions_pattern = re.compile(
            r"\b((?:with|without)\s+food|on an empty stomach|before\s*(?:meals?|bedtime)|after\s*meals?)\b",
            flags=re.IGNORECASE
        )
        inst_match = instructions_pattern.search(sentence)
        instructions = inst_match.group(1).strip() if inst_match else None

        return MedicationEntry(
            name=name,
            dosage=dosage,
            frequency=frequency,
            route=route,
            duration=duration,
            instructions=instructions
        )

    def _extract_medication_entries(self, text: str) -> List[MedicationEntry]:
        entries: List[MedicationEntry] = []
        seen: set[str] = set()
        
        sentences = re.split(r"[.\n]", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            for match in self._medication_pattern.finditer(sentence):
                name = match.group(1).strip()
                dosage = match.group(2).strip()
                
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    entry = self._parse_medication_details(sentence, name, dosage)
                    entries.append(entry)
                    
        return entries

    def _extract_current_medications(self, text: str) -> List[MedicationEntry]:
        return self._extract_medication_entries(text)

    def _extract_medications(self, text: str) -> List[MedicationEntry]:
        return self._extract_medication_entries(text)

    def _extract_vital_signs(self, text: str) -> List[str]:
        vitals: List[str] = []
        seen: set[str] = set()
        
        bp_pattern = re.compile(
            r"\b(?:bp|blood pressure)(?:\s*(?:is|of|:))?\s*(\d{2,3}/\d{2,3})\b",
            flags=re.IGNORECASE
        )
        for match in bp_pattern.finditer(text):
            vital_str = f"Blood Pressure: {match.group(1)}"
            if vital_str.lower() not in seen:
                seen.add(vital_str.lower())
                vitals.append(vital_str)
                
        hr_pattern = re.compile(
            r"\b(?:heart rate|hr|pulse)(?:\s*(?:is|of|:))?\s*(\d{2,3})\s*(?:bpm)?\b",
            flags=re.IGNORECASE
        )
        for match in hr_pattern.finditer(text):
            val = int(match.group(1))
            if 40 <= val <= 200:
                vital_str = f"Heart Rate: {val} bpm"
                if vital_str.lower() not in seen:
                    seen.add(vital_str.lower())
                    vitals.append(vital_str)
                    
        temp_pattern = re.compile(
            r"\b(?:temp|temperature)(?:\s*(?:is|of|:))?\s*(\d{2,3}(?:\.\d+)?)\s*(?:f|c|degrees|deg)?\b",
            flags=re.IGNORECASE
        )
        for match in temp_pattern.finditer(text):
            temp_val = float(match.group(1))
            unit = "°F"
            if temp_val < 45.0:
                unit = "°C"
            vital_str = f"Temperature: {temp_val}{unit}"
            if vital_str.lower() not in seen:
                seen.add(vital_str.lower())
                vitals.append(vital_str)
                
        o2_pattern = re.compile(
            r"\b(?:o2(?:\s*sat)?|oxygen(?:\s*saturation|level)?)(?:\s*(?:is|of|:))?\s*(\d{2,3})\s*%\b",
            flags=re.IGNORECASE
        )
        for match in o2_pattern.finditer(text):
            val = int(match.group(1))
            if 50 <= val <= 100:
                vital_str = f"O2 Saturation: {val}%"
                if vital_str.lower() not in seen:
                    seen.add(vital_str.lower())
                    vitals.append(vital_str)
                    
        rr_pattern = re.compile(
            r"\b(?:rr|respiratory rate)(?:\s*(?:is|of|:))?\s*(\d{1,2})\b",
            flags=re.IGNORECASE
        )
        for match in rr_pattern.finditer(text):
            val = int(match.group(1))
            if 8 <= val <= 40:
                vital_str = f"Respiratory Rate: {val} breaths/min"
                if vital_str.lower() not in seen:
                    seen.add(vital_str.lower())
                    vitals.append(vital_str)
                    
        return vitals

    def _extract_follow_up_plan(self, text: str) -> Optional[str]:
        follow_up_pattern = re.compile(
            r"\b(?:follow up|see you back|return to clinic|schedule a visit)\s+([^.\n]+)",
            flags=re.IGNORECASE
        )
        match = follow_up_pattern.search(text)
        if match:
            plan = match.group(1).strip()
            if len(plan.split()) <= 15:
                return f"Follow up {plan}"
            else:
                return f"Follow up { ' '.join(plan.split()[:10]) }..."
        
        worsen_pattern = re.compile(
            r"\b(return|call|come back|follow up)\s+(?:if|should|if symptoms worsen|if you feel worse)\b[^.\n]+",
            flags=re.IGNORECASE
        )
        match_worsen = worsen_pattern.search(text)
        if match_worsen:
            return match_worsen.group(0).strip()
            
        return None

    def _extract_clinical_notes(self, segments: List[TranscriptSegment]) -> List[str]:
        notes: List[str] = []
        for segment in segments:
            if segment.speaker.lower() == "doctor":
                notes.append(segment.text)
        return notes
