import json

CONFIG_FILE = '../config.json'


def get_config():
    """
    Load the configuration from the config file.

    Returns:
        dict: The configuration values (host, port, max_msg)
    """
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    host = config["SERVER_HOST"]
    port = config["SERVER_PORT"]
    max_msg = config["MAX_MSG_TO_DISPLAY"]
    max_users = config["MAX_USERS_TO_DISPLAY"]

    return {"host": host, "port": port, "max_msg": max_msg, "max_users": max_users}
