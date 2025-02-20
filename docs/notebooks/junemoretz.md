# June Moretz Engineering Notebook

## February 19, 2025

One thought I've already had: the previous model of sending messages over the socket immediately will no longer be possible since RPC is request/response. My suggestion is that we use a polling approach like the other teams, and just run the standard retrieve messages call every few seconds.

I'm going to start writing up a gRPC definition as a translation of our previous protocols tonight, and hopefully figure out how to integrate that into the Java server later!

Update - started writing the new server to make sure I know what I'm doing while writing the gRPC definitions. Looks like ultimately it'll involve the following:

- Replacing all the custom request/response types with gRPC generated code (for simplicity)
- Moving the logic from AppThread into the rewritten App, which will contain the gRPC server
- Removing the Protocol files entirely
- Rewriting a number of tests

Another realization: gRPC is stateless, sockets aren't. Easiest way to work around this is probably just to implement a simple session system where clients get a random string as a session key and have to attach it to future requests.
