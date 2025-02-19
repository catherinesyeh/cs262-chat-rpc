import time
from unittest.mock import patch, MagicMock
import pytest
import os
import sys
import json

from helpers.utils import wait_for_condition

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from client.network.network_json import JSONChatClient
from client import config

# Test the JSONChatClient class


@pytest.fixture(scope="function")
def mock_client():
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]
    with patch.object(JSONChatClient, 'connect', return_value=True):
        # Prevent actual connection attempt
        client = JSONChatClient(host, port, max_msg, max_users)
        client.socket = MagicMock()
        client.running = True
        client.message_callback = MagicMock()
        client.start_listener(client.message_callback)
        return client


### BASIC TESTS ###


def test_client_initialized(mock_client):
    """
    Test that the client is initialized correctly.

    :param mock_client: Mocked JSONChatClient instance
    """
    assert mock_client.running == True, "Client should be running"


def test_client_close(mock_client):
    """
    Test that the client can be closed.

    :param mock_client: Mocked JSONChatClient instance
    """
    mock_client.close()
    assert mock_client.socket is None, "Client socket should be None"


### SENDING REQUESTS ###


def test_send_lookup_account(mock_client):
    """
    Test that the client can send a lookup account message.

    :param mock_client: Mocked JSONChatClient instance
    """
    user = "test_user"
    mock_client.send_lookup_account("test_user")
    expected_request = (json.dumps({"operation": "LOOKUP_USER", "payload": {
                        "username": user}}) + '\n').encode("utf-8")
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_username", ["", None, 123])
def test_send_lookup_account_invalid_username(mock_client, invalid_username):
    """Test lookup request with invalid usernames."""
    assert mock_client.send_lookup_account(
        invalid_username) == False, "Invalid username should return False"


def test_send_create_account(mock_client):
    """
    Test that the client can send a create account message.

    :param mock_client: Mocked JSONChatClient instance
    """
    user = "test_user"
    password = "test_password"
    hashed_password = b"$2b$12$1Q7e4wto"

    # Mock password hashing
    with patch.object(mock_client, 'generate_hashed_password_for_create', return_value=hashed_password):
        mock_client.send_create_account(user, password)
        expected_request = (json.dumps({"operation": "CREATE_ACCOUNT", "payload": {
                            "username": user, "password_hash": hashed_password.decode('utf-8')}}) + '\n').encode("utf-8")
        mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_username", ["", None, 123])
def test_send_create_account_invalid_username(mock_client, invalid_username):
    """Test create request with invalid usernames."""
    assert mock_client.send_create_account(
        invalid_username, "test_password") == False, "Invalid username should return False"


@pytest.mark.parametrize("invalid_password", ["", None, 123])
def test_send_create_account_invalid_password(mock_client, invalid_password):
    """Test create request with invalid passwords."""
    assert mock_client.send_create_account(
        "test_user", invalid_password) == False, "Invalid password should return False"


def test_send_login(mock_client):
    """
    Test that the client can send a login message.

    :param mock_client: Mocked JSONChatClient instance
    """
    user = "test_user"
    password = "test_password"
    hashed_password = b"$2b$12$1Q7e4wto"

    # Mock password hashing
    with patch.object(mock_client, 'get_hashed_password_for_login', return_value=hashed_password):
        mock_client.send_login(user, password)
        expected_request = (json.dumps({"operation": "LOGIN", "payload": {
                            "username": user, "password_hash": hashed_password.decode('utf-8')}}) + '\n').encode("utf-8")
        mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_username", [123, False])
def test_send_login_invalid_username(mock_client, invalid_username):
    """Test login request with invalid usernames."""
    assert mock_client.send_login(
        invalid_username, "test_password") == False, "Invalid username should return False"


@pytest.mark.parametrize("invalid_password", [123, False])
def test_send_login_invalid_password(mock_client, invalid_password):
    """Test login request with invalid passwords."""
    assert mock_client.send_login(
        "test_user", invalid_password) == False, "Invalid password should return False"


