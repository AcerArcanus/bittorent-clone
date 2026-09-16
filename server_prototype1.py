import socket
import threading
import time

class HTTPRequest:
    #intake for a request

    #raw_data has the HTTP request as a string
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.method = None
        self.path = None
        self.version = None
        self.body = None
        self.headers = {}

        self.parse()

    def parse(self):
        #separates headers from body
        parts = self.raw_data.split("\r\n\r\n", 1)

        header_data = parts[0]

        #check for a body
        if len(parts) > 1:
            self.body = parts[1]
        else:
            self.body = ""

        #separates headers from eachother
        lines = header_data.split("\r\n")

        #parses the request, specifically the first line containing the method, path, and version
        request_line = lines[0]
        self.method, self.path, self.version = request_line.split(" ", 2)

        #splits headers, stored into dictionary self.headers
        for line in lines[1:]:
            if line == "":
                break

            name, value = line.split(":", 1)
            self.headers[name.strip()] = value.strip()
            #helps remove whitespace from the name & value

class HTTPResponse:
    #creates HTTP response

    def __init__(
            self, body, status_code = 200, status_text = "OK", 
                 content_type = "text/plain", headers=None,
                 keep_alive = True
                 ):
        self.body = body
        self.status_code = status_code
        self.status_text = status_text
        self.content_type = content_type
        self.headers = headers or {}
        self.keep_alive = keep_alive
        #dictionary is made if no header is provided

    def build(self):
        #builds HTTP response string

        if isinstance(self.body, str):
            body_bytes = self.body.encode("utf-8")
        #encodes the body into bytes if it is string
        else:
            body_bytes = self.body
            #only if it's already bytes

        connection = "keep_alive" if self.keep_alive else "close"

        #creates the HTTP headers
        response = (
            f"HTTP/1.1 {self.status_code} {self.status_text}\r\n"
            f"Content-Type: {self.content_type}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            f"Connection: {connection}\r\n"
        )
        #adds extra custom headers from HTTPResponse
        for name, value in self.headers.items():
            response += f"{name}: {value}\r\n"

        #blank line between header and body
        response += "\r\n"

        #encodes the response and adds already encoded body bytes
        return response.encode("utf-8") + body_bytes


class User:

    def __init__(self, source_ip, source_port, bandwidth = None):
        self.source_ip = source_ip
        self.source_port = source_port
        self.bandwidth = bandwidth #in bytes per second

    #string representation of what is inside the user object
    def __repr__(self):
        return (
            f"({self.source_ip}, {self.source_port}, {self.bandwidth})"
        )

