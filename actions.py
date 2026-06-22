from enum import IntEnum


class F1Action(IntEnum):
    STAY_OUT = 0
    PIT_SOFT = 1
    PIT_MEDIUM = 2
    PIT_HARD = 3


ACTION_NAMES = {
    F1Action.STAY_OUT: "STAY_OUT",
    F1Action.PIT_SOFT: "PIT_SOFT",
    F1Action.PIT_MEDIUM: "PIT_MEDIUM",
    F1Action.PIT_HARD: "PIT_HARD",
}


def action_to_name(action: int) -> str:
    try:
        return ACTION_NAMES[F1Action(action)]
    except ValueError:
        return f"UNKNOWN_ACTION_{action}"


def action_to_tyre_compound(action: int):
    """
    Returns tyre compound only for pit actions.

    Suggested encoding:
    0 = SOFT
    1 = MEDIUM
    2 = HARD
    """

    if action == F1Action.PIT_SOFT:
        return 0

    if action == F1Action.PIT_MEDIUM:
        return 1

    if action == F1Action.PIT_HARD:
        return 2

    return None