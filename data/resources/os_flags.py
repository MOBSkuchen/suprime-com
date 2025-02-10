import os


def get_bool_flag(name: str):
    return os.environ.get(name) == "true"


def set_bool_flag(name: str, value: bool):
    os.environ[name] = "true" if value else "false"


def get_flag(name: str):
    return os.environ.get(name)


def set_flag(name: str, value: str):
    os.environ[name] = value
