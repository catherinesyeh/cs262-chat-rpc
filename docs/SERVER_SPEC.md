# General Chat Server Specifications

## Password hashing

Passwords are double-hashed using bcrypt. Double-hashing means that the password will be hashed both by the client and by the server. The server will use the bcrypt hash sent by the client as an input for its own hashing function. Both the client and server hash will have unique salts. Double-hashing prevents values obtained by exfiltrating the database from being used for future login, while also protecting passwords in transit.

The client can obtain the bcrypt settings needed for login by making an account lookup request; this request will return the password salt and number of bcrypt rounds to use. All password hashes will be transmitted in the standard bcrypt string format, which includes the number of rounds, salt, and hash.

## Request/Response System

Most messages from the server will be sent only as a response to a request, with one exception: a read messages response will be sent to a client when a message is sent to that client's logged in user and their connection is active.

Requests can be sent in either JSON format or the custom wire protocol. Any request sent with an opening curly bracket `{` as the first byte (`0x7b`/`123`) will be interpreted as a JSON message. (Thus `123` can never be used as an operation ID.) For spontaneous/unrequested message responses, as described above, the format used by the first request message sent over the connection by the client will be used.

## Pagination

All entities (accounts and messages) are assigned a unique integer ID, which will always be assigned in ascending order. Entities are always returned to the client ordered by ID. The highest ID received by the client in one request can then be used as the "offset ID" in the next request - the server will then return only entities with a greater ID.

Pagination is currently only used for listing accounts, as messages are implicitly paginated by their delivered status, as noted below.

## Maximum Lengths

**Usernames:** 255 characters (2^8-1)

**Messages:** 65535 characters (2^16-1)

## Message delivery

You cannot send a message to yourself.

Only the delivery of new/unread messages is supported by the protocol, but all messages are stored. Once a message has been delivered, it is marked as read and will not be redelivered.

When a message is sent to a currently logged in user, it will be automatically delivered. Automatic message deliveries will only be sent to the most recently logged in socket per user, if a user has multiple open sockets.

## Account Deletion

Deletion of an account marks the account as deleted. The username will remain claimed in the database. The user's hashed password will be deleted, as will all messages received by that user, including unread messages. Messages sent by the user will remain sent.

## Persistence

There is currently no persistence support. A server crash will lose all accounts and messages, as they are stored only in memory.

## Internals

The server code is in the `server/app/src` directory. `main` contains all the functional classes, while `test` contains unit tests.

The `Data` package primarily handles data flowing over the network (including implementations for both protocols), and also includes the definitions for the classes stored in the database.

The `Logic` package contains the actual database and operation logic. These classes only handle internal data classes, and do not interact with the (JSON/wire protocol) data sent over the network - they are exactly the same no matter which protocol is used. The database is an in-memory datastore, with no persistence, and is created in `App` and shared between the threads. All methods are `synchronized` to allow for cross thread use.

The `App` class does very little, beyond setting up a socket server. Most of the work is done in `AppThread`, which repeatedly pulls a request from the socket, parses it (using one of the two protocol classes), handles the request (by handing off the data to an OperationHandler), and then generates a response using the same protocol class as was used to parse the request, sending it back out over the socket.
