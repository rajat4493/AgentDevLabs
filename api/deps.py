from config.router import get_router_mode, RouterMode


def get_router_mode_dep() -> RouterMode:
    return get_router_mode()
