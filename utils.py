import random
import numpy as np
import torch


def set_global_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def validate_state(state, expected_size: int) -> np.ndarray:
    state_array = np.asarray(state, dtype=np.float32).flatten()

    if state_array.shape != (expected_size,):
        raise ValueError(
            f"Invalid state shape. Expected {(expected_size,)}, "
            f"got {state_array.shape}. State received: {state_array}"
        )

    return state_array


def validate_action_mask(action_mask, action_size: int) -> np.ndarray:
    if action_mask is None:
        return np.ones(action_size, dtype=np.bool_)

    mask_array = np.asarray(action_mask, dtype=np.bool_).flatten()

    if mask_array.shape != (action_size,):
        raise ValueError(
            f"Invalid action mask shape. Expected {(action_size,)}, "
            f"got {mask_array.shape}. Mask received: {mask_array}"
        )

    if not mask_array.any():
        raise ValueError(
            "Invalid action mask. At least one action must be valid."
        )

    return mask_array