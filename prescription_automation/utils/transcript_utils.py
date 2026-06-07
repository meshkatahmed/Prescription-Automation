import re
from dataclasses import dataclass
from typing import List


@dataclass
class TranscriptSegment:
    speaker: str
    text: str


SPEAKER_PATTERNS = [
    r"^(Doctor|Dr|Physician)[:\-]?\s*(.+)$",
    r"^(Patient|Pt)[:\-]?\s*(.+)$",
    r"^(Nurse)[:\-]?\s*(.+)$",
]


def normalize_transcript(raw_text: str) -> str:
    normalized = raw_text.strip()
    normalized = re.sub(r"\r\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def parse_transcript(raw_text: str) -> List[TranscriptSegment]:
    normalized = normalize_transcript(raw_text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    segments: List[TranscriptSegment] = []

    for line in lines:
        matched = False
        for pattern in SPEAKER_PATTERNS:
            match = re.match(pattern, line, flags=re.IGNORECASE)
            if match:
                speaker = match.group(1).title()
                text = match.group(2).strip()
                segments.append(TranscriptSegment(speaker=speaker, text=text))
                matched = True
                break
        if not matched:
            if segments:
                segments[-1].text += " " + line
            else:
                segments.append(TranscriptSegment(speaker="Unknown", text=line))
    return segments
