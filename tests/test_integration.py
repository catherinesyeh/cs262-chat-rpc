import socket
import time
import sys
import os
import pytest
from contextlib import contextmanager
from helpers.ContextHelper import ContextHelper
from helpers.utils import wait_for_condition, write_to_log

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from client import config
from client.network.network_json import JSONChatClient
from client.network.network_wire import WireChatClient

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


@pytest.fixture(scope="function")
def test_context():
    """
    Set up a TestContext instance.
    """
    return ContextHelper()


@contextmanager
def client_connection():
    """
    Set up a ChatClient instance and connect to the server.
    """
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]
    use_json_protocol = client_config["use_json_protocol"]

    # Create a client based on the protocol
    if use_json_protocol:
        client = JSONChatClient(host, port, max_msg, max_users)
    else:
        client = WireChatClient(host, port, max_msg, max_users)

    try:
        yield client
    finally:
        client.close()
        time.sleep(1)  # Wait for server to close connection


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
def test_server_connection():
    """
    Test if the client can connect to the server.
    """
    with client_connection() as client:
        assert client.running == True, "Client failed to connect to server"


def test_lookup_nonexistent_user():
    """
    Test if the client can lookup a user that does not exist.
    """
    start_time = time.time()
    username = "new_user"

    with client_connection() as sender_client:
        sender_client.send_lookup_account(username)
        time.sleep(1)

        assert sender_client.bcrypt_prefix is None, "Lookup should fail for nonexistent user"
        bytes_sent = sender_client.bytes_sent
        bytes_received = sender_client.bytes_received
        protocol_type = "json" if isinstance(
            sender_client, JSONChatClient) else "wire"

    time_elapsed = time.time() - start_time
    write_to_log("test_lookup_nonexistent_user", protocol_type,
                 bytes_received, bytes_sent, time_elapsed)


def test_create_account():
    """
    Test if the client can create an account.
    """
    start_time = time.time()
    username = "new_user"
    password = "new_password"

    with client_connection() as sender_client:
        # Create account
        sender_client.send_create_account(username, password)
        time.sleep(1)

        # Now lookup should succeed
        sender_client.send_lookup_account(username)
        time.sleep(1)

        assert sender_client.bcrypt_prefix is not None, "Lookup should succeed for created user"
        bytes_sent = sender_client.bytes_sent
        bytes_received = sender_client.bytes_received
        protocol_type = "json" if isinstance(
            sender_client, JSONChatClient) else "wire"

    time_elapsed = time.time() - start_time
    write_to_log("test_create_account", protocol_type,
                 bytes_received, bytes_sent, time_elapsed)


def test_login():
    """
    Test if the client can login.
    """
    start_time = time.time()
    username = "new_user"
    password = "new_password"

    with client_connection() as sender_client:
        # See if account exists
        sender_client.send_lookup_account(username)
        time.sleep(1)

        # Create account if it doesn't exist
        if sender_client.bcrypt_prefix is None:
            sender_client.send_create_account(username, password)
            time.sleep(1)
        else:  # Login
            sender_client.send_login(username, password)
            time.sleep(1)

        assert sender_client.username == username, "Login failed: Username not set correctly"
        bytes_sent = sender_client.bytes_sent
        bytes_received = sender_client.bytes_received
        protocol_type = "json" if isinstance(
            sender_client, JSONChatClient) else "wire"

    time_elapsed = time.time() - start_time
    write_to_log("test_login", protocol_type,
                 bytes_received, bytes_sent, time_elapsed)


def test_list_accounts(test_context):
    """
    Test if the client can request a list of accounts from the server.

    :param test_context: TestContext instance
    """
    start_time = time.time()
    with client_connection() as sender:
        # Attach the callback to capture received messages
        sender.start_polling_messages(test_context.message_callback)

        sender.max_users = 2

        # Create some accounts first to ensure the list is not empty
        usernames = ["user1", "user2"]
        password = "test_password"

        for username in usernames:
            sender.send_create_account(username, password)
            time.sleep(1)

        # Request the list of accounts
        sender.send_list_accounts()
        time.sleep(1)

        # Check if the returned accounts contain the created users
        listed_usernames = [account[1] for account in test_context.accounts]

        assert len(
            listed_usernames) == sender.max_users, "List of accounts should be equal to max_users"

        # Send another request
        sender.last_offset_account_id = sender.max_users
        sender.send_list_accounts()
        time.sleep(1)

        # Check if returned account ids are correct
        ids = [account[0] for account in test_context.accounts]
        assert len(
            listed_usernames) == sender.max_users, "List of accounts should be equal to max_users"

        for id in ids:
            assert id > sender.last_offset_account_id, f"Account ID {id} should be greater than last_offset_account_id {sender.last_offset_account_id}"

        # Now try filtering
        filter_text = "user1"
        sender.last_offset_account_id = 0
        sender.send_list_accounts(filter_text)
        time.sleep(1)

        # Check if the returned accounts contain the created users
        listed_usernames = [account[1] for account in test_context.accounts]
        assert len(listed_usernames) == 1, "List of accounts should be equal to 1"

        assert usernames[0] in listed_usernames, f"New username {usernames[0]} not found in account list"

        bytes_sent = sender.bytes_sent
        bytes_received = sender.bytes_received
        protocol_type = "json" if isinstance(
            sender, JSONChatClient) else "wire"

    time_elapsed = time.time() - start_time
    write_to_log("test_list_accounts", protocol_type,
                 bytes_received, bytes_sent, time_elapsed)


