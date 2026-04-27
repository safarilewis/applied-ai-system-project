# Reflection Notes

## Profiles Tested

- `High-Energy Pop`
- `Chill Lofi`
- `Deep Intense Rock`
- `Edge Case: Sad but Energetic`

## Pair Comparisons

`High-Energy Pop` vs `Chill Lofi`: The pop profile pushed upbeat, glossy songs like `Sunrise City` and `Gym Hero` to the top because the target energy was high and the acoustic preference was off. The chill lofi profile moved toward `Library Rain` and `Midnight Coding` because the lower target energy and acoustic bonus rewarded calmer and softer tracks.

`High-Energy Pop` vs `Deep Intense Rock`: Both profiles liked high energy songs, so some overlap happened around tracks like `Gym Hero`. The difference is that the rock profile strongly favored `Storm Runner` because it matched both the `rock` genre and `intense` mood, while the pop profile preferred `Sunrise City` because it aligned with `pop` and `happy`.

`Chill Lofi` vs `Deep Intense Rock`: These outputs separated very clearly, which is a good sign for the scoring logic. The lofi profile preferred low-energy, more acoustic songs, while the rock profile favored loud and driving songs with very low acousticness.

`Chill Lofi` vs `Edge Case: Sad but Energetic`: The chill lofi profile produced results that felt coherent because the preferences pointed in one direction. The edge-case profile produced more awkward results because the mood and energy combination was unusual for the small dataset, so the recommender had to settle for partial matches instead of a true fit.

`High-Energy Pop` vs `Edge Case: Sad but Energetic`: The pop profile got clean upbeat recommendations because the catalog has several songs that fit that pattern. The edge-case profile exposed a weakness: the system used genre and acoustic bonuses to keep `Spacewalk Thoughts` on top even though its energy was not close to the requested high level.

`Deep Intense Rock` vs `Edge Case: Sad but Energetic`: Both profiles included some high-energy songs near the top, but for different reasons. The rock profile was more convincing because it had a strong exact match in `Storm Runner`, while the edge-case profile showed how the recommender starts to look less human when the dataset does not contain a good example of the requested vibe.

## Experiment Notes

I tested one weight change by cutting the genre weight in half and doubling the energy weight. For the `High-Energy Pop` profile, `Rooftop Lights` moved above `Gym Hero`. That made the ranking more sensitive to energy closeness and mood, but it also made the system more willing to drift away from the user's favorite genre.
