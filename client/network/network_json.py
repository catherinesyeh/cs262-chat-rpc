
import json
import threading
from .network import ChatClient


class JSONChatClient(ChatClient):
    """
    Handles the client-side network communication for the chat application using a JSON protocol.
    (Subclass of ChatClient)
    """

    def listen_for_messages(self):
        """
        Listen for messages from the server and store them.
        """
        print("[CLIENT] Listening for messages...")

        buffer = b""  # Buffer to store incoming data for JSON messages
        while self.running:
            try:
                # Parse JSON messages and store them
                # Read available bytes in chunks
                chunk = self.socket.recv(1024)
                if not chunk:
                    print("[DISCONNECTED] Disconnected from server")
                    self.close()
                    break
                buffer += chunk
                while b'\n' in buffer:  # Process each complete JSON message
                    message, buffer = buffer.split(b'\n', 1)
                    threading.Thread(target=self.handle_json_response, args=(
                        message.decode("utf-8"),), daemon=True).start()

            except (OSError, ConnectionError) as e:
                self.log_error(
                    f"Socket closed or connection reset. Stopping listener: {e}")
                break

            except Exception as e:
                self.log_error(f"Error receiving messages: {e}")
                self.close()
                break

    ### MAIN OPERATIONS ###
    # (1) LOOKUP
    def send_lookup_account(self, username):
        """
        OPERATION 1: Send a lookup account message to the server (LOOKUP_USER).

        :param username: Username to lookup
        """
        if self.is_not_connected():
            return

        if not isinstance(username, str) or not username:
            return self.log_error("Invalid username", False)

        self.send_json_request("LOOKUP_USER", {"username": username})

    def handle_lookup_account_response(self, payload):
        """
        Handle the JSON response from the server for the LOOKUP_USER operation (1).

        :param payload: JSON payload
        """
        print("[LOOKUP] Handling JSON response...")
        exists = payload["exists"]
        self.bcrypt_prefix = payload["bcrypt_prefix"].encode(
            "utf-8") if exists else None

        # Notify UI of lookup result
        if self.message_callback:
            self.message_callback(f"LOOKUP_USER:{int(exists)}")

    # (2) LOGIN
    def send_login(self, username, password):
        """
        OPERATION 2: Send a login message to the server (LOGIN).
        Assumes LOOKUP_USER has been called and account exists.

        :param username: Username to login
        :param password: Password to login
        """
        if self.is_not_connected():
            return

        if not isinstance(username, str) or not username:
            return self.log_error("Invalid username", False)

        if not isinstance(password, str) or not password:
            return self.log_error("Invalid password", False)

        hashed_password = self.get_hashed_password_for_login(
            username, password)

        self.send_json_request(
            "LOGIN", {"username": username, "password_hash": hashed_password.decode('utf-8')})

    def handle_login_response(self, payload, success):
        """
        Handle the JSON response from the server for the LOGIN operation (2).

        :param payload: JSON payload
        :param success: Success flag
        :return: Tuple of success flag and unread message count if login is successful, False otherwise
        """
        # Notify UI of login result
        print("[LOGIN] Handling JSON response...")
        unread_messages = payload.get("unread_messages", 0)
        print(f"[LOGIN] Unread messages: {unread_messages}")
        if self.message_callback:
            self.message_callback(f"LOGIN:{int(success)}:{unread_messages}")
        return True, unread_messages if success else False

    # (3) CREATE ACCOUNT
    def send_create_account(self, username, password):
        """
        OPERATION 3: Create a new account (CREATE_ACCOUNT).
        Assumes LOOKUP_USER has been called and account does not exist.

        :param username: Username to create
        :param password: Password to create
        """
        if self.is_not_connected():
            return

        if not isinstance(username, str) or not username:
            return self.log_error("Invalid username", False)

        if not isinstance(password, str) or not password:
            return self.log_error("Invalid password", False)

        hashed_password = self.generate_hashed_password_for_create(
            username, password)

        self.send_json_request("CREATE_ACCOUNT", {
                               "username": username, "password_hash": hashed_password.decode('utf-8')})

    def handle_create_account_response(self):
        """
        Handle the JSON response from the server for the CREATE_ACCOUNT operation (3).
        """
        # Notify UI of account creation result
        if self.message_callback:
            self.message_callback(f"CREATE_ACCOUNT:{1}")  # success

        if not self.username:
            self.log_error("Username not set")

    # (4) LIST ACCOUNTS
    def send_list_accounts(self, filter_text=""):
        """
        OPERATION 4: Request a list of accounts from the server (LIST_ACCOUNTS).

        :param filter_text: Filter text to search for
        """
        if self.is_not_connected():
            return

        if not isinstance(filter_text, str):
            return self.log_error("Invalid filter text", False)

        # Determine the offset ID based on the direction user wants to go
        offset_id = self.last_offset_account_id

        print("[ACCOUNTS] Offset ID:", offset_id, ", Filter:",
              filter_text, ", Max users:", self.max_users)

        self.send_json_request("LIST_ACCOUNTS", {
                               "maximum_number": self.max_users, "offset_account_id": offset_id, "filter_text": filter_text})

    def handle_list_accounts_response(self, payload):
        """
        Handle the JSON response from the server for the LIST_ACCOUNTS operation (4).

        :param payload: JSON payload
        :return: List of accounts
        """
        print("[ACCOUNTS] Handling JSON response...")
        account_data = payload["accounts"]
        accounts = [(account["id"], account["username"])
                    for account in account_data]
        print(f"[ACCOUNTS] Retrieved {len(accounts)} accounts")

        if self.message_callback:  # Notify UI of user list update
            self.message_callback(f"LIST_ACCOUNTS:{json.dumps(accounts)}")
        return accounts

    # (5) SEND MESSAGE
    def send_message(self, recipient, message):
        """
        OPERATION 5: Send a message to the server (SEND_MESSAGE).

        :param recipient: Recipient of the message
        :param message: Message to send
        """
        if self.is_not_connected():
            return

        if not isinstance(recipient, str) or not recipient:
            return self.log_error("Invalid recipient", False)

        if not isinstance(message, str) or not message:
            return self.log_error("Invalid message", False)

        self.send_json_request(
            "SEND_MESSAGE", {"recipient": recipient, "message": message})

    def handle_send_message_response(self, payload):
        """
        Handle the JSON response from the server for the SEND_MESSAGE operation (5).

        :param payload: JSON payload
        :return: True if message is sent successfully + message ID, False otherwise
        """
        message_id = payload["message_id"]
        print(f"[MESSAGE SENT] Message ID: {message_id}")
        # Notify UI of message sent
        if self.message_callback:
            self.message_callback(f"SEND_MESSAGE:{1}")  # success
        return True, message_id  # Return the message ID

    # (6) REQUEST MESSAGES
    def send_request_messages(self):
        """
        OPERATION 6: Request unread messages from the server (REQUEST_MESSAGES).
        """
        if self.is_not_connected():
            return

        self.send_json_request("REQUEST_MESSAGES", {
                               "maximum_number": self.max_msg})

    def handle_request_messages_response(self, payload):
        """
        Handle the JSON response from the server for the REQUEST_MESSAGES operation (6).

        :param payload: JSON payload
        :return: List of messages
        """
        message_data = payload["messages"]
        messages = [(message["id"], message["sender"], message["message"])
                    for message in message_data]
        # print(f"[MESSAGES] Retrieved {len(messages)} messages")
        # Notify UI of received messages
        if self.message_callback:
            self.message_callback(f"REQUEST_MESSAGES:{json.dumps(messages)}")
        return messages

    # (7) DELETE MESSAGES
    def send_delete_message(self, message_ids):
        """
        OPERATION 7: Delete messages from the server (DELETE_MESSAGES).

        :param message_ids: List of message IDs to delete
        """
        if self.is_not_connected():
            return

        if not isinstance(message_ids, list) or not message_ids or not all(isinstance(i, int) for i in message_ids):
            return self.log_error("Invalid message IDs", False)

        num_messages = len(message_ids)
        if num_messages == 0:
            return self.log_error("No messages to delete", False)

        self.send_json_request("DELETE_MESSAGES", {"message_ids": message_ids})

    def handle_delete_message_response(self):
        """
        Handle the JSON response from the server for the DELETE_MESSAGES operation (7).

        :return: True if messages are deleted successfully, False otherwise
        """
        print(f"[MESSAGE DELETED] Messages deleted successfully")
        # Notify UI of message deletion
        if self.message_callback:
            self.message_callback(f"DELETE_MESSAGES:{1}")  # success
        return True

    # (8) DELETE ACCOUNT
    def send_delete_account(self):
        """
        OPERATION 8: Delete the account from the server (DELETE_ACCOUNT).
        """
        if self.is_not_connected():
            return

        print("[ACCOUNT DELETION] Deleting account...")
        self.send_json_request("DELETE_ACCOUNT")

    def handle_delete_account_response(self):
        """
        Handle the JSON response from the server for the DELETE_ACCOUNT operation (8).

        :return: True if account is deleted successfully
        """
        print("[ACCOUNT DELETED] Account deleted successfully (JSON)")
        # Notify UI of account deletion
        if self.message_callback:
            self.message_callback(f"DELETE_ACCOUNT:{1}")  # success
        return True

    ### HELPERS ###
    def send_json_request(self, operation, payload=None):
        """
        Send a request to the server using the JSON protocol
a
        :param operation: Operation name
        :param payload: Payload data
        """
        if not isinstance(operation, str) or not operation:
            return self.log_error("Invalid operation", False)

        request = (json.dumps(
            {"operation": operation, "payload": payload or {}}) + '\n').encode("utf-8")
        self.bytes_sent += len(request)
        print("[DEBUG] Sending JSON request:", request)
        self.socket.send(request)

    def handle_json_response(self, message):
        """ 
        Handle JSON responses from the server.

        :param message: JSON message
        :return: True if the message is handled successfully, False otherwise
        """
        if not isinstance(message, str) or not message:
            return self.log_error("Invalid message", False)

        self.bytes_received += len(message)
        try:
            parsed_message = json.loads(message)
            print("[DEBUG] Parsed message:", parsed_message)
            operation = parsed_message.get("operation")
            success = parsed_message.get("success")
            payload = parsed_message.get("payload", {})
            if not success:
                message = parsed_message.get("message", "")
                # Log error message if operation failed
                return self.log_error(f"Operation {operation} failed: {message}")

            # Else, handle the JSON response based on the operation
            if operation == "LOOKUP_USER":
                if payload is None:
                    return self.log_error(f"Operation {operation} failed: No payload found")
                return self.handle_lookup_account_response(payload)
            elif operation == "LOGIN":
                if payload is None:
                    return self.log_error(f"Operation {operation} failed: No payload found")
                return self.handle_login_response(payload, success)
            elif operation == "CREATE_ACCOUNT":
                return self.handle_create_account_response()
            elif operation == "LIST_ACCOUNTS":
                if payload is None:
                    return self.log_error(f"Operation {operation} failed: No payload found")
                return self.handle_list_accounts_response(payload)
            elif operation == "SEND_MESSAGE":
                if payload is None:
                    return self.log_error(f"Operation {operation} failed: No payload found")
                return self.handle_send_message_response(payload)
            elif operation == "REQUEST_MESSAGES":
                if payload is None:
                    return self.log_error(f"Operation {operation} failed: No payload found")
                return self.handle_request_messages_response(payload)
            elif operation == "DELETE_MESSAGES":
                return self.handle_delete_message_response()
            elif operation == "DELETE_ACCOUNT":
                # Note: this is potentially not needed as the socket will be automatically disconnected
                return self.handle_delete_account_response()
            else:
                return self.log_error(f"Unknown operation: {operation}")
        except Exception as e:
            return self.log_error(f"Error handling JSON response: {e}")