def test_send_receive_message(test_context):
    """
    Test if the client can send and receive messages (synchronously).

    :param test_context: TestContext instance
    """
    start_time = time.time()
    with client_connection() as sender, client_connection() as receiver:
        # Set up the receiver
        receiver.start_polling_messages(test_context.message_callback)
        sender.start_polling_messages(test_context.message_callback)

        # Create sender account
        sender.send_create_account("test_sender", "test_password")
        time.sleep(1)

        # Create receiver account
        receiver.send_create_account("test_receiver", "test_password")
        time.sleep(1)

        # Send message from sender to receiver while receiver is logged in
        sender.send_message("test_receiver", "Hello, world!")
        time.sleep(1)

        # Check if message was received
        def check_message():
            return len(test_context.messages) == 1 and test_context.messages[0][1] == "test_sender" and test_context.messages[0][2] == "Hello, world!"

        assert wait_for_condition(
            check_message), "(1) Sync message not received in time"

        # Test long message
        long_message = "a" * 1000
        sender.send_message("test_receiver", long_message)
        time.sleep(1)

        # Check if long message was received
        def check_long_message():
            return len(test_context.messages) == 1 and test_context.messages[0][1] == "test_sender" and test_context.messages[0][2] == long_message

        assert wait_for_condition(
            check_long_message), "(2) Sync long message not received in time"

        # Log out receiver
        receiver.close()
        time.sleep(1)

        # Send multiple messages from sender to receiver while receiver is logged out
        num_messages = 3
        receiver.max_msg = num_messages - 1

        for i in range(num_messages):
            sender.send_message("test_receiver", f"Message {i}")
            time.sleep(1)
            assert test_context.msg_sent == True, "Message not sent"
            time.sleep(1)
            test_context.msg_sent = False

        # Restart the receiver
        receiver.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        receiver.connect()
        receiver.start_polling_messages(test_context.message_callback)

        # Log in receiver
        receiver.send_login("test_receiver", "test_password")
        time.sleep(1)

        # Request messages for receiver
        receiver.send_request_messages()

        # Check if messages were received
        def check_messages():
            return len(test_context.messages) == receiver.max_msg and all([msg[1] == "test_sender" for msg in test_context.messages])

        assert wait_for_condition(
            check_messages), "(3) Async messages not received in time"

        # Get the last message
        receiver.send_request_messages()

        def check_last_message():
            return len(test_context.messages) == 1 and test_context.messages[0][2] == f"Message {num_messages - 1}"

        assert wait_for_condition(
            check_last_message), "Last message not received in time"
        bytes_sent = sender.bytes_sent + receiver.bytes_sent
        bytes_received = sender.bytes_received + receiver.bytes_received
        protocol_type = "json" if isinstance(
            sender, JSONChatClient) else "wire"

    time_elapsed = time.time() - start_time
    write_to_log("test_send_receive_message", protocol_type,
                 bytes_received, bytes_sent, time_elapsed)


def test_delete_message(test_context):
    """
    Test if the client can delete a message.

    :param test_context: TestContext instance
    """
    start_time = time.time()
    with client_connection() as sender, client_connection() as receiver:
        # Set up the receiver
        receiver.start_polling_messages(test_context.message_callback)

        # Create sender account
        sender.send_create_account("test_sender1", "test_password")
        time.sleep(1)

        # Create receiver account
        receiver.send_create_account("test_receiver1", "test_password")
        time.sleep(1)

        # Send message from sender to receiver
        sender.send_message("test_receiver1", "Hello, world!")
        time.sleep(1)

        # Check if message was received
        # (should automatically be received by the receiver since they are logged in)
        def check_message():
            return len(test_context.messages) == 1 and test_context.messages[0][1] == "test_sender1" and test_context.messages[0][2] == "Hello, world!"

        assert wait_for_condition(
            check_message), "Message not received in time"

        # Delete the message
        receiver.send_delete_message([test_context.messages[0][0]])
        time.sleep(1)

        # Request messages for receiver
        receiver.send_request_messages()

        # Check if message was deleted
        def check_deleted_message():
            return test_context.msg_deleted

        assert wait_for_condition(
            check_deleted_message), "Message not deleted in time"
        bytes_sent = sender.bytes_sent + receiver.bytes_sent
        bytes_received = sender.bytes_received + receiver.bytes_received
        protocol_type = "json" if isinstance(
            sender, JSONChatClient) else "wire"

    time_elapsed = time.time() - start_time
    write_to_log("test_delete_message", protocol_type,
                 bytes_received, bytes_sent, time_elapsed)


def test_delete_account():
    """
    Test if the client can delete an account.
    """
    start_time = time.time()
    with client_connection() as sender:
        # Create account
        sender.send_create_account("test_user_to_delete", "test_password")
        time.sleep(1)

        # Delete account
        sender.send_delete_account()
        time.sleep(1)

        def check_deleted_account():
            return sender.thread is None

        # Check if account was deleted
        assert wait_for_condition(
            check_deleted_account), "Account not deleted in time"
        bytes_sent = sender.bytes_sent
        bytes_received = sender.bytes_received
        protocol_type = "json" if isinstance(
            sender, JSONChatClient) else "wire"

    time_elapsed = time.time() - start_time
    write_to_log("test_delete_account", protocol_type,
                 bytes_received, bytes_sent, time_elapsed)
