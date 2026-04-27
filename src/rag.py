"""RAG pipeline: free-text → Claude classifier → UserProfile → Recommender → Claude explainer."""

import json
import logging
import os
from pathlib import Path

import anthropic

from .recommender import Recommender, Song, UserProfile, load_songs

# ── Logging ──────────────────────────────────────────────────────────────────
_LOG_PATH = Path(__file__).resolve().parents[1] / "rag_errors.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_file_handler = logging.FileHandler(_LOG_PATH)
_file_handler.setLevel(logging.ERROR)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
)
logger.addHandler(_file_handler)

# ── Constants ─────────────────────────────────────────────────────────────────
_SONGS_CSV = Path(__file__).resolve().parents[1] / "data" / "songs.csv"

_VALID_GENRES = {
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave", "indie pop",
    "world", "edm", "electropop", "metal", "folk", "blues", "acoustic",
    "reggaeton",
}
_VALID_MOODS = {
    "happy", "chill", "intense", "relaxed", "dreamy", "moody", "focused",
    "energetic", "playful", "peaceful", "warm", "soulful", "dark", "confident",
}

_CLASSIFIER_PROMPT = """\
You are a music preference classifier. Given a user's free-text description \
of their music taste or current mood, extract a structured profile.

Return ONLY valid JSON with exactly these four keys:
- "favorite_genre": one of [{genres}]
- "favorite_mood": one of [{moods}]
- "target_energy": a float between 0.0 (very calm) and 1.0 (very intense)
- "likes_acoustic": true or false

User description: {{text}}

JSON:\
""".format(
    genres=", ".join(sorted(_VALID_GENRES)),
    moods=", ".join(sorted(_VALID_MOODS)),
)

_EXPLAINER_PROMPT = """\
You are a friendly music concierge explaining recommendations to a listener.

Profile detected from their description:
- Favorite genre: {genre}
- Favorite mood: {mood}
- Target energy: {energy:.2f}  (0 = very calm, 1 = very intense)
- Likes acoustic: {acoustic}

Top recommended songs:
{songs}

Write 2-4 warm, specific sentences explaining why each song fits this listener. \
Speak directly to the user using "you". Reference each song title at least once.\
"""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Run: export ANTHROPIC_API_KEY=your-key-here"
        )
    return anthropic.Anthropic(api_key=api_key)


def _load_songs() -> list[Song]:
    raw = load_songs(str(_SONGS_CSV))
    return [
        Song(
            id=int(s["id"]),
            title=s["title"],
            artist=s["artist"],
            genre=s["genre"],
            mood=s["mood"],
            energy=float(s["energy"]),
            tempo_bpm=float(s["tempo_bpm"]),
            valence=float(s["valence"]),
            danceability=float(s["danceability"]),
            acousticness=float(s["acousticness"]),
        )
        for s in raw
    ]


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that Claude sometimes wraps JSON in."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


# ── Public API ────────────────────────────────────────────────────────────────
def validate_input(text: str) -> str:
    """
    Clean and validate free-text input.
    Raises ValueError with a user-readable message on bad input.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    text = text.strip()
    if not text:
        raise ValueError("Input cannot be empty — please describe your music mood.")
    if len(text) < 5:
        raise ValueError("Input is too short — please give a bit more detail.")
    if len(text) > 2000:
        raise ValueError("Input is too long — please keep it under 2000 characters.")
    # Gibberish guard: require at least 2 real alphabetic words (≥ 2 letters each)
    real_words = [w for w in text.split() if sum(c.isalpha() for c in w) >= 2]
    if len(real_words) < 2:
        raise ValueError(
            "Input looks like gibberish — please describe your music taste in plain words."
        )
    return text


def classify_input(text: str) -> UserProfile:
    """
    Use Claude to parse a free-text music description into a UserProfile.
    Validates the input first; raises ValueError on bad input or bad response.
    """
    text = validate_input(text)
    logger.info("Classifying input: %r", text[:100])

    prompt = _CLASSIFIER_PROMPT.format(text=text)

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = _strip_fences(response.content[0].text)
        logger.info("Classifier raw response: %s", raw)
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse failed for input %r: %s", text[:50], exc)
        raise ValueError(f"Claude returned non-JSON output: {exc}") from exc
    except EnvironmentError:
        raise
    except Exception as exc:
        logger.error("Classification API error for input %r: %s", text[:50], exc)
        raise

    profile = UserProfile(
        favorite_genre=str(data.get("favorite_genre", "pop")).lower().strip(),
        favorite_mood=str(data.get("favorite_mood", "happy")).lower().strip(),
        target_energy=max(0.0, min(1.0, float(data.get("target_energy", 0.5)))),
        likes_acoustic=bool(data.get("likes_acoustic", False)),
    )
    logger.info("Classified profile: %s", profile)
    return profile


def explain_recommendations(profile: UserProfile, songs: list[Song]) -> str:
    """
    Use Claude to generate a natural-language explanation for the recommended songs.
    Returns a plain string; raises on API error.
    """
    if not songs:
        return "No recommendations available to explain."

    song_lines = "\n".join(
        f"{i + 1}. '{s.title}' by {s.artist}"
        f" — genre: {s.genre}, mood: {s.mood}, energy: {s.energy:.2f}"
        for i, s in enumerate(songs)
    )
    prompt = _EXPLAINER_PROMPT.format(
        genre=profile.favorite_genre,
        mood=profile.favorite_mood,
        energy=profile.target_energy,
        acoustic=profile.likes_acoustic,
        songs=song_lines,
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = response.content[0].text.strip()
        logger.info("Explanation generated (%d chars)", len(explanation))
        return explanation
    except EnvironmentError:
        raise
    except Exception as exc:
        logger.error("Explainer API error: %s", exc)
        raise


def run_rag_pipeline(text: str) -> dict:
    """
    Full RAG pipeline:
      validate → Claude classify → Recommender retrieve → Claude explain

    Returns:
        {
            "profile": UserProfile,
            "recommendations": list[Song],   # top 3
            "explanation": str,
        }
    Raises ValueError on invalid input, EnvironmentError if API key missing.
    """
    logger.info("=== RAG pipeline start ===")

    profile = classify_input(text)

    songs = _load_songs()
    recommender = Recommender(songs)
    top_songs = recommender.recommend(profile, k=3)
    logger.info("Top recommendations: %s", [s.title for s in top_songs])

    explanation = explain_recommendations(profile, top_songs)

    logger.info("=== RAG pipeline complete ===")
    return {
        "profile": profile,
        "recommendations": top_songs,
        "explanation": explanation,
    }
