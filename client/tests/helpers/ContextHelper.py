import json


class ContextHelper:
    """
    Helper class for setting up a test context for integration tests.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        self.messages = []

    def message_callback(self, msgs):
        print(f"[CALLBACK] Received messages: {msgs}")
        self.messages = msgs
