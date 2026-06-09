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
from ..utils.transcript_utils import normalize_transcript


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

    def extract(self, transcript: str) -> ExtractionResult:
        normalized_transcript = normalize_transcript(transcript)
        prompt = render_extraction_prompt(normalized_transcript)

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

        return parsed_data