class HTTPServer:
#server itself

    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port

        self.server = None
        self.running = False

        #a dict of lists
        self.data_dict = {}
        self.bandwidth_dict = {}

    def start(self):
        #fcn to start the server

        #creates socket
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        #Tries to bind port, if it cannot, then it returns a runtime error
        try:
            self.server.bind((self.host, self.port))
            #look into OSErrors further
        except OSError:
            self.server.close()

            #closes server if error with socket occurs and returns runtime error

            raise RuntimeError(
                f"Could not start server on {self.host}:{self.port}. "
                "The port may already be in use."
            )

        self.server.listen(5)
        #listens for requests

        self.running = True

        print(
            f"Server running at "
            f"http://{self.host}:{self.port}"
        )

        self.run()
        #runs the server

    def run(self):
        #maintains server loop

        while self.running:
            try:
                client, address = self.server.accept()
                #accepts connection and gathers information about client
                print(f"\nConnection from {address}")


                #creates a separate thread for each client
                client_thread = threading.Thread(
                    #when a new thread arrives, handle the client
                    target = self.handle_client,
                    #tuple containing socket & IP address
                    args = (client, address)

                )

                #starts the thread and allows for background use
                client_thread.daemon = True
                client_thread.start()

            #shows what error ocurred
            except Exception as error:
                print(f"Server error: {error}")

    def measure_bandwidth(self, test_data, el_time):
        #ensures bandwidth calculation doesn't return an error
        if el_time == 0:
            return None

        bandwidth = len(test_data)/el_time
        return bandwidth

    def handle_client(self, client, address):
        #interprets data and responds to client

        try:
            buffer = b""

            while True:
                #ensures you recieve one whole HTTP request
                while b"\r\n\r\n" not in buffer:


                    #recieve request
                    data = client.recv(4096)
                    

                    #return nothing if no data is recieved
                    if not data:
                        return

                    #stores all the data in the buffer
                    buffer += data

                #find where the headers end
                header_end = buffer.find(b"\r\n\r\n")

                header_bytes = buffer[:header_end + 4]

                #decode only the headers
                header_text = header_bytes.decode("utf-8")

                content_length = None

                #finds the content length parameter
                #only needed for POST
                for line in header_text.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":", 1)[1].strip())
                        break

                if content_length is None:
                    content_length = 0

                #calculate the bytes used to make the request
                request_length = header_end + 4 + content_length

                #retrieves the rest of the request
                while len(buffer) < request_length:
                    data = client.recv(4096)

                    if not data:
                        return

                    buffer += data

                #contains exactly one HTTP request
                request_bytes = buffer[:request_length]

                #anything in the next request is left in the buffer
                buffer = buffer[request_length:]

                request_data = request_bytes.decode("utf-8")

                #parse request using HTTPRequest class
                request = HTTPRequest(request_data)

                #just for show and server side readability
                print(f"Request from: {address}")
                print(f"Request line: {request.method} {request.path} {request.version}")

                print("Headers:")
                for name, value in request.headers.items():
                    print(f"  {name}: {value}")

                #creates response from request (interpreted from HTTPRequest class)
                response = self.handle_request(request, address, client)

                #send response
                if response is not None:
                    #bandwidth test is performed here
                    if request.path == "/bandwidth":
                        start_time = time.perf_counter()

                        response_bytes = response.build()
                        client.sendall(response_bytes)

                        end_time = time.perf_counter()

                        el_time = end_time - start_time

                        bandwidth = self.measure_bandwidth(response.body, el_time)
                        self.bandwidth_dict[address] = bandwidth

                    else:
                        client.sendall(response.build())

                #check if client requests to close the connection
                connection_header = request.headers.get("Connection", "").lower()

                if connection_header == "close":
                    break

        except ConnectionResetError:
            print(f"Client {address} disconnection")

        #if an error occurs, responds with error message
        except Exception as error:
            print(f"Request error: {error}")

            response = HTTPResponse(
                body = "Internal Server Error",
                status_code = 500, status_text = "Internal Server Error",
                keep_alive = False
            )

            #sends error message
            client.sendall(response.build())

        #closes connection when finished with client
        finally:
            client.close()
            print(f"Connection closed: {address}")

    #client is never used, but it needs to be passed for methods to work
    def handle_request(self, request, address, client):
        #decides which method handles its appropriate request

        if request.method == "GET":
            return self.get(request, client, address)

        elif request.method == "POST":
            return self.post(request, address)

        else:
            #error method not supported message
            return HTTPResponse(
                body=f"Method {request.method} is not supported",
                status_code = 405,
                status_text = "Method Not Allowed",
                headers = {
                    "Allow": "GET, POST"
                }
            )

    def get(self, request, client, address):
        if request.path == "/bandwidth":

            test_data = b"x" * (102 * 102)
            response = HTTPResponse(
                body = test_data,
                content_type = "application/octet-stream"
            )
            return response

        response =  HTTPResponse(
            body = request.body,
            content_type = "text/html"
        )
        return response

    def post(self, request, address):
        #matches IP to bandwidth
        #.get helps to avoid an error if that address isn't in the dict
        bandwidth = self.bandwidth_dict.get(address)

        if bandwidth == None:
            return HTTPResponse(
                body = "Bandwidth has not been calculated",
                status_code = 400, status_text = "Bad Request"
            )

        #splits by the new line
        body_parts = request.body.split("\r\n")

        #for server interface readability
        print("POST body:", request.body)

        #ensures there is at least something in body_parts
        if body_parts[0] == "":
            return HTTPResponse(
                body = "Invalid POST body",
                status_code = 400, status_text = "Bad Request"
            )

        elif body_parts[0] == "provide":

            #in case it has less than 2 parameters in body_parts
            if len(body_parts) < 2:
                return HTTPResponse(
                    body = "No filename provided",
                    status_code = 400, status_text = "Bad Request"
                )

            for i in body_parts[1:]:
                if i in self.data_dict:

                    #checks whether filename exists in self.data_dict
                    #once that filename is found, it adds the user object to that list
                    #that object contains the IP address, port #, and bandwidth speed
                    self.data_dict[i].append(User(address[0], address[1], bandwidth))


                else:
                    #if a list for that data was not created, it makes one
                    #a list of objects
                    self.data_dict[i] = [User(address[0], address[1], bandwidth)]

            return HTTPResponse(

                body = f"Added to user list for {body_parts[1]}",
                status_code = 201, status_text = "Created",

        )

        #requesting list of data
        #ensures it has at least 2 parameters in body_parts
        elif len(body_parts) >= 2 and body_parts[0] == "request" and body_parts[1] == "list":


            #joins the data keys by adding , inbetween
            file_names = ", ".join(self.data_dict.keys())

            return HTTPResponse(
                #returns only keys in the dict (file names)
                body = f"{file_names}",
                status_code = 200, status_text = "OK"

            )

        elif body_parts[0] == "depart":
            #IP and port of departing client
            client_ip = address[0]
            client_port = address[1]

            #make a temp list of keys to delete from, allowing for safe deletion of dict keys
            for i in list(self.data_dict.keys()):

                #creates a new list that contains only users that don't match departing client's IP & port
                self.data_dict[i] = [user for user in self.data_dict[i] if
                    not (user.source_ip == client_ip and user.source_port == client_port)]

            #delete file if no client provides it anymore
                if not self.data_dict[i]:
                    del self.data_dict[i]

            return HTTPResponse(
                body = "Departed successfully",
                status_code = 200, status_text = "OK"
            )


        #requesting list of people who have that data
        #if the software that is requested is in the dictionary
        #it will respond a list of objects that contain the IP, port, and bandwidth
        else:

            #in case it has less than 2 parameters in body_parts
            if len(body_parts) < 2:
                return HTTPResponse(
                    body = "No filename provided",
                    status_code = 400, status_text = "Bad request"
                )

            elif body_parts [1] in self.data_dict:
                return HTTPResponse(

                body = f"{self.data_dict[body_parts[1]]}",
                status_code = 200, status_text = "OK"
                #uses repr to send user information from within that list
                )

            else:
                return HTTPResponse(

                    body = "File not found",
                    status_code = 404, status_text = "Not Found"
                )


if __name__ == "__main__":
    server = HTTPServer()
    server.start()
