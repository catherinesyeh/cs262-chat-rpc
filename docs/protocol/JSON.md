# JSON Protocol: Chat

## General rules

All messages should be sent as standard-form JSON. Messages must match a defined `operation`. Each `operation` defines its own `payload` for requests and responses. For all operations defined below, the JSON format given is for the `payload` only - it must be wrapped in the expected standard format specified below. The `payload` is optional and may be omitted in some cases.

Some fields have maximum lengths. See [docs/SERVER_SPEC.md](/docs/SERVER_SPEC.md). Integers other than account/message IDs must be less than or equal to 255. All string fields with a maximum length not specified in that file must not be over 255 characters.

All messages must be terminated by a newline (`\n`), and should not contain the newline character within them.

The JSON body of a **request** message should always be the following:

```json
{
  "operation": "EXAMPLE",
  "payload": {}
}
```

The JSON body of a **successful response** message should be the following:

```json
{
  "operation": "EXAMPLE",
  "success": true,
  "payload": {}
}
```

The JSON body of a **failed response** message should be the following:

```json
{
  "operation": "EXAMPLE",
  "success": false,
  "unexpected_failure": true,
  "message": "The operation failed because [...]"
}
```

_Note: The `message` field may be unfilled if `unexpected_failure` is false. In these cases, failure has a defined meaning - see the wire protocol for more info._

### Versioning

If an operation's message specification is updated, the updated version of the operation must be assigned a new operation code.

## Look Up Account (Operation: LOOKUP_USER)

### Request

```json
{
  "username": "example" // string
}
```

### Response

```json
{
  "exists": true, // boolean
  // The remaining fields will be sent only if the account exists:
  "bcrypt_prefix": "$2a$12$salt" // 29 byte string, containing bcrypt metadata and salt
}
```

## Log In (Operation ID LOGIN)

### Request

```json
{
  "username": "example", // string
  "password_hash": "1234" // string, bcrypt password hash
}
```

### Response

```json
{
  "unread_messages": 300
}
```

## Create Account (Operation ID CREATE_ACCOUNT)

_Note: when creating an account a user's socket will automatically be associated with the newly created account. No subsequent login is required._

### Request

```json
{
  "username": "example", // string
  "password_hash": "1234" // string, bcrypt password hash
}
```

_Note: The cost and salt will be determined by the server based on the password hash, which is a string in bcrypt format and thus contains these values._

### Response

Empty payload on success.

## List accounts (Operation ID LIST_ACCOUNTS)

### Request

```json
{
  "maximum_number": 10, // integer, maximum number of accounts to return
  "offset_account_id": 1, // integer, see Pagination in server spec
  "filter_text": "1234" // Optional. Filters the returned accounts to only those whose usernames match the format `*[text]*`
}
```

### Response

```json
{
  "accounts": [
    {
      "id": 123123, // integer
      "username": "june" // string
    }
    // ...
  ]
}
```

## Send message (Operation ID SEND_MESSAGE)

### Request

```json
{
  "recipient": "june", // string, recipient username
  "message": "message" // string
}
```

### Response

```json
{
  "message_id": 123456 // integer
}
```

## Request new messages (Operation ID REQUEST_MESSAGES)

### Request

```json
{
  "maximum_number": 10 // integer, maximum number of messages to return
}
```

### Response

```json
{
  "messages": [
    {
      "id": 123456, // integer
      "sender": "june", // string
      "message": "Hi!" // string
    }
    // ...
  ]
}
```

## Delete message(s) (Operation ID DELETE_MESSAGES)

### Request

```json
{
  "message_ids": [1, 2, 3] // Array of message IDs. A maximum of 255 message IDs can be sent at one time.
}
```

### Response

Empty payload on success.

## Delete account (Operation ID DELETE_ACCOUNT)

### Request

Empty payload. No other request information is needed, as only the currently logged in account can be deleted.

### Response

No response.

_Note: After deletion, the socket is closed by the server without sending a response.._
