import struct
from unittest.mock import patch, MagicMock
import pytest
import os
import sys
import json

from helpers.utils import wait_for_condition

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from client.network.network_wire import WireChatClient
from client import config

# Test the WireChatClient class


@pytest.fixture(scope="function")
def mock_client():
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]
    with patch.object(WireChatClient, 'connect', return_value=True):
        # prevent actual connection to the server
        client = WireChatClient(host, port, max_msg, max_users)
        client.socket = MagicMock()
        client.running = True
        client.message_callback = MagicMock()
        client.listen_for_messages = MagicMock()
        client.start_listener(client.message_callback)
        return client


### BASIC TESTS ###


def test_client_connect(mock_client):
    """
    Test the connect method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    assert mock_client.running == True, "Client should be running"


def test_client_close(mock_client):
    """
    Test the close method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    mock_client.close()
    assert mock_client.socket is None, "Client socket should be None"


### SENDING REQUESTS ###


def test_send_lookup_account(mock_client):
    """
    Test the send_lookup_account method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    user = "test_user"

    expected_request = struct.pack("!B B", 1, len(user)) + user.encode("utf-8")

    # Call the send_lookup_account method
    mock_client.send_lookup_account("test_user")

    # Check if the sendall method was called with the expected request
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_username", ["", None, 123])
def test_send_lookup_account_invalid_username(mock_client, invalid_username):
    """
    Test the send_lookup_account method of the WireChatClient class with an invalid username

    :param mock_client: A WireChatClient instance
    :param invalid_username: An invalid username
    """
    assert mock_client.send_lookup_account(
        invalid_username) == False, "Invalid username should return False"


def test_send_create_account(mock_client):
    """
    Test the create_account method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    user = "test_user"
    password = "test_password"

    hashed_password = b"$2b$12$1Q7e4wto"

    # Mock password hashing
    with patch.object(mock_client, 'generate_hashed_password_for_create', return_value=hashed_password):
        mock_client.send_create_account(user, password)
        expected_request = struct.pack("!B B", 3, len(user)) + \
            user.encode("utf-8")
        expected_request += struct.pack("!B",
                                        len(hashed_password)) + hashed_password
        mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_username", ["", None, 123])
def test_send_create_account_invalid_username(mock_client, invalid_username):
    """
    Test the create_account method of the WireChatClient class with an invalid username

    :param mock_client: A WireChatClient instance
    :param invalid_username: An invalid username
    """
    assert mock_client.send_create_account(
        invalid_username, "test_password") == False, "Invalid username should return False"


@pytest.mark.parametrize("invalid_password", ["", None, 123])
def test_send_create_account_invalid_password(mock_client, invalid_password):
    """
    Test the create_account method of the WireChatClient class with an invalid password

    :param mock_client: A WireChatClient instance
    :param invalid_password: An invalid password
    """
    assert mock_client.send_create_account(
        "test_user", invalid_password) == False, "Invalid password should return False"


def test_send_login(mock_client):
    """
    Test the send_login method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    user = "test_user"
    password = "test_password"

    hashed_password = b"$2b$12$1Q7e4wto"

    # Mock password hashing
    with patch.object(mock_client, 'get_hashed_password_for_login', return_value=hashed_password):
        mock_client.send_login(user, password)
        expected_request = struct.pack("!B B", 2, len(user)) + \
            user.encode("utf-8")
        expected_request += struct.pack("!B",
                                        len(hashed_password)) + hashed_password
        mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_username", ["", None, 123])
def test_send_login_invalid_username(mock_client, invalid_username):
    """
    Test the send_login method of the WireChatClient class with an invalid username

    :param mock_client: A WireChatClient instance
    :param invalid_username: An invalid username
    """
    assert mock_client.send_login(
        invalid_username, "test_password") == False, "Invalid username should return False"


@pytest.mark.parametrize("invalid_password", ["", None, 123])
def test_send_login_invalid_password(mock_client, invalid_password):
    """
    Test the send_login method of the WireChatClient class with an invalid password

    :param mock_client: A WireChatClient instance
    :param invalid_password: An invalid password
    """
    assert mock_client.send_login(
        "test_user", invalid_password) == False, "Invalid password should return False"


def test_send_list_accounts(mock_client):
    """
    Test the send_list_accounts method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    filter_text = "test_filter"

    mock_client.send_list_accounts(filter_text)

    expected_request = struct.pack("!B B I B", 4, mock_client.max_users,
                                   mock_client.last_offset_account_id, len(filter_text))
    expected_request += filter_text.encode("utf-8")
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_filter_text", [None, 123])
def test_send_list_accounts_invalid_filter_text(mock_client, invalid_filter_text):
    """
    Test the send_list_accounts method of the WireChatClient class with an invalid filter text

    :param mock_client: A WireChatClient instance
    :param invalid_filter_text: An invalid filter text
    """
    assert mock_client.send_list_accounts(
        invalid_filter_text) == False, "Invalid filter text should return False"


