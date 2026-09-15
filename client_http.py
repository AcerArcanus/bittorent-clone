import sys      # Used so client can read from stdin
import socket

class HTTPRequest:
    # Creates and encodes HTTP request to send to server or other peers

    def __init__(self, req: str, source_ip: str, dest_port: int):
        self.req = req
        self.method = None
        self.path = None
        self.version = None
        self.headers = {}
        self.body = None
        self.destination = None
        self.source_ip = source_ip
        self.dest_port = dest_port

        self.parse()

    def parse(self):

        # Split input string from req into a list of strings
        lines = self.req.split("\r\n")

        # Parse for method, path, and HTTP version
        request_line = lines[0]
        self.method, self.path, self.version = request_line.split(" ")

        # Check that HTTP method in request is valid
        valid_methods = ["GET", "POST"]
        if self.method not in valid_methods:
            raise ValueError(f"{self.method} is not a valid HTTP method for this client")

        # Store header lines as key-value pairs
        for index, line in enumerate(lines[1:]):
            # if end of headers, store body if there is one
            if line == "":
                body_index = lines.index("") + 1
                self.body = []
                for body_elem in lines[body_index:]:
                    self.body.append(body_elem)
                break

            name, value = line.split(":", 1)
            self.headers[name.strip()] = value.strip()

        # Raise error if no host is given, else save host to request object
        if "Host" not in self.headers:
            raise ValueError("No destination host specified in request")
        self.destination = (self.headers["Host"], 8080)

    def send_req(self):
        # Create TCP/IPv4 socket to communicate with server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # Bind socket to IP and port
            # NOTE: appears to be redundant on the client side; just needs to connect
            # client_socket.bind((self.source_ip, self.dest_port))

            # Connect to server using destination IP
            client_socket.connect(self.destination)

            # Send the HTTP request
            # socket method requires byte object, so it must be encoded
            client_socket.sendall(self.req.encode("utf-8"))

            # Receive and print response
            response = client_socket.recv(4096)

            # Close the connection (may be redundant due to with statement)
            if self.headers["Connection"] == "close":
                client_socket.close()

            # Decode and return response
            return response.decode("utf-8")

if __name__ == "__main__":
    # Declare source IP and outgoing port variables here manually
    source_ip = "127.0.0.1"
    port = 7787

    req = HTTPRequest(sys.stdin.read(), source_ip, port)
    print(req.send_req())
