import json

class ContextHelper:
    """
    Helper class for setting up a test context for integration tests.
    """
    def __init__(self):
        self.clear()
    
    def clear(self):
        self.messages = []
        self.accounts = []
        self.msg_sent = False
        self.msg_deleted = False
    
    def message_callback(self, msg):
        print(f"[CALLBACK] Received message: {msg}")

        if msg.startswith("SEND_MESSAGE:"):
            success = int(msg.split(":")[1])
            self.msg_sent = success == 1
        elif msg.startswith("REQUEST_MESSAGES:"):
            msg_data = json.loads(msg.split(":", 1)[1])
            self.messages = msg_data
        elif msg.startswith("LIST_ACCOUNTS:"):
            account_data = json.loads(msg.split(":", 1)[1])
            self.accounts = account_data
        elif msg.startswith("DELETE_MESSAGES:"):
            success = int(msg.split(":")[1])
            self.msg_deleted = success == 1