def test_send_message(mock_client):
    """
    Test the send_message method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    recipient = "test_recipient"
    message = "test_message"

    mock_client.send_message(recipient, message)

    message_bytes = message.encode("utf-8")
    expected_request = struct.pack("!B B", 5, len(
        recipient)) + recipient.encode("utf-8")
    expected_request += struct.pack("!H", len(message_bytes)) + message_bytes
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_recipient", ["", None, 123])
def test_send_message_invalid_recipient(mock_client, invalid_recipient):
    """
    Test the send_message method of the WireChatClient class with an invalid recipient

    :param mock_client: A WireChatClient instance
    """
    assert mock_client.send_message(
        invalid_recipient, "test_message") == False, "Invalid recipient should return False"


@pytest.mark.parametrize("invalid_message", ["", None, 123])
def test_send_message_invalid_message(mock_client, invalid_message):
    """
    Test the send_message method of the WireChatClient class with an invalid message

    :param mock_client: A WireChatClient instance
    """
    assert mock_client.send_message(
        "test_recipient", invalid_message) == False, "Invalid message should return False"


def test_send_request_messages(mock_client):
    """
    Test the send_request_messages method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    mock_client.send_request_messages()
    expected_request = struct.pack("!B B", 6, mock_client.max_msg)
    mock_client.socket.send.assert_called_with(expected_request)


def test_send_delete_message(mock_client):
    """
    Test the send_delete_message method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    message_ids = [1, 2, 3]

    mock_client.send_delete_message(message_ids)
    expected_request = struct.pack("!B B", 7, len(message_ids))
    for message_id in message_ids:
        expected_request += struct.pack("!I", message_id)
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_message_ids", ["", None, 123])
def test_send_delete_message_invalid_message_ids(mock_client, invalid_message_ids):
    """
    Test the send_delete_message method of the WireChatClient class with invalid message ids

    :param mock_client: A WireChatClient instance
    """
    assert mock_client.send_delete_message(
        invalid_message_ids) == False, "Invalid message ids should return False"


def test_send_delete_account(mock_client):
    """
    Test the send_delete_account method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    mock_client.send_delete_account()
    expected_request = struct.pack("!B", 8)
    mock_client.socket.send.assert_called_with(expected_request)

### HANDLING RESPONSES ###


def test_lookup_account(mock_client):
    """
    Test the handle_lookup_account_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing successful response
    # 1 byte exists + 29 bytes salt

    exists = struct.pack("!B", 1)
    salt = b"$2b$12$abcdefghijklmnopqrstuv"

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[exists, salt, b""])

    mock_client.handle_lookup_account_response()

    mock_client.message_callback.assert_called_with(
        "LOOKUP_USER:1")


def test_lookup_account_not_found(mock_client):
    """
    Test the handle_lookup_account_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing not found response
    # 1 byte does not exist

    exists = struct.pack("!B", 0)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[exists, b""])

    mock_client.handle_lookup_account_response()

    mock_client.message_callback.assert_called_with(
        "LOOKUP_USER:0")


def test_create_account(mock_client):
    """
    Test the handle_create_account_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing successful response
    # 1 byte success

    success = struct.pack("!B", 1)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[success, b""])

    mock_client.handle_create_account_response()

    mock_client.message_callback.assert_called_with(
        "CREATE_ACCOUNT:1")


def test_create_account_failure(mock_client):
    """
    Test the handle_create_account_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing failure response
    # 1 byte failure

    failure = struct.pack("!B", 0)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[failure, b""])

    mock_client.handle_create_account_response()

    mock_client.message_callback.assert_called_with(
        "CREATE_ACCOUNT:0")


def test_login(mock_client):
    """
    Test the handle_login_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing successful response
    # 1 byte success + 2 bytes unread count

    success = struct.pack("!B", 1)
    unread_count = struct.pack("!H", 10)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[success, unread_count, b""])

    mock_client.handle_login_response()

    mock_client.message_callback.assert_called_with(
        "LOGIN:1:10")


def test_login_failure(mock_client):
    """
    Test the handle_login_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing failure response
    # 1 byte failure

    failure = struct.pack("!B", 0)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[failure, b""])

    mock_client.handle_login_response()

    mock_client.message_callback.assert_called_with(
        "LOGIN:0:0")


