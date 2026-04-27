"""CLI runner for the Music Recommender — simulation mode and RAG demo mode."""

import argparse
import sys

from .recommender import DEFAULT_WEIGHTS, load_songs, recommend_songs


# ── Simulation mode (unchanged from Module 3) ─────────────────────────────────

PROFILES = {
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.38,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },
    "Edge Case: Sad but Energetic": {
        "favorite_genre": "ambient",
        "favorite_mood": "sad",
        "target_energy": 0.9,
        "likes_acoustic": True,
    },
}


def print_recommendations(
    profile_name: str, recommendations: list[tuple[dict, float, str]]
) -> None:
    """Print one recommendation block in a readable CLI format."""
    print(f"\nTop recommendations for {profile_name}:\n")
    for index, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        print(f"{index}. {song['title']} by {song['artist']}")
        print(
            f"   Genre: {song['genre']} | Mood: {song['mood']} | "
            f"Energy: {song['energy']:.2f} | Score: {score:.2f}"
        )
        print(f"   Reasons: {explanation}")
        print()


def run_simulation() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for profile_name, user_prefs in PROFILES.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_recommendations(profile_name, recommendations)

    experiment_weights = {
        "genre": DEFAULT_WEIGHTS["genre"] / 2,
        "energy": DEFAULT_WEIGHTS["energy"] * 2,
    }
    experiment_recommendations = recommend_songs(
        PROFILES["High-Energy Pop"],
        songs,
        k=5,
        weights=experiment_weights,
    )

    print("Experiment: half genre weight, double energy weight")
    print(
        f"Original weights: genre={DEFAULT_WEIGHTS['genre']}, "
        f"mood={DEFAULT_WEIGHTS['mood']}, energy={DEFAULT_WEIGHTS['energy']}, "
        f"acoustic={DEFAULT_WEIGHTS['acoustic']}"
    )
    print(
        f"Experimental weights: genre={experiment_weights['genre']}, "
        f"mood={DEFAULT_WEIGHTS['mood']}, energy={experiment_weights['energy']}, "
        f"acoustic={DEFAULT_WEIGHTS['acoustic']}"
    )
    print_recommendations("High-Energy Pop (Experiment)", experiment_recommendations)


# ── RAG demo mode ─────────────────────────────────────────────────────────────

_DEMO_INPUTS = [
    "I need something calm and acoustic to focus while studying",
    "Give me high-energy pop bangers for my workout session",
    "I'm feeling melancholy tonight — something slow and soulful please",
]


def run_rag_demo() -> None:
    try:
        from .rag import run_rag_pipeline, validate_input
    except ImportError as exc:
        print(f"ERROR: Could not import RAG module: {exc}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("  NextPlay RAG Demo — Claude-powered music recommendations")
    print("=" * 60)

    for i, text in enumerate(_DEMO_INPUTS, 1):
        print(f"\n[Demo {i}/3] Input: \"{text}\"\n")

        # Input validation shown explicitly so the guardrail is visible
        try:
            validate_input(text)
        except ValueError as exc:
            print(f"  Validation failed: {exc}")
            continue

        try:
            result = run_rag_pipeline(text)
        except EnvironmentError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        except ValueError as exc:
            print(f"  Pipeline error: {exc}")
            continue

        profile = result["profile"]
        print(
            f"  Classified profile → genre: {profile.favorite_genre}, "
            f"mood: {profile.favorite_mood}, "
            f"energy: {profile.target_energy:.2f}, "
            f"acoustic: {profile.likes_acoustic}"
        )
        print()
        print("  Top 3 recommendations:")
        for j, song in enumerate(result["recommendations"], 1):
            print(
                f"    {j}. {song.title} by {song.artist}"
                f" (genre: {song.genre}, energy: {song.energy:.2f})"
            )
        print()
        print("  Explanation:")
        for line in result["explanation"].splitlines():
            print(f"    {line}")
        print("\n" + "-" * 60)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="NextPlay Music Recommender",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  (default)  Run the Module 3 simulation with hardcoded profiles\n"
            "  --rag      Run the RAG demo: Claude classifies 3 example inputs\n"
            "             and explains the recommendations (requires ANTHROPIC_API_KEY)"
        ),
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Run the Claude-powered RAG pipeline demo",
    )
    args = parser.parse_args()

    if args.rag:
        run_rag_demo()
    else:
        run_simulation()


if __name__ == "__main__":
    main()
