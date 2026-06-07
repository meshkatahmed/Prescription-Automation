from typing import Protocol

from .regex_extractor import RegexExtractor
from .llm_extractor import LLMExtractor
from ..schemas import ExtractionResult


class BaseExtractor(Protocol):
    """Protocol defining the interface for all transcript extractor implementations."""

    def extract(self, raw_transcript: str) -> ExtractionResult:
        """Extract medical fields from the raw transcript."""
        ...

class ExtractionPipeline:
    """Orchestrates or delegates extraction to the selected extractor implementation.
    
    Defaults to regex-based extraction for backwards compatibility.
    """

    def __init__(self, method: str = "regex", **kwargs) -> None:
        self.method = method
        self._extractor: BaseExtractor
        if method == "llm":
            self._extractor = LLMExtractor(**kwargs)
        else:
            self._extractor = RegexExtractor()

    def extract(self, raw_transcript: str) -> ExtractionResult:
        return self._extractor.extract(raw_transcript)
