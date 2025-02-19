# June Moretz Engineering Notebook

## February 5, 2025

(Goals: Protocol Design/Documentation)

I met with Catherine today after class to begin work on the design exercise. We decided to move forward by splitting the work between us such that we can more easily move forward independently and take advantage of all the time available to us as wel as possible. We also discussed language choices. I will be taking the lead on protocol design and server side development for now, while she will be working primarily on the client, at least until we next meet.

I've designed an initial wire protocol, as well as a JSON protocol. My plan is to build the server in Java, and to build a translation layer that can convert either wire protocol format into an internal representation. My largest concern with my wire protocol design is that lengths of messages are not fixed (or, for that matter, specified anywhere in the message). Whether or not a message has been fully received can be deduced at any time, but this may add some level of complexity. If this causes serious issues, we may end up having to change some elements of the design - however, given the existence of a JSON protocol (where a length attribute would be unconventional and the end of the message can similarly only be deduced from context), I'm not certain how useful it would really be to change this. The choice of raw sockets is one I'm somewhat unaccustomed to, as I'm used to higher level protocols (RPC-like systems or HTTP), but I'm confident I'll figure it out quickly once we start on implementation. For now, we felt it would be easiest to move forward if we both have some shared documentation to work from. This protocol design (and some specifications for the system) should provide the baseline for coordinating server and client development, and we'll refine as needed from there!

## February 7, 2025

(Goals: Server Wireframing, Client Validation)

### Client Validation

I pulled Catherine's code to attempt to run the client. I did have some issues getting it set up, which I believe were related to an old version of Poetry that I had retrieved from the Arch repositories and wasn't handling the pyproject.toml file properly. After fixing this, I was able to install the dependencies and run the client - though the version that didn't mock out the server never called `connect`! I fixed this error so I could actually send socket connections to my server as I started attempting to wireframe a functional socket server.

### Wireframing the Server

I can't remember the last time I started a project in Java from scratch, especially without an IDE (I'm writing this entire project in Visual Studio Code). I found a tutorial for initializing a new project using Gradle, which seemed sufficient for my needs - I ran this to initialize a project, installed a working JDK, and managed to get it to compile--and even better, to pull in a JSON parsing library as a first dependency.

I haven't written any tests yet, since I'm just trying to get the server into working shape. It's always hard wrapping my brain around a paradigm and ensuring I know what I'm doing before diving into just writing code, so that's been my focus for now - especially around ensuring the socket server will function in a variety of different cases. (For example, how do we extract a single JSON message out of the socket, when its length is unknown? I think I've solved this problem at least - messages should be newline separated and should not contain newlines! I've also decided to use threads rather than selecting sockets, as this allows blocking when more bytes are needed to properly parse a message to work without disabling other clients.)

This wireframed test server seems to be in fairly good shape now. A few decisions I made and accomplishments:

- Server configuration is separate from client configuration, in a .properties file in the server directory. I need to document this properly later. It does seem to be working though!
- The protocols are implemented through separate implementations of a Protocol interface. These should be called with an input stream, and will then create a standard-form Request class, which the server can handle consistently regardless of the input format. The Protocol interface will then also have methods to generate all of the needed response types. This means that the logic and the protocol layer can ideally be completely separated.
- I also made a Data class. This contains internal data-only classes, as well as data-only classes to contain multiple fields for request/response messages that need these - these classes will be produced or consumed by the Protocol methods. Longer term, I want to have a Datastore class that will handle database operations - this will just be needed by the server logic, and not by the protocol layer, where my current focus is, so I'll work on it later.
- I'll need to add more tests once I start building more of the protocol and logic functionality. I want to have a wide spectrum of tests, from unit tests to more end-to-end tests.

## February 8, 2025

(Goals: Data Parsing)

I'm continuing to work on the wireframed data parsing system I built yesterday. A lot of the data classes are plain Java objects where all the fields are public. This might not be ideal coding practice, but in a small application with sufficient testing, it doesn't concern me too much (and makes development substantially faster - we don't have unlimited time!)

I've already finished building the parser for JSON request messages. It was quite easy with the base I had in place from yesterday, and seems to be working too! I've also written some helpers to assist in the wire protocol parser, which should make it just as quick to finish. Really not too bad once I've established the general flow for "how should the protocol translator work" - just a matter of filling in the holes for each message type until it matches the spec!

Once this is done, I'll probably start framing out the actual logic and database system for the server. It'll be easier to write the response serializers for both protocol layers once I have an actual source for the response messages. After that's done I'll go back and fill in a lot of the tests. I'd like to unit-test the protocol and logic layers fairly thoroughly - the logic of the main app thread and socket system can be tested better by end-to-end integration tests! I expect Catherine will be able to write some tests for the client that can hit the actual server, so long as one is configured and running - this will ensure everything works end to end as intended.

I'll also want to manually try out the rest of the client. Since the server doesn't work yet (and I'm not bothering testing with the mock network), I've never even gotten past the first step of the login screen. I'll need to be sure that we've interpreted the protocol/instructions sufficiently similarly!

I'm planning to go back and document and refactor my code somewhat once it's in working shape. I'd rather not write documentation for code that I'll be changing a lot in the next few days and doesn't work yet!

### (Update 2)

The JSON and wire protocol parsers are finished, and fully tested! Everything seems to be working as intended. I'm starting on the database and logic now. The database will just be a Java object, with no persistence - if the server crashes, all data will be lost.

### (Update 3)

I now have a working database system, including testing, and logic for the first few operations - looking up and logging into or registering an account! I ran into a number of issues with the client while getting this working, which I'll be reaching out to Catherine about:

- The bcrypt logic in Python was a bit different than what I expected. It interprets "salt" as the entire prefix of the bcrypt hash (the first 29 bytes, excluding the actual hash), rather than just the 16-byte (22-byte in base64) salt. I changed the specification to just send this instead, since it'll work well enough, and modified the client to match.
- There were a few other client issues in how it interacted with the server, some of which I've fixed and some of which I haven't. It seems to expect a `message` for a create account request, which doesn't match the spec, and also expects users to log in after creating an account, which isn't needed per the spec. The user list request also seems to be providing more parameters than that method actually needs. There might be some other issues, but if so I haven't built the server out enough to find them yet - getting there, though!

The database system should have everything needed to handle the remaining operations - I just need to write some additional higher-level logic and the response generation for both protocols. I'll then need to do some testing on both the higher-level logic and response generation. Once this is done, the server should be approximately complete, other than cleaning up and documenting the code!

### (Update 4)

I believe the server is approximately done! It should be able to handle every message type in both protocols. I'll be waiting for Catherine to work on the client some more with the server available, and then we can hopefully do some end-to-end integration testing and resolve any outstanding issues. The testing I've done so far was definitely very helpful - I found a lot of lingering bugs in my code by writing tests for the logic and for the message parsers and generators, so I wouldn't be surprised if there are a few left in the parts that are hard to test without a complete client.

## February 10, 2025

I met with Catherine again today after class. Things seem to be in pretty good shape - we're just about ready for Wednesday! I did notice a few issues:

- A graphical issue on the client with displaying long lines of text properly
- The server doesn't prevent users from sending themselves messages, despite synchronization possibly causing a deadlock if this occurs. (Fixed - this is now prohibited, and checked for!)
- Pagination handling on the list accounts call was incorrect. Thank you to Catherine for informing me of this - I fixed it and added a test.

## February 11, 2025

Almost everything seems to be in working order, but I had managed to overlook properly setting up the global socket mapping that's needed to auto-deliver messages to logged in recipients. This has now been fixed! Glad I tested this properly before demo day.
