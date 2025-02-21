import time
from BytesTrackingInterceptor import BytesTrackingInterceptor
import grpc
import threading
import bcrypt
from proto import chat_pb2, chat_pb2_grpc


class ChatClient():
    """
    Base class to handles the client-side network communication for the chat application,
    implemeted with gRPC.
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
        channel_str = f"{host}:{port}"
        base_channel = grpc.insecure_channel(
            channel_str)  # Create a base channel
        # Interceptor to track bytes sent/received
        self.interceptor = BytesTrackingInterceptor(self)
        # Create a channel with the interceptor
        self.channel = grpc.intercept_channel(base_channel, self.interceptor)
        self.stub = chat_pb2_grpc.ChatServiceStub(
            self.channel)  # Create a stub with the channel and interceptor

        self.session_key = None  # Session key for authenticated requests
        self.running = False  # Flag to control polling thread
        self.thread = None  # Thread to poll for messages

        self.max_msg = max_msg  # Maximum number of messages to display
        self.max_users = max_users  # Maximum number of users to display

        self.last_offset_account_id = 0  # Offset ID for pagination of accounts
        self.username = None  # Username of the client
        self.bcrypt_prefix = None  # Bcrypt prefix for password hashing
        self.on_messages_updated = None  # Callback function to update messages

        self.bytes_sent = 0  # Number of bytes sent
        self.bytes_received = 0  # Number of bytes received

        print("[INITIALIZED] Client initialized")

    def set_message_update_callback(self, callback):
        """
        Set a callback function to update messages.

        :param callback: Callback function
        """
        self.on_messages_updated = callback

    def start_polling_messages(self, poll_interval=5):
        """
        Start a thread to listen for messages from the server.

        :param poll_interval: Polling interval
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(
                target=self.poll_messages, args=(poll_interval,), daemon=True)
            self.thread.start()

    def poll_messages(self, poll_interval):
        """
        Poll for messages from the server.

        :param poll_interval: Polling interval
        """
        while self.running:
            self.request_messages()

            # Sleep for the polling interval
            time.sleep(poll_interval)

    def stop_polling_messages(self):
        """
        Stop the thread listening for messages.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("[STOPPED] Polling messages")

    # MAIN OPERATIONS
    # (1) LOOKUP
    def account_lookup(self, username):
        """
        Lookup an account by username.

        :param username: Username
        :return: True if the account exists, False otherwise
        """
        request = chat_pb2.AccountLookupRequest(username=username)
        response = self.stub.AccountLookup(request)
        print(
            f"[LOOKUP] Exists: {response.exists}, Prefix: {response.bcrypt_prefix}")
        if response.exists:
            self.bcrypt_prefix = response.bcrypt_prefix
        return response.exists

    # (2) LOGIN
    def login(self, username, password):
        """
        Login to the server.

        :param username: Username
        :param password: Password
        :return: True + number of unread messages if login is successful, False otherwise
        """
        hashed_password = self.get_hashed_password_for_login(password)
        request = chat_pb2.LoginCreateRequest(
            username=username, password_hash=hashed_password)
        response = self.stub.Login(request)

        if response.success:  # If login is successful, store the session key and username
            print(
                f"[LOGIN] Session key: {response.session_key}, Unread messages: {response.unread_messages}")
            self.session_key = response.session_key
            self.username = username
            self.start_polling_messages()
            return response.success, response.unread_messages
        # Else, log the error and return False
        return self.log_error("Login failed", False)

    # (3) CREATE ACCOUNT
    def create_account(self, username, password):
        """
        Create an account on the server.

        :param username: Username
        :param password: Password
        :return: True if account creation is successful, False otherwise
        """
        hashed_password = self.generate_hashed_password_for_create(password)
        request = chat_pb2.LoginCreateRequest(
            username=username, password_hash=hashed_password)
        response = self.stub.CreateAccount(request)
        if response.success:
            print(
                f"[CREATE ACCOUNT] Success: {response.success}, Session key: {response.session_key}")
            self.session_key = response.session_key
            self.username = username
            self.start_polling_messages()
        else:
            self.log_error("Account creation failed")
        return response.success

    # (4) LIST ACCOUNTS
    def list_accounts(self, filter_text=""):
        """
        List accounts on the server.

        :param filter_text: Filter text
        :return: List of accounts
        """
        if not self.session_key:
            return self.log_error("No session key available")

        request = chat_pb2.ListAccountsRequest(
            session_key=self.session_key, maximum_number=self.max_users, offset_account_id=self.last_offset_account_id, filter_text=filter_text)
        response = self.stub.ListAccounts(request)
        accounts = [(account.id, account.username)
                    for account in response.accounts]
        print(f"[LIST ACCOUNTS] Accounts: {accounts}")
        return accounts

    # (5) SEND MESSAGE
    def send_message(self, recipient, message):
        """
        Send a message to a recipient.

        :param recipient: Recipient
        :param message: Message
        :return: True if message is sent successfully, False otherwise
        """
        if not self.session_key:
            return self.log_error("No session key available")

        request = chat_pb2.SendMessageRequest(
            session_key=self.session_key, recipient=recipient, message=message)
        response = self.stub.SendMessage(request)
        print(f"[MESSAGE SENT] ID: {response.id}")
        return True

    # (6) REQUEST MESSAGES
    def request_messages(self):
        """
        Request messages from the server.

        :return: List of messages
        """
        if not self.session_key:
            return self.log_error("No session key available")

        request = chat_pb2.RequestMessagesRequest(
            session_key=self.session_key, maximum_number=self.max_msg)
        response = self.stub.RequestMessages(request)
        messages = [(message.id, message.sender,
                     message.message) for message in response.messages]
        if len(messages) > 0:
            print(f"[RECEIVED MESSAGES] Messages: {messages}")
            # send callback
            if self.on_messages_updated:
                self.on_messages_updated(messages)
        return messages

    # (7) DELETE MESSAGES
    def delete_message(self, message_ids):
        """
        Delete messages from the server.

        :param message_ids: List of message IDs
        :return: True if messages are deleted successfully, False otherwise
        """
        if not self.session_key:
            return self.log_error("No session key available")

        request = chat_pb2.DeleteMessagesRequest(
            session_key=self.session_key, id=message_ids)
        self.stub.DeleteMessages(request)
        print(f"[DELETED MESSAGES] IDs: {message_ids}")
        return True

    # (8) DELETE ACCOUNT
    def delete_account(self):
        """
        Delete the account from the server.

        :return: True if account is deleted successfully, False otherwise
        """
        if not self.session_key:
            return self.log_error("No session key available")

        request = chat_pb2.DeleteAccountRequest(
            session_key=self.session_key)
        self.stub.DeleteAccount(request)
        print(f"[DELETED ACCOUNT] Session key: {self.session_key}")
        self.session_key = None
        return True

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

    ### MISC HELPER FUNCTIONS ###
    def get_hashed_password_for_login(self, password):
        """
        Get the hashed password for login.

        :param password: Password
        :return: Hashed password
        """
        if not self.bcrypt_prefix:
            self.log_error("No bcrypt prefix available")
            return None

        hashed_password = bcrypt.hashpw(
            password.encode(), self.bcrypt_prefix.encode()).decode()
        return hashed_password

    def generate_hashed_password_for_create(self, password):
        """
        Generate the hashed password for account creation.

        :param password: Password
        :return: Hashed password
        """
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
        self.bcrypt_prefix = salt.decode()
        return hashed_password