def test_send_list_accounts(mock_client):
    """
    Test that the client can send a list accounts message.

    :param mock_client: Mocked JSONChatClient instance
    """
    filter_text = "test"
    mock_client.send_list_accounts(filter_text)
    expected_request = (json.dumps({"operation": "LIST_ACCOUNTS", "payload": {"maximum_number": mock_client.max_users,
                                                                              "offset_account_id": mock_client.last_offset_account_id, "filter_text": filter_text}}) + '\n').encode("utf-8")
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_filter_text", [None, 123])
def test_send_list_accounts_invalid_filter_text(mock_client, invalid_filter_text):
    """Test list accounts request with invalid filter text."""
    assert mock_client.send_list_accounts(
        invalid_filter_text) == False, "Invalid filter text should return False"


def test_send_message(mock_client):
    """
    Test that the client can send a message.

    :param mock_client: Mocked JSONChatClient instance
    """
    recipient = "test_user"
    message = "test_message"
    mock_client.send_message(recipient, message)
    expected_request = (json.dumps({"operation": "SEND_MESSAGE", "payload": {
                        "recipient": recipient, "message": message}}) + '\n').encode("utf-8")
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_recipient", ["", None, 123])
def test_send_message_invalid_recipient(mock_client, invalid_recipient):
    """Test send message request with invalid recipient."""
    assert mock_client.send_message(
        invalid_recipient, "test_message") == False, "Invalid recipient should return False"


@pytest.mark.parametrize("invalid_message", ["", None, 123])
def test_send_message_invalid_message(mock_client, invalid_message):
    """Test send message request with invalid message."""
    assert mock_client.send_message(
        "test_user", invalid_message) == False, "Invalid message should return False"


def test_send_request_messages(mock_client):
    """
    Test that the client can send a request messages message.

    :param mock_client: Mocked JSONChatClient instance
    """
    mock_client.send_request_messages()
    expected_request = (json.dumps({"operation": "REQUEST_MESSAGES", "payload": {
                        "maximum_number": mock_client.max_msg}}) + '\n').encode("utf-8")
    mock_client.socket.send.assert_called_with(expected_request)


def test_send_delete_message(mock_client):
    """
    Test that the client can send a delete message message.

    :param mock_client: Mocked JSONChatClient instance
    """
    message_ids = [1, 2, 3]
    mock_client.send_delete_message(message_ids)
    expected_request = (json.dumps({"operation": "DELETE_MESSAGES", "payload": {
                        "message_ids": message_ids}}) + '\n').encode("utf-8")
    mock_client.socket.send.assert_called_with(expected_request)


@pytest.mark.parametrize("invalid_message_ids", ["", None, 123])
def test_send_delete_message_invalid_message_ids(mock_client, invalid_message_ids):
    """Test delete message request with invalid message ids."""
    assert mock_client.send_delete_message(
        invalid_message_ids) == False, "Invalid message ids should return False"


def test_send_delete_account(mock_client):
    """
    Test that the client can send a delete account message.

    :param mock_client: Mocked JSONChatClient instance
    """
    mock_client.send_delete_account()
    expected_request = (json.dumps(
        {"operation": "DELETE_ACCOUNT", "payload": {}}) + '\n').encode("utf-8")
    mock_client.socket.send.assert_called_with(expected_request)

### HANDLING RESPONSES ###


def test_lookup_account(mock_client):
    """
    Test handling of LOOKUP_USER response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "LOOKUP_USER",
        "success": True,
        "payload": {"exists": True, "bcrypt_prefix": "$2b$12$something"}
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    mock_client.message_callback.assert_called_with("LOOKUP_USER:1")


def test_lookup_account_not_found(mock_client):
    """
    Test handling of LOOKUP_USER response (not found).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "LOOKUP_USER",
        "success": True,
        "payload": {"exists": False}
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    mock_client.message_callback.assert_called_with("LOOKUP_USER:0")


def test_lookup_account_fail(mock_client):
    """
    Test handling of LOOKUP_USER response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "LOOKUP_USER",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation LOOKUP_USER failed: Unexpected failure")


def test_create_account(mock_client):
    """
    Test handling of CREATE_ACCOUNT response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "CREATE_ACCOUNT",
        "success": True,
        "payload": {}
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

   # Assert message callback was called correctly
    mock_client.message_callback.assert_called_with("CREATE_ACCOUNT:1")


