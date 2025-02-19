import socket
import threading
from abc import ABC, abstractmethod
import bcrypt


class ChatClient(ABC):
    """
    Base class to handles the client-side network communication for the chat application.
    """
    ### GENERAL FUNCTIONS ###

    def __init__(self, host, port, max_msg, max_users):
        """
        Initialize the client.

        :param host: Server host
        :param port: Server port
        :param max_msg: Maximum number of messages to display
        :param max_users: Maximum number of users to display
        """
        self.host = host  # Server host
        self.port = port  # Server port
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
        self.running = False  # Flag to indicate if the client is running
        self.thread = None  # Thread to listen for messages from the server

        self.max_msg = max_msg  # Maximum number of messages to display
        self.max_users = max_users  # Maximum number of users to display

        self.last_offset_account_id = 0  # Offset ID for pagination of accounts
        self.bcrypt_prefix = None  # Bcrypt prefix for password hashing
        self.username = None  # Username of the client
        self.message_callback = None  # Callback function to handle received messages

        self.bytes_sent = 0  # Number of bytes sent
        self.bytes_received = 0  # Number of bytes received

        print("[INITIALIZED] Client initialized")
        self.connect()

    def connect(self):
        """ 
        Establish a connection to the server.

        :return: True if connection is successful, False otherwise
        """
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"[CONNECTED] Connected to {self.host}:{self.port}")
        except Exception as e:
            return self.log_error(f"Could not connect to {self.host}:{self.port} - {e}", False)
        return True

    def start_listener(self, callback):
        """
        Start a thread to listen for messages from the server.

        :param callback: Callback function to handle received messages
        """
        self.message_callback = callback
        self.thread = threading.Thread(
            target=self.listen_for_messages, daemon=True)
        self.thread.start()

    def close(self):
        """
        Close the connection to the server.
        """
        print("CLOSING")
        if not self.running:
            return
        self.running = False
        if self.socket:
            try:
                # Properly close the socket
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except OSError:
                pass  # Ignore errors if the socket, is already closed
            self.socket = None

        # Don't try to join the thread if we're already in it
        if threading.current_thread() != self.thread and self.thread is not None:
            self.thread.join(timeout=1)

        print("[DISCONNECTED] Disconnected from server")

    ### TEMPLATE / ABSTRACT METHODS ###
    @abstractmethod
    def listen_for_messages(self):
        pass

    # MAIN OPERATIONS
    # (1) LOOKUP
    @abstractmethod
    def send_lookup_account(self, username):
        pass

    @abstractmethod
    def handle_lookup_account_response(self, payload=None):
        pass

    # (2) LOGIN
    @abstractmethod
    def send_login(self, username, password):
        pass

    @abstractmethod
    def handle_login_response(self, payload=None, success=None):
        pass

    # (3) CREATE ACCOUNT
    @abstractmethod
    def send_create_account(self, username, password):
        pass

    @abstractmethod
    def handle_create_account_response(self):
        pass

    # (4) LIST ACCOUNTS
    @abstractmethod
    def send_list_accounts(self, filter_text=""):
        pass

    @abstractmethod
    def handle_list_accounts_response(self, payload=None):
        pass

    # (5) SEND MESSAGE
    @abstractmethod
    def send_message(self, recipient, message):
        pass

    @abstractmethod
    def handle_send_message_response(self, payload=None):
        pass

    # (6) REQUEST MESSAGES
    @abstractmethod
    def send_request_messages(self):
        pass

    @abstractmethod
    def handle_request_messages_response(self, payload=None):
        pass

    # (7) DELETE MESSAGES
    @abstractmethod
    def send_delete_message(self, message_ids):
        pass

    @abstractmethod
    def handle_delete_message_response(self):
        pass

    # (8) DELETE ACCOUNT
    @abstractmethod
    def send_delete_account(self):
        pass

    @abstractmethod
    def handle_delete_account_response(self):
        pass

    ### ERROR HANDLING ###
    def log_error(self, message, return_value=None):
        """ 
        Helper method to log errors and return a default value. 

        :param message: Error message
        :param return_value: Default return value
        :return: Default return value
        """
        print(f"[ERROR] {message}")
        return return_value

    def is_not_connected(self):
        """
        Helper method to log a "not connected to server" error.

        :return: True if not connected, False otherwise
        """

        print(f"Running: {self.running}, Socket: {self.socket}")

        if not self.running or self.socket is None:
            self.log_error("Not connected to server")
            self.close()
            return True
        return False

    ### MISC HELPER FUNCTIONS ###
    def get_hashed_password_for_login(self, username, password):
        """
        Get the hashed password for login.

        :param username: Username
        :param password: Password
        :return: Hashed password
        """
        # Save username
        self.username = username

        # Lookup account
        salt = self.bcrypt_prefix
        if salt is None:
            return self.log_error("Account does not exist")

        # Otherwise, account exists
        # Hash the password using the cost and salt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_password

    def generate_hashed_password_for_create(self, username, password):
        """
        Generate a hashed password for creating an account.

        :param username: Username
        :param password: Password
        :return: Hashed password
        """
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        self.bcrypt_prefix = salt

        # store username
        self.username = username

        return hashed_password