def test_list_accounts(mock_client):
    """
    Test the handle_list_accounts_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing successful response
    # 1 byte num_accounts

    num_accounts = struct.pack("!B", 2)

    # for each account: 4 bytes id + 1 byte username length + string
    account1 = struct.pack("!I B", 1, 9)
    account1_user = b"test_user"
    account2 = struct.pack("!I B", 2, 10)
    account2_user = b"test_user2"

    accounts = [
        [1, "test_user"],
        [2, "test_user2"]
    ]

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[num_accounts, account1, account1_user, account2, account2_user, b""])

    mock_client.handle_list_accounts_response()

    mock_client.message_callback.assert_called_with(
        f"LIST_ACCOUNTS:{json.dumps(accounts)}")


def test_list_accounts_empty(mock_client):
    """
    Test the handle_list_accounts_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing empty response
    # 1 byte num_accounts

    num_accounts = struct.pack("!B", 0)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[num_accounts, b""])

    mock_client.handle_list_accounts_response()

    mock_client.message_callback.assert_called_with(
        "LIST_ACCOUNTS:[]")


def test_send_message_response(mock_client):
    """
    Test the handle_send_message_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing successful response
    # 1 byte success + 4 bytes message_id

    expected = struct.pack("!B I", 1, 123)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[expected, b""])

    mock_client.handle_send_message_response()

    mock_client.message_callback.assert_called_with(
        "SEND_MESSAGE:1")


def test_send_message_response_fail(mock_client):
    """
    Test the handle_send_message_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing failure response
    # 1 byte failure

    expected = struct.pack("!B", 0)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[expected, b""])

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        mock_client.handle_send_message_response()

        mock_log_error.assert_called_with(
            "SEND_MESSAGE Invalid response from server", False)


def test_request_messages(mock_client):
    """
    Test the handle_request_messages_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # 1 byte num_messages
    num_messages = struct.pack("!B", 2)

    # for each message: 4 bytes message_id + 1 byte sender length + string + 2 bytes message length + string
    message_1 = struct.pack("!I", 1)
    message_1_user_len = struct.pack("!B", 9)
    message_1_user = b"test_user"
    message_1_message = struct.pack("!H", 8)
    message_1_message_text = b"test_msg"
    message_2 = struct.pack("!I", 2)
    message_2_user_len = struct.pack("!B", 10)
    message_2_user = b"test_user2"
    message_2_message = struct.pack("!H", 9)
    message_2_message_text = b"test_msg2"

    messages = [
        (1, "test_user", "test_msg"),
        (2, "test_user2", "test_msg2")
    ]

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[num_messages, message_1, message_1_user_len, message_1_user, message_1_message, message_1_message_text,
                     message_2, message_2_user_len, message_2_user, message_2_message, message_2_message_text, b""])

    mock_client.handle_request_messages_response()

    mock_client.message_callback.assert_called_with(
        f"REQUEST_MESSAGES:{json.dumps(messages)}")


def test_request_messages_empty(mock_client):
    """
    Test the handle_request_messages_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # testing empty response
    # 1 byte num_messages

    num_messages = struct.pack("!B", 0)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[num_messages, b""])

    mock_client.handle_request_messages_response()

    mock_client.message_callback.assert_called_with(
        "REQUEST_MESSAGES:[]")


def test_delete_message(mock_client):
    """
    Test the handle_delete_message_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # 1 byte success
    success = struct.pack("!B", 1)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[success, b""])

    mock_client.handle_delete_message_response()

    mock_client.message_callback.assert_called_with(
        "DELETE_MESSAGES:1")


def test_delete_message_fail(mock_client):
    """
    Test the handle_delete_message_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    # 1 byte failure
    failure = struct.pack("!B", 0)

    # Mock `socket.recv` to return response and then terminate
    mock_client.socket.recv = MagicMock(
        side_effect=[failure, b""])

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        mock_client.handle_delete_message_response()

        mock_log_error.assert_called_with(
            "Message deletion failed", False)


def test_delete_account(mock_client):
    """
    Test the handle_delete_account_response method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    mock_client.handle_delete_account_response()

    mock_client.message_callback.assert_called_with(
        "DELETE_ACCOUNT:1")
