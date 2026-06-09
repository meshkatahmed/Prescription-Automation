from __future__ import annotations

import os
from dotenv import load_dotenv
from typing import Optional

from fastapi import FastAPI

from prescription_automation import ExtractRequest,ExtractResponse,ExtractionResult,ExtractionPipeline

load_dotenv()

app = FastAPI(
    title='Prescription Automation API',
    version='0.1.0',
    description='Extract medical information from transcript text using regex and LLM extractors separately.',
)

@app.post('/extract', response_model=ExtractResponse)
def extract(request: ExtractRequest) -> ExtractResponse:
    regex_pipeline = ExtractionPipeline(method='regex')
    regex_result = regex_pipeline.extract(request.transcript)

    llm_result: Optional[ExtractionResult] = None
    llm_error: Optional[str] = None
    
    if not (os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')):
        
        llm_error = (
            'LLM extraction skipped: set GEMINI_API_KEY or GOOGLE_API_KEY '
            'in the environment to enable LLM extraction.'
        )
    else:
        try:
            llm_pipeline = ExtractionPipeline(method='llm')
            llm_result = llm_pipeline.extract(request.transcript)
        except Exception as exc:
            llm_error = str(exc)

    return ExtractResponse(regex=regex_result, llm=llm_result, llm_error=llm_error)