def test_create_account_fail(mock_client):
    """
    Test handling of CREATE_ACCOUNT response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "CREATE_ACCOUNT",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        # Call the function
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation CREATE_ACCOUNT failed: Unexpected failure")


def test_login(mock_client):
    """
    Test handling of LOGIN response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "LOGIN",
        "success": True,
        "payload": {
            "unread_messages": 10,
        }
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    mock_client.message_callback.assert_called_with("LOGIN:1:10")


def test_login_fail(mock_client):
    """
    Test handling of LOGIN response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "LOGIN",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        # Call the function
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation LOGIN failed: Unexpected failure")


def test_list_accounts(mock_client):
    """
    Test handling of LIST_ACCOUNTS response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "LIST_ACCOUNTS",
        "success": True,
        "payload": {
            "accounts": [
                {"id": 1, "username": "test_user1"},
                {"id": 2, "username": "test_user2"}
            ]
        }
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    account_data = expected_response["payload"]["accounts"]
    accounts = [(account["id"], account["username"])
                for account in account_data]

    mock_client.message_callback.assert_called_with(
        f"LIST_ACCOUNTS:{json.dumps(accounts)}")


def test_list_accounts_fail(mock_client):
    """
    Test handling of LIST_ACCOUNTS response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "LIST_ACCOUNTS",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        # Call the function
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation LIST_ACCOUNTS failed: Unexpected failure")


def test_send_message_response(mock_client):
    """
    Test handling of SEND_MESSAGE response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "SEND_MESSAGE",
        "success": True,
        "payload": {
            "message_id": 5
        }
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    mock_client.message_callback.assert_called_with("SEND_MESSAGE:1")


def test_send_message_response_fail(mock_client):
    """
    Test handling of SEND_MESSAGE response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "SEND_MESSAGE",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        # Call the function
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation SEND_MESSAGE failed: Unexpected failure")


def test_request_messages(mock_client):
    """
    Test handling of REQUEST_MESSAGES response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "REQUEST_MESSAGES",
        "success": True,
        "payload": {
            "messages": [
                {"id": 1, "sender": "test_user1", "message": "test_message1"},
                {"id": 2, "sender": "test_user2", "message": "test_message2"}
            ]
        }
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    message_data = expected_response["payload"]["messages"]
    messages = [(message["id"], message["sender"], message["message"])
                for message in message_data]

    mock_client.message_callback.assert_called_with(
        f"REQUEST_MESSAGES:{json.dumps(messages)}")


def test_request_messages_fail(mock_client):
    """
    Test handling of REQUEST_MESSAGES response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "REQUEST_MESSAGES",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
       # Call the function
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation REQUEST_MESSAGES failed: Unexpected failure")


def test_delete_message(mock_client):
    """
    Test handling of DELETE_MESSAGES response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "DELETE_MESSAGES",
        "success": True,
        "payload": {}
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    mock_client.message_callback.assert_called_with("DELETE_MESSAGES:1")


def test_delete_message_fail(mock_client):
    """
    Test handling of DELETE_MESSAGES response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "DELETE_MESSAGES",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        # Call the function
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation DELETE_MESSAGES failed: Unexpected failure")


def test_delete_account(mock_client):
    """
    Test handling of DELETE_ACCOUNT response.

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "DELETE_ACCOUNT",
        "success": True,
        "payload": {}
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Call the function
    mock_client.handle_json_response(expected_response_str)

    # Assert message callback was called correctly
    mock_client.message_callback.assert_called_with("DELETE_ACCOUNT:1")


def test_delete_account_fail(mock_client):
    """
    Test handling of DELETE_ACCOUNT response (fail).

    :param mock_client: Mocked JSONChatClient instance
    """
    expected_response = {
        "operation": "DELETE_ACCOUNT",
        "success": False,
        "unexpected_failure": True,
        "message": "Unexpected failure"
    }

    expected_response_str = json.dumps(expected_response) + '\n'

    # Patch log_error method to see if it was called
    with patch.object(mock_client, 'log_error') as mock_log_error:
        # Call the function
        mock_client.handle_json_response(expected_response_str)

        mock_log_error.assert_called_with(
            "Operation DELETE_ACCOUNT failed: Unexpected failure")
