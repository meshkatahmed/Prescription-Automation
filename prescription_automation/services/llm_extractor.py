from typing import Optional
from google import genai
from google.genai import types

from ..schemas import (
    ExtractionResult,
    MedicationEntry,
    PatientInfo,
    SymptomEntry,
)
from ..prompts import render_extraction_prompt


_SCHEMA_MODELS = [
    MedicationEntry,
    SymptomEntry,
    PatientInfo,
    ExtractionResult,
]


class LLMExtractor:
    """LLM-based extractor utilizing Gemini API structured outputs to parse transcript data."""

    def __init__(self, model_name: str = "gemini-2.5-flash", client: Optional[genai.Client] = None) -> None:
        self.model_name = model_name
        if client is not None:
            self.client = client
        else:
            self.client = genai.Client()

    def extract(self, raw_transcript: str) -> ExtractionResult:
        prompt = render_extraction_prompt(raw_transcript)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractionResult,
                temperature=0.0,
            ),
        )

        if hasattr(response, "parsed") and response.parsed is not None:
            parsed_obj = response.parsed
            if isinstance(parsed_obj, ExtractionResult):
                parsed_data = parsed_obj
            else:
                parsed_data = ExtractionResult.model_validate(parsed_obj)
        else:
            parsed_data = ExtractionResult.model_validate_json(response.text)

        parsed_data.raw_transcript = raw_transcript
        return parsed_data
