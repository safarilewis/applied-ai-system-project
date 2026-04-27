"""RAG evaluation harness — 5 predefined free-text inputs through the full pipeline.

Run as a test suite:
    pytest tests/test_rag.py -v

Run as a standalone script to see the X/5 summary:
    python tests/test_rag.py

Each test checks:
  (a) A UserProfile was returned
  (b) At least 1 song was recommended
  (c) An explanation string was returned
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from src.recommender import UserProfile, Song
from src.rag import run_rag_pipeline


# ── Test cases ────────────────────────────────────────────────────────────────
# Each tuple: (label, free_text_input)
_CASES = [
    (
        "chill-study",
        "I need something calm and acoustic to focus while I study",
    ),
    (
        "high-energy-workout",
        "Give me high-energy pop bangers for my workout",
    ),
    (
        "sad-evening",
        "I am feeling melancholy tonight, something slow and soulful please",
    ),
    (
        "late-night-drive",
        "Moody synthwave or electronic music for a late night drive",
    ),
    (
        "upbeat-party",
        "Upbeat dance music to get the party started, something energetic",
    ),
]

_NEEDS_KEY = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API tests",
)


# ── Individual pytest tests ───────────────────────────────────────────────────

@_NEEDS_KEY
def test_rag_chill_study():
    _assert_pipeline_ok("chill-study", _CASES[0][1])


@_NEEDS_KEY
def test_rag_high_energy_workout():
    _assert_pipeline_ok("high-energy-workout", _CASES[1][1])


@_NEEDS_KEY
def test_rag_sad_evening():
    _assert_pipeline_ok("sad-evening", _CASES[2][1])


@_NEEDS_KEY
def test_rag_late_night_drive():
    _assert_pipeline_ok("late-night-drive", _CASES[3][1])


@_NEEDS_KEY
def test_rag_upbeat_party():
    _assert_pipeline_ok("upbeat-party", _CASES[4][1])


def _assert_pipeline_ok(label: str, text: str) -> None:
    result = run_rag_pipeline(text)

    # (a) UserProfile was returned
    assert isinstance(result["profile"], UserProfile), (
        f"[{label}] expected a UserProfile, got {type(result['profile'])}"
    )

    # (b) At least 1 song recommended
    recs = result["recommendations"]
    assert isinstance(recs, list) and len(recs) >= 1, (
        f"[{label}] expected ≥1 recommendation, got {recs!r}"
    )
    assert all(isinstance(s, Song) for s in recs), (
        f"[{label}] recommendations must be Song objects"
    )

    # (c) Explanation string returned
    explanation = result["explanation"]
    assert isinstance(explanation, str) and explanation.strip(), (
        f"[{label}] expected a non-empty explanation string, got {explanation!r}"
    )


# ── Standalone runner (prints X/5 summary) ───────────────────────────────────

def _run_all_and_summarise() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set. Cannot run live tests.")
        print("       export ANTHROPIC_API_KEY=your-key-here  then re-run.")
        sys.exit(1)

    passed = 0
    total = len(_CASES)

    for label, text in _CASES:
        print(f"\n[{label}]")
        print(f"  Input:  {text!r}")
        try:
            result = run_rag_pipeline(text)
            profile = result["profile"]
            recs = result["recommendations"]
            explanation = result["explanation"]

            ok_profile = isinstance(profile, UserProfile)
            ok_recs = isinstance(recs, list) and len(recs) >= 1
            ok_expl = isinstance(explanation, str) and bool(explanation.strip())

            if ok_profile and ok_recs and ok_expl:
                passed += 1
                print(f"  Got:    genre={profile.favorite_genre}, "
                      f"mood={profile.favorite_mood}, "
                      f"energy={profile.target_energy:.2f}")
                print(f"  Songs:  {', '.join(s.title for s in recs)}")
                print(f"  Status: PASS")
            else:
                failures = []
                if not ok_profile:
                    failures.append(f"profile={profile!r}")
                if not ok_recs:
                    failures.append(f"recs={recs!r}")
                if not ok_expl:
                    failures.append(f"explanation={explanation!r}")
                print(f"  Status: FAIL ({'; '.join(failures)})")

        except Exception as exc:
            print(f"  Status: FAIL — exception: {exc}")

    print(f"\n{'='*50}")
    print(f"Result: {passed}/{total} tests passed")
    print('='*50)


if __name__ == "__main__":
    _run_all_and_summarise()
