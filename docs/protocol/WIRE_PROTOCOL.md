# Wire Protocol: Chat

## General rules

All messages in this protocol support several base types:

- **Integers.** Integers have a defined length in bytes, specificed as part of the message specification. All integers are in big-endian byte order.
- **Booleans.** Booleans are 1-byte integers equal to 1 or 0.
- **Strings.** Strings are in UTF-8. Strings are NOT zero-terminated (as in C), but have a defined length stored in an integer field earlier in the message. This integer field specifies the number of characters in the string. Since strings are in UTF-8, the number of characters is equal to the number of bytes.

All messages begin with a 1-byte integer Operation ID. Each message type specified below has a unique Operation ID. The same Operation ID is used for messages from the client to the server (actions/requests) and messages from the server to the client (responses), though these message types will have different formats. The formats will be specified as "request" or "response" formats under the header for the applicable Operation ID.

Messages are not strictly ordered. The client is advised not to send multiple messages with the same operation ID until a response to the earlier message has been received, such that the client can determine what request a response is intended to respond to.

Message lengths may vary. There is no high-level message length field. A parse-as-you-go approach can identify if a message has concluded by matching the received message against the expected fields and the expected lengths of string fields.

### Versioning

If an operation's message specification is updated, the updated version of the operation must be assigned a new ID.

## Look Up Account (Operation ID 1)

### Request

- Operation ID (1 byte integer)
- Username Length (1 byte integer)
- Username (String)

### Response

- Operation ID (1 byte integer)
- Account Exists (Boolean/1 byte integer)
  - 0: no account exists
  - 1: account exists

The remaining fields will be sent only if the account exists:

- Bcrypt Prefix (29 byte UTF-8 string)

## Log In (Operation ID 2)

### Request

- Operation ID (1 byte integer)
- Username Length (1 byte integer)
- Username (String)
- Password Hash Length (1 byte integer)
- Password Hash (String - bcrypt password hash)

### Response

- Operation ID (1 byte integer)
- Success (Boolean/1 byte integer)
  - False means that the username/password pair was invalid.
- Unread Message Count (2 byte integer)
  - Only sent if success was 1!

## Create Account (Operation ID 3)

_Note: when creating an account a user's socket will automatically be associated with the newly created account. No subsequent login is required._

### Request

- Operation ID (1 byte integer)
- Username Length (1 byte integer)
- Username (String)
- Password Hash Length (1 byte integer)
- Password Hash (String - bcrypt password hash)

_Note: The cost and salt will be determined by the server based on the password hash, which is a string in bcrypt format and thus contains these values._

### Response

- Operation ID (1 byte integer)
- Success (Boolean/1 byte integer)

## List accounts (Operation ID 4)

### Request

- Operation ID (1 byte integer)
- Maximum number of accounts to list (1 byte integer)
- Offset account ID (4 byte integer)
- Filter text length (1 byte integer)
  - Set to 0 when no filtering is requested.
- Filter text (string)
  - Filters the returned accounts to only those whose usernames match the format `*[text]*`

### Response

- Operation ID (1 byte integer)
- Number of accounts (1 byte integer)
- For each account:
  - Account ID (4 byte integer)
  - Username length (1 byte integer)
  - Username (String)

## Send message (Operation ID 5)

### Request

- Operation ID (1 byte integer)
- Username length (1 byte integer)
- Recipient username
- Message length (2 byte integer)
- Message

### Response

- Operation ID (1 byte integer)
- Success (Boolean)
  - False if the specified recipient does not exist.
- Message ID (4 byte integer)
  - The ID of the created message. Only supplied if success is 1.

## Request new messages (Operation ID 6)

### Request

- Operation ID (1 byte integer)
- Maximum quantity (1 byte integer)

### Response

- Operation ID (1 byte integer)
- Number of messages (1 byte integer)
- For each message:
  - Message ID (4 byte integer)
  - Sender username length (1 byte integer)
  - Sender username (String)
  - Message length (2 byte integer)
  - Message

## Delete message(s) (Operation ID 7)

### Request

- Operation ID (1 byte integer)
- Number of message IDs (1 byte integer)
  - A maximum of 255 messages can be deleted at one time.
- For each message:
  - Message ID (4 byte integer)

### Response

- Operation ID (1 byte integer)
- Success (Boolean)
  - False if one or more of the specified message IDs either does not exist or was neither sent nor received by the current user. Users can delete messages they sent or messages that were sent to them.

## Delete account (Operation ID 8)

### Request

- Operation ID (1 byte integer)

_Note: No other request information is needed, as only the currently logged in account can be deleted._

### Response

No response.

_Note: After deletion, the socket is closed by the server without sending a response.._

## Failure (Operation ID 255)

Failure messages are sent by the server when an operation unexpectedly fails. Failure messages may be sent due to unhandled failures on the server or due to an invalid message sent by the client.

Where a request message includes an identifier (i.e. login, send message, delete message), a success field will generally be present in the response. Where such a success field exists, the specification will list the conditions under which it is set to 0. Under those conditions, a standard response message with the success field set to 0 will be sent insetad of a failure message.

A failure message will also be sent when the operation requires being logged in and the client is not currently logged in.

### Response

- Operation ID (1 byte integer)
- Original Request Operation ID (1 byte integer)
- Failure message length (2 byte integer)
- Failure message (String)
