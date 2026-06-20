"""Smoke test for Gemini AI service (S0106). Requires GEMINI_API_KEY in .env.local."""

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.debrief import VisitStructuredInput
from app.services.ai import generate_debrief

STRUCTURED = VisitStructuredInput(
    location="Region Y - Village A",
    visit_date="2026-06-18",
    program_area="Water Access",
    stakeholders="Village council, farmer cooperative",
)

SAMPLE_NOTES = """
Met with village council and farmer cooperative.
Community is engaged but frustrated about water access.

- Irrigation canal damaged in three sections near the east field
- Women's group wants training scheduled before monsoon
- Local official promised fund release but nothing received yet

Council mood was tense but cooperative. They asked for an engineering visit within two weeks.
"""


def main() -> None:
    result = generate_debrief(
        SAMPLE_NOTES,
        structured=STRUCTURED,
        has_photo_notes=False,
    )
    print(json.dumps(result.model_dump(), indent=2))
    assert result.sentiment in {"positive", "neutral", "negative"}
    assert result.findings, "Expected key findings"
    assert result.blockers, "Expected blockers observed"
    print("\nS0106 AI debrief test passed (4 sections present)")


if __name__ == "__main__":
    main()
