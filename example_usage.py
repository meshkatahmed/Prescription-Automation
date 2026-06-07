import os
from dotenv import load_dotenv
from prescription_automation import ExtractionPipeline

load_dotenv()

SAMPLE_TRANSCRIPT = """
Doctor: Good morning. What brings you in today?
Patient: My name is Jenny, I am a 42 year old female. I'm here because of a severe headache that has been going on for two days.
Doctor: I see. Do you have any other symptoms?
Patient: Yes, I have a mild fever and a bit of a cough.
Doctor: Let's get your measurements and vitals first.
Nurse: She weighs 68 kg and height is 165 cm. Her blood pressure is 130/80, heart rate is 72, and temperature is 98.6.
Doctor: Thank you. Do you have any pre-existing medical conditions or allergies?
Patient: I have a history of hypertension. Also, I am allergic to penicillin.
Doctor: Are you currently taking any medications?
Patient: I take Ibuprofen 200 mg twice daily for pain.
Doctor: Okay, I am going to prescribe Amoxicillin 500 mg three times a day for 7 days instead. Please follow up in two weeks.
"""


def main() -> None:
    print("=== REGEX-BASED EXTRACTION ===")
    regex_pipeline = ExtractionPipeline(method="regex")
    regex_result = regex_pipeline.extract(SAMPLE_TRANSCRIPT)

    print("Patient Info:")
    print(regex_result.patient_info)
    print("\nMedications:")
    for med in regex_result.medications:
        print(f"- {med}")
    print("\nClinical Notes:")
    for note in regex_result.clinical_notes:
        print(f"- {note}")

    print("\n" + "=" * 40 + "\n")

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print("=== LLM-BASED EXTRACTION (Gemini) ===")
        llm_pipeline = ExtractionPipeline(method="llm")
        llm_result = llm_pipeline.extract(SAMPLE_TRANSCRIPT)

        print("Patient Info:")
        print(llm_result.patient_info)
        print("\nMedications:")
        for med in llm_result.medications:
            print(f"- {med}")
        print("\nClinical Notes:")
        for note in llm_result.clinical_notes:
            print(f"- {note}")
    else:
        print("=== LLM-BASED EXTRACTION (Gemini) ===")
        print("[Skipped] Set the 'GEMINI_API_KEY' environment variable to run the LLM extraction demo.")


if __name__ == "__main__":
    main()
