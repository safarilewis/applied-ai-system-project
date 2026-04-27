"""CLI runner for the Music Recommender Simulation."""

from .recommender import DEFAULT_WEIGHTS, load_songs, recommend_songs


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


def print_recommendations(profile_name: str, recommendations: list[tuple[dict, float, str]]) -> None:
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


def main() -> None:
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


if __name__ == "__main__":
    main()
