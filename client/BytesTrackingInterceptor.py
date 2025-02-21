import grpc


class BytesTrackingInterceptor(grpc.UnaryUnaryClientInterceptor):
    def __init__(self, client):
        """
        Initializes the interceptor with a reference to the ChatClient instance.

        :param client: The ChatClient instance.
        """
        self.client = client  # Reference to the ChatClient instance

    def intercept_unary_unary(self, continuation, client_call_details, request):
        """
        Intercepts unary-unary RPC calls to measure bytes sent and received.

        :param continuation: The continuation function to invoke the next interceptor in the chain.
        :param client_call_details: The client call details.
        :param request: The request message.
        :return: The response object (future or not).
        """
        request_size = request.ByteSize()
        self.client.bytes_sent += request_size

        # Get the response (this may be a future)
        response_future = continuation(client_call_details, request)

        # If the response is a future, we extract the actual response
        response = response_future.result() if hasattr(
            response_future, "result") else response_future

        # Measure response size if it's available
        if response and hasattr(response, "ByteSize"):
            response_size = response.ByteSize()
            self.client.bytes_received += response_size

        # Return the original response object (future or not)
        return response_future
