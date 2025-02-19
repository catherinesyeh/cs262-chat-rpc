# cs262-chat-rpc

CS262 Design Exercise 2: Chat Server (RPC Version)

This project should provide a fully functional chat system built with RPC instead of raw sockets.

## Setup

1. Duplicate [config_example.json](config_example.json) and rename to `config.json`.
   - Fill in your configuration details.
2. Duplicate [server/config.example.properties](server/config.example.properties) and rename to `server/config.properties`.
   - Fill in your configuration details. Be sure these match!
3. Install the python dependencies for the client (this requires `poetry` to be installed):

```
poetry install
```

## Server

The server is a Java application built using Gradle. On Linux, run `./gradlew run` from the `server` directory to run the server. (On Windows, this can be replaced with `./gradlew.bat`.)

### Server Testing

Run `./gradlew test` from the `server` directory.

## Client

The client is a Python application with a Tkinter interface.

1. Navigate to [client/](client/) folder:

```
cd client
```

2. Start client:

```
poetry run python client.py
```

### Client Testing

1. Navigate into [tests](tests) folder:

```
cd tests
```

2. Start tests:

```
poetry run pytest
```

- Client JSON protocol tests: [tests/test_client_wire.py](tests/test_client_wire.py)
  - Note: server does not need to be running.
- Client JSON protocol tests: [tests/test_client_json.py](tests/test_client_json.py)
  - Note: server does not need to be running.
- Integration tests: [tests/test_integration.py](tests/test_integration.py)
  - Note: These tests do require the server and expect a clean database, so we suggest restarting the server before running them.
  - To test with each protocol, change the `USE_JSON_PROTOCOL` flag in your `config.json` file.
  - The integration tests will also log metrics to the [tests/logs/](tests/logs/) directory.

## Documentation

More comprehensive internal documentation (including engineering notebooks with our efficiency analysis) is in the [docs/](docs/) folder.
