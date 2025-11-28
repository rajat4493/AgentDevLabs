from enum import Enum
import os


class RouterMode(str, Enum):
    BASELINE = "baseline"
    ENHANCED = "enhanced"


def get_router_mode() -> RouterMode:
    value = os.getenv("AGENTICLABS_ROUTER_MODE", RouterMode.BASELINE.value)
    try:
        return RouterMode(value.lower())
    except ValueError:
        return RouterMode.BASELINE
