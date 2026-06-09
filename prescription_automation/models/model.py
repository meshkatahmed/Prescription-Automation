from pydantic import BaseModel, Field
from typing import Optional

from prescription_automation.schemas.schema import ExtractionResult

class ExtractRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description='Raw transcript text to extract')


class ExtractResponse(BaseModel):
    regex: ExtractionResult
    llm: Optional[ExtractionResult] = Field(
        None, description='LLM extraction result, if available.'
    )
    llm_error: Optional[str] = Field(
        None,
        description='LLM extraction error message if extraction failed.',
    )