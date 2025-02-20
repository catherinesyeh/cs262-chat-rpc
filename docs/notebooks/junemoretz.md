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

Todos:

- Build session handling into the database and rip out unneeded bits (done!)
- Make login/create session-aware (done!)
- Build a session lookup utility for the rest (and make the operation handler responsible for using it, to keep other operation implementations similar) (done!)
- Make the existing operation handler test validate this (done!)
- Write a proper server-side test that includes the gRPC server and the session system (done!)

### Update

I believe the server is now 100% done! That wasn't too bad. Using gRPC has its advantages - generated code means the amount of code actually written by me in the server is only around 500 lines total now, and it's a lot more fluent to work with (and to be sure of the protocol layer's correctness) than the custom protocols. It does have its disadvantages (particularly around being stateless, which forced me to implement a session system). We _could_ have used gRPC streams to have messages delivered instantly, but this seemed like it would be more difficult than it's worth on the client end (and would be no less complex than the previous approach on the server side), so we're opting for polling instead.

We haven't yet tested the difference in bytes sent between gRPC and our custom wire protocol. We'll do this once Catherine has the client reimplementation done - this should let us use (roughly) the same test suite as before, for a direct comparison!
