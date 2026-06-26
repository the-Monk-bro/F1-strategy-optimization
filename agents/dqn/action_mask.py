import numpy as np


def get_action_mask(env):
    """
    Action mask for F1StrategyEnv.

    Actions:
        0 = stay out
        1 = pit soft
        2 = pit medium
        3 = pit hard
        4 = pit intermediate
        5 = pit wet

    True  = action allowed
    False = action blocked
    """

    mask = np.ones(6, dtype=bool)

    current_lap = env.state.current_lap
    max_laps = env.max_laps
    tyre_age = env.state.tyre_age
    current_compound = env.state.tyre_compound
    track_wetness = env.state.track_wetness

    # Staying out is always allowed.
    mask[0] = True

    # Do not pit in the first few laps on a dry track.
    if current_lap < 3 and track_wetness == 0:
        mask[1:] = False
        return mask

    # Do not pit again immediately after a pit stop.
    if tyre_age <= 2:
        mask[1:] = False
        return mask

    # Do not pit on the final lap or near-final lap.
    if current_lap >= max_laps - 1:
        mask[1:] = False
        return mask

    # Dry track: block intermediate and wet tyres.
    if track_wetness == 0:
        mask[4] = False
        mask[5] = False

    # Intermediate condition: prefer intermediate only.
    if 0 < track_wetness < 1.5:
        mask[1] = False
        mask[2] = False
        mask[3] = False
        mask[5] = False

    # Heavy wet condition: prefer wet only.
    if track_wetness >= 1.5:
        mask[1] = False
        mask[2] = False
        mask[3] = False
        mask[4] = False
        mask[5] = True

    # Do not pit to the same compound.
    same_compound_action = current_compound + 1
    if 1 <= same_compound_action <= 5:
        mask[same_compound_action] = False

    # Safety fallback: if somehow all pit actions are blocked, stay out remains valid.
    mask[0] = True

    return mask