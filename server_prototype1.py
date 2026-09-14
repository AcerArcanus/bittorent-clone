import socket
import threading

class HTTPRequest:
    #intake for a request

    #raw_data are the raw bits being sent
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
        self.method, self.path, self.version = request_line.split(" ")

        #splits headers, stored into dictionary self.headers
        for line in lines[1:]:
            if line == "":
                break

            name, value = line.split(":", 1)
            self.headers[name.strip()] = value.strip()
        #commented out, parse has been changed

class HTTPResponse:
    #creates HTTP response

    def __init__(self, body, status_code=200, status_text="OK", content_type="text/plain", headers=None):
        self.body = body
        self.status_code = status_code
        self.status_text = status_text
        self.content_type = content_type
        self.headers = headers or {}
        #doing this so a new dictionary is made every time it is ran

    def build(self):
        #builds HTTP response string

        if isinstance(self.body, str):
            body_bytes = self.body.encode("utf-8")
        #encodes the body into bytes if it is string
        else:
            body_bytes = self.body
            #only if it's already bytes

        #creates the response from variables, can vary depending on situation
        response = (
            f"HTTP/1.1 {self.status_code} {self.status_text}\r\n"
            f"Content-Type: {self.content_type}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            "Connection: close\r\n"
        )
        #for loop separates the headers
        for name, value in self.headers.items():
            response += f"{name}: {value}\r\n"
        #headers get placed here

        return response.encode("utf-8") + body_bytes


class HTTPServer:
#server itself

    def __init__(self, host="127.0.0.1", port=8080, backlog=5):
        self.host = host
        self.port = port
        self.backlog = backlog

        self.server = None
        self.running = False

        self.address = None
        self.data_dict = {}

    def start(self):
        #fcn to start the server

        #creates socket
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        #Tries to bind port, if it cannot, then it returns a runtime error
        try:
            self.server.bind((
                self.host, 
                self.port
                ))
            #look into OSErrors further
        except OSError:
            self.server.close()

            #closes server if error with socket occurs and returns runtime error

            raise RuntimeError(
                f"Could not start server on {self.host}:{self.port}. "
                "The port may already be in use."
            )
        
        self.server.listen(self.backlog)
        #ensure it runs continuously

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
                client, self.address = self.server.accept()
                #accepts connection and gathers information about client
                print(f"\nConnection from {self.address}")


                #creates a separate thread for each client
                client_thread = threading.thread(
                    #name of the fcn thread will run
                    target = self.handle_client,
                    #tuple containing socket & IP address
                    args = (client, self.address[0])

                )

                #starts the thread and allows for background use
                client_thread.daemon = True
                client_thread.start()

                self.handle_client(client)

            #shows what error ocurred
            except Exception as error:
                print(f"Server error: {error}")

    def handle_client(self, client):
        #interprets data and responds to client

        try:
            #recieve request
            data = client.recv(4096).decode("utf-8")
            #look more into bites, encoding, and decoding

            #return nothing if no data is recieved
            if not data:
                return

            #parse request using HTTPRequest class
            request = HTTPRequest(data)

            #just for show and server side readability
            print(f"Request: {request}")

            print("Headers:")
            for name, value in request.headers.items():
                print(f"  {name}: {value}")

            #creates response from request (interpreted from HTTPRequest class)
            response = self.handle_request(request)

            #send response
            client.sendall(response.build())

        #if an error occurs, responds with error message
        except Exception as error:
            print(f"Request error: {error}")

            response = HTTPResponse(
                body="Internal Server Error",
                status_code=500,
                status_text="Internal Server Error"
            )

            #sends error message
            client.sendall(response.build())

        #finally is used to catch and present all error messages that were made
        #closes client
        finally:
            client.close()

    def handle_request(self, request):
        #decides which method handles its appropriate request

        if request.method == "GET":
            return self.get(request)

        elif request.method == "POST":
            return self.post(request)

        else:
            #error method not supported message
            return HTTPResponse(
                body=f"Method {request.method} is not supported",
                status_code=405,
                status_text="Method Not Allowed",
                headers={
                    "Allow": "GET, POST"
                }
            )

    def get(self, request):

        response =  HTTPResponse(
            body = request.body, content_type = "text/html"
        )
        return response

    def post(self, request):
        body_parts = []
        body_parts = request.body.split(" ", 3)
        #for server interface readability
        print("POST body:", request.body)

        
        if body_parts[0] == "provide":
            if body_parts[1] in self.data_dict:
                #searches data_dict for body_parts[1], which contains a dictionary
                #once that dictionary is found, it adds a key value pair containing the ip address and the port #
                 self.data_dict[body_parts[1]][self.address[0]] = self.address[1]

            else:
                #if the dictionary for that data was not already made, it creates a new one
                self.data_dict[body_parts[1]] = {self.address[0] : self.address[1]}

            return HTTPResponse(

                body = f"Added to user list for {body_parts[1]}", 
                status_code = 201, status_text = "Created",

        )

        #requesting list of data
        elif body_parts[0] == "request" and body_parts[1] == "list": 
            return HTTPResponse(

                body = f"{self.data_dict}",
                status_code = 200, status_text = "OK"

            )

        #requesting list of people who have that data
        else:
            if body_parts [1] in self.data_dict:
                return HTTPResponse(

                body = f"{self.data_dict[body_parts[1]]}",
                status_code = 200, status_text = "OK"

                )


server = HTTPServer()
server.start()