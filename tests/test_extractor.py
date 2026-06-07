from unittest.mock import MagicMock
from prescription_automation.services.extractor import (
    ExtractionPipeline,
    RegexExtractor,
    LLMExtractor,
)
from prescription_automation.schemas import (
    ExtractionResult,
    PatientInfo,
    SymptomEntry,
    MedicationEntry,
)


def test_regex_extractor_demographics() -> None:
    transcript = """
Doctor: Hello, I am Dr. Smith.
Patient: I am a 42-year-old female with a headache and fever.
Patient: I take lisinopril 10 mg once daily.
Doctor: I recommend ibuprofen 400 mg every 6 hours as needed.
"""
    # Test via default facade (ExtractionPipeline defaults to regex)
    pipeline = ExtractionPipeline()
    result = pipeline.extract(transcript)

    assert result.patient_info.age == 42
    assert result.patient_info.gender == "female"
    assert any("headache" in symptom.symptom for symptom in result.patient_info.symptoms)
    assert any(med.name.lower().startswith("lisinopril") for med in result.medications)
    assert any(med.name.lower().startswith("ibuprofen") for med in result.medications)

    # Test RegexExtractor directly
    regex_extractor = RegexExtractor()
    result_direct = regex_extractor.extract(transcript)
    assert result_direct.patient_info.age == 42
    assert result_direct.patient_info.gender == "female"


def test_llm_extractor_with_mock() -> None:
    # Set up mock client and response
    mock_client = MagicMock()

    mock_data = ExtractionResult(
        raw_transcript="Doctor: Hello.\nPatient: I have a bad cough.",
        patient_info=PatientInfo(
            name="John Doe",
            age=45,
            gender="male",
            weight="80 kg",
            chief_complaint="Cough and sore throat",
            symptoms=[
                SymptomEntry(
                    symptom="cough",
                    onset="3 days",
                    severity="moderate",
                    descriptors=["dry", "hacking"],
                )
            ],
        ),
        medications=[
            MedicationEntry(
                name="Amoxicillin",
                dosage="500 mg",
                frequency="three times a day",
                route="oral",
                duration="7 days",
                instructions="Take with food",
            )
        ],
        clinical_notes=["Advised rest and hydration.", "Follow up if symptoms worsen."],
    )

    mock_response = MagicMock()
    mock_response.parsed = mock_data
    # Mock return value of generate_content
    mock_client.models.generate_content.return_value = mock_response

    # Initialize LLMExtractor with mock client
    llm_extractor = LLMExtractor(client=mock_client)

    transcript = "Doctor: Hello.\nPatient: I have a bad cough."
    result = llm_extractor.extract(transcript)

    # Check that model generate_content was called
    mock_client.models.generate_content.assert_called_once()

    # Check assertions on the returned ExtractionResult
    assert result.patient_info.name == "John Doe"
    assert result.patient_info.age == 45
    assert result.patient_info.gender == "male"
    assert result.patient_info.weight == "80 kg"
    assert result.patient_info.chief_complaint == "Cough and sore throat"

    assert len(result.patient_info.symptoms) == 1
    assert result.patient_info.symptoms[0].symptom == "cough"
    assert result.patient_info.symptoms[0].onset == "3 days"
    assert result.patient_info.symptoms[0].severity == "moderate"
    assert result.patient_info.symptoms[0].descriptors == ["dry", "hacking"]

    assert len(result.medications) == 1
    assert result.medications[0].name == "Amoxicillin"
    assert result.medications[0].dosage == "500 mg"
    assert result.medications[0].frequency == "three times a day"
    assert result.medications[0].route == "oral"
    assert result.medications[0].duration == "7 days"
    assert result.medications[0].instructions == "Take with food"

    assert result.clinical_notes == ["Advised rest and hydration.", "Follow up if symptoms worsen."]


def test_llm_extractor_uses_schema_prompt() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = ExtractionResult(raw_transcript="Test transcript")
    mock_response.text = '{"raw_transcript": "Test transcript", "patient_info": {}}'
    mock_client.models.generate_content.return_value = mock_response

    llm_extractor = LLMExtractor(client=mock_client)
    llm_extractor.extract("Doctor: Hello. Patient: I have a bad cough.")

    assert mock_client.models.generate_content.call_count == 1
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert "contents" in call_kwargs
    # The external prompt template should be used and include the assistant header
    assert "You are a medical data extraction assistant." in call_kwargs["contents"]
    # The schema description (rendered by prompt_utils) includes a header for ExtractionResult
    assert "### ExtractionResult" in call_kwargs["contents"]
    assert "config" in call_kwargs
    assert getattr(call_kwargs["config"], "response_schema", None) == ExtractionResult


def test_extraction_pipeline_facade_routing() -> None:
    # Verify that pipeline routes to LLMExtractor when method="llm"
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = ExtractionResult(raw_transcript="Test transcript")
    mock_client.models.generate_content.return_value = mock_response

    pipeline = ExtractionPipeline(method="llm", client=mock_client)
    pipeline.extract("Test transcript")

    mock_client.models.generate_content.assert_called_once()


def test_regex_extractor_all_fields() -> None:
    transcript = """
Doctor: Hello. Can you please state your name and what brings you in today?
Patient: My name is Jenny, I'm a 35 year old female. I'm here because of a severe headache that started yesterday.
Doctor: Okay. Do you have any other symptoms?
Patient: Yes, a mild fever.
Doctor: Let's record your vitals.
Nurse: Her blood pressure is 130/85, pulse is 75, temperature is 98.6. She weighs 65 kg and is 165 cm tall.
Doctor: Do you have any medical history, allergies, or current medications?
Patient: I have a history of hypertension. I am allergic to penicillin. And I currently take Lisinopril 10 mg once daily.
Doctor: Thank you. I want you to follow up in two weeks.
"""
    extractor = RegexExtractor()
    result = extractor.extract(transcript)
    info = result.patient_info

    assert info.name == "Jenny"
    assert info.age == 35
    assert info.gender == "female"
    assert info.weight == "65 kg"
    assert info.height == "165 cm"
    assert "headache" in info.chief_complaint
    assert "hypertension" in info.conditions
    assert "penicillin" in info.allergies
    
    assert len(info.current_medications) == 1
    assert info.current_medications[0].name.lower() == "lisinopril"
    assert info.current_medications[0].dosage == "10 mg"
    assert info.current_medications[0].frequency == "once daily"

    assert any("headache" in s.symptom for s in info.symptoms)
    assert any("fever" in s.symptom for s in info.symptoms)

    assert "Blood Pressure: 130/85" in info.vital_signs
    assert "Heart Rate: 75 bpm" in info.vital_signs
    assert "Temperature: 98.6°F" in info.vital_signs

    assert info.follow_up_plan == "Follow up in two weeks"

