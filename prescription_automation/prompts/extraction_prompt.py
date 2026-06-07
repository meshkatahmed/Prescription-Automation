from __future__ import annotations

from importlib import resources
from typing import Iterable

from ..utils.prompt_utils import schema_to_prompt
from ..schemas import MedicationEntry, SymptomEntry, PatientInfo, ExtractionResult


_DEFAULT_MODELS: list[type] = [
	MedicationEntry,
	SymptomEntry,
	PatientInfo,
	ExtractionResult,
]


def render_extraction_prompt(transcript: str, models: Iterable[type] | None = None) -> str:
	"""Return the extraction prompt with the schema and transcript injected.

	Args:
		transcript: The raw transcript to inject into the template.
		models: Optional ordered list of Pydantic model classes used to
			render the schema description. If omitted, a sensible default
			set is used.
	"""
	model_list = list(models) if models is not None else _DEFAULT_MODELS
	schema_description = schema_to_prompt(model_list)

	try:
		template = resources.files("prescription_automation.prompts").joinpath("extraction_prompt.txt").read_text(encoding="utf-8")
	except Exception:
		try:
			with resources.open_text("prescription_automation.prompts", "extraction_prompt.txt", encoding="utf-8") as fh:
				template = fh.read()
		except Exception:
			template = "You are a medical data extraction assistant.\n\n{schema_description}\n\nTranscript:\n{transcript}"

	return template.replace("{schema_description}", schema_description).replace("{transcript}", transcript)
