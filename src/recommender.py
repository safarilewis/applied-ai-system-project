import csv
from dataclasses import dataclass
from typing import Dict, List, Tuple


DEFAULT_WEIGHTS = {
    "genre": 2.0,
    "mood": 1.0,
    "energy": 1.5,
    "acoustic": 0.5,
}


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked for the given user profile."""
        scored_songs = []
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }

        for song in self.songs:
            song_dict = {
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "genre": song.genre,
                "mood": song.mood,
                "energy": song.energy,
                "tempo_bpm": song.tempo_bpm,
                "valence": song.valence,
                "danceability": song.danceability,
                "acousticness": song.acousticness,
            }
            score, _ = score_song(user_prefs, song_dict)
            scored_songs.append((score, song))

        ranked = sorted(scored_songs, key=lambda item: item[0], reverse=True)
        return [song for _, song in ranked[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a short natural-language explanation for one recommendation."""
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        song_dict = {
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "genre": song.genre,
            "mood": song.mood,
            "energy": song.energy,
            "tempo_bpm": song.tempo_bpm,
            "valence": song.valence,
            "danceability": song.danceability,
            "acousticness": song.acousticness,
        }
        _, reasons = score_song(user_prefs, song_dict)
        return ", ".join(reasons)


def score_song(user_prefs: Dict, song: Dict, weights: Dict[str, float] | None = None) -> Tuple[float, List[str]]:
    """Score one song against one user profile and return reasons."""
    active_weights = DEFAULT_WEIGHTS.copy()
    if weights:
        active_weights.update(weights)

    score = 0.0
    reasons = []

    favorite_genre = user_prefs.get("favorite_genre", user_prefs.get("genre", "")).strip().lower()
    favorite_mood = user_prefs.get("favorite_mood", user_prefs.get("mood", "")).strip().lower()
    target_energy = float(user_prefs.get("target_energy", user_prefs.get("energy", 0.5)))
    likes_acoustic = bool(user_prefs.get("likes_acoustic", False))

    song_genre = str(song["genre"]).strip().lower()
    song_mood = str(song["mood"]).strip().lower()
    song_energy = float(song["energy"])
    song_acousticness = float(song["acousticness"])

    if song_genre == favorite_genre:
        genre_points = active_weights["genre"]
        score += genre_points
        reasons.append(f"genre match (+{genre_points:.2f})")

    if song_mood == favorite_mood:
        mood_points = active_weights["mood"]
        score += mood_points
        reasons.append(f"mood match (+{mood_points:.2f})")

    energy_closeness = max(0.0, 1 - abs(song_energy - target_energy))
    energy_points = active_weights["energy"] * energy_closeness
    score += energy_points
    reasons.append(f"energy closeness (+{energy_points:.2f})")

    if likes_acoustic:
        acoustic_points = active_weights["acoustic"] * song_acousticness
        score += acoustic_points
        reasons.append(f"acoustic bonus (+{acoustic_points:.2f})")
    else:
        non_acoustic_points = active_weights["acoustic"] * (1 - song_acousticness)
        score += non_acoustic_points
        reasons.append(f"less-acoustic bonus (+{non_acoustic_points:.2f})")

    return score, reasons

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from CSV and convert numeric columns to numbers."""
    songs = []
    int_fields = {"id"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}

    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            parsed_row = dict(row)
            for field in int_fields:
                parsed_row[field] = int(parsed_row[field])
            for field in float_fields:
                parsed_row[field] = float(parsed_row[field])
            songs.append(parsed_row)

    return songs

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights: Dict[str, float] | None = None,
) -> List[Tuple[Dict, float, str]]:
    """Return the top-k song recommendations with scores and explanations."""
    scored_results = []

    for song in songs:
        score, reasons = score_song(user_prefs, song, weights=weights)
        explanation = ", ".join(reasons)
        scored_results.append((song, score, explanation))

    ranked_results = sorted(scored_results, key=lambda item: item[1], reverse=True)
    return ranked_results[:k]
