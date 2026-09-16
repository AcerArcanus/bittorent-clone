import asyncio
import sys
from pathlib import Path

import client_http as http

HOST = '0.0.0.0'            # Local server bind address
PORT = 8888                 # Port to listen for tracker messages
P2P_PORT = 6767             # Port for listening for peer requests
TRACKER_HOST = '127.0.0.1'  # Tracker server address
TRACKER_PORT = 8080         # Tracker server port
HEARTBEAT_INTERVAL = 30     # Send a heartbeat every 30 seconds

# used to keep track of connections so that they can remain
# persistent outside and between function calls
class ConnectionManager:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        if self.writer is not None:
            return

        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

        print(f"[+] Connected to tracker at {self.host}:{self.port}")

    async def send(self, request):
        if self.writer is None:
            raise ConnectionError("Not connected to tracker.")

        self.writer.write(request.encode("utf-8"))
        await self.writer.drain()

        return await self.read_response()

    async def read_response(self):
        # Read until HTTP headers are complete
        response_buffer = b""

        while b"\r\n\r\n" not in response_buffer:
            data = await self.reader.read(1073152)

            if not data:
                raise ConnectionError("Tracker closed the connection.")

            response_buffer += data

        header_end = response_buffer.find(b"\r\n\r\n")
        header = response_buffer[:header_end + 4]

        # Find Content-Length
        content_length = 0

        for line in header.decode("utf-8").split("\r\n"):
            if line.lower().startswith("content-length:"):
                content_length = int(
                    line.split(":", 1)[1].strip()
                )
                break

        body_start = header_end + 4

        # Read until the complete body has arrived
        while len(response_buffer) - body_start < content_length:
            data = await self.reader.read(4096)

            if not data:
                raise ConnectionError("Tracker closed the connection.")

            response_buffer += data

        return response_buffer[:body_start + content_length]

    async def close(self):
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()

        self.writer = None
        self.reader = None

async def tracker_heartbeat_loop(conn: ConnectionManager):
    # During the heartbeat, send a POST/provide request to tell the server
    # files available for download from the client
    """
    Background task that periodically registers/pings the tracker server.
    Runs continuously without interrupting network handling or terminal inputs.
    """
    print(f"\n[*] Heartbeat task started. Tracking with {TRACKER_HOST}:{TRACKER_PORT}")
    print(f"\n[Peer Client]$ ")

    # Grab list of files from file-transfer directory
    files = [f.name for f in Path("file-transfer").iterdir()
             if f.is_file() and f.name != ".gitignore"]

    # POST/provide request telling tracker who we are and what files we have
    body = f"provide\r\n"
    for file in files:
        body += f"{file}\r\n"  # store body separately to calculate byte len

    body_bytes = body.encode("utf-8")

    heartbeat_payload = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {TRACKER_HOST}\r\n"
        f"Accept: text/*\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"Connection: keep_alive\r\n"
        f"\r\n"
        + body
        )

    try:
        # Send GET request to measure bandwidth
        get_req = (
            f"GET /bandwidth HTTP/1.1\r\n"
            f"Host: {TRACKER_HOST}\r\n"
            f"Accept: text/*\r\n"
            f"Connection: keep_alive\r\n"
            f"\r\n"
            )

        # Use pre-existing connection
        get_response = await conn.send(get_req)

        # Print response (if needed for debugging)
        # print("[Tracker] GET response:")
        # print(get_response)

        # Send POST request in while loop
        while True:
            heartbeat_response = await conn.send(heartbeat_payload)

            # Optional: Read tracker acknowledgment response (for debugging)
            # print("[Tracker] POST response:")
            # print(heartbeat_response)

            # Print a subtle visual indicator or log
            # sys.stdout.write("\n[Tracker] Heartbeat acknowledged.\n\n[Peer Client]$ ")
            # sys.stdout.flush()

            # Sleep asynchronously for the designated interval
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    except (ConnectionRefusedError, OSError):
        # Fail silently or log so a down tracker doesn't crash the client
        sys.stdout.write("\n[Tracker Error] Tracker offline. Retrying next cycle...\n\n[Peer Client]$ ")
        sys.stdout.flush()

async def request_list(conn: ConnectionManager):
    # POST/request request asking for list of files from tracker
    body = "request\r\nlist\r\n"
    body_bytes = body.encode("utf-8")

    req_payload = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {TRACKER_HOST}\r\n"
        f"Accept: text/*\r\n"
        f"Content-Length: 15\r\n"
        f"Connection: keep_alive\r\n"
        f"\r\n"
        + body
        )

    try:
        # Use pre-existing tracker connection to send the list request
        response = await conn.send(req_payload)

        # response_body = get_body(response)

        # if response_body == "":
            # pass

        # else:
            # print(f"-> Files available for download:")

        # Optional: Read raw tracker acknowledgment response (for debugging)
        print("LIST RESPONSE:")
        print(response)

    except (ConnectionRefusedError, OSError):
        # Fail silently or log so a down tracker doesn't crash the client
        sys.stdout.write("\n[Tracker Error] Unable to get list from tracker\n\n[Peer Client]$ ")
        sys.stdout.flush()


async def handle_peer_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # TODO: listen for HTTP request using ClientHTTP,
    #       send response with requested file
    #       Might use ConnectionManager for this?
    """
    Triggered automatically whenever a peer connects to request a file.
    Runs concurrently without blocking the terminal input loop.
    """
    peer_address = writer.get_extra_info("peername")
    print(f"\n[Network Event] Peer connected from: {peer_address}")

    try:
        # Read the file request from the peer
        data = await reader.read(1073152)
        filename = data.decode().strip()
        print(f"[Network Event] Peer requested file: '{filename}'")

        # --- File Transfer Logic (Boilerplate placeholder) ---
        # In a real app, verify the file exists, read it, and stream bytes back.
        response = f"SUCCESS: Preparing to transfer '{filename}'...\n"
        writer.write(response.encode())
        await writer.drain() # Ensure all data is sent out over the socket

    except Exception as e:
        print(f"[Network Error] Error handling peer {peer_address}: {e}")
    finally:
        print(f"[Network Event] Closing connection to {peer_address}\n")
        writer.close()
        await writer.wait_closed()

async def request_file_from_peer(host: str, port: int, filename: str):
    # TODO: possibly use ConnectionManager? Unless persistence is not required
    """
    Connects to a peer, requests a file, and prints the response.
    """
    print(f"[*] Attempting to connect to peer at {host}:{port}...")

    try:
        # Open an asynchronous network connection to the target peer
        reader, writer = await asyncio.open_connection(host, port)
        print(f"[+] Connected to peer!")

        # Send the file request (add a newline as a delimiter)
        print(f"[*] Requesting file: '{filename}'")
        writer.write(f"{filename}\n".encode())
        await writer.drain()  # Ensure data is flushed through the network socket

        # Read the peer's response stream
        print("[*] Waiting for peer response...")
        response = await reader.read(-1)

        if response:
            print(f"\n[Peer Response]:\n{response.decode().strip()}")
        else:
            print("\n[-] Peer closed the connection without sending data.")

    except ConnectionRefusedError:
        print(f"\n[-] Error: Connection refused. Is the peer server running on port {port}?")
    except Exception as e:
        print(f"\n[-] An error occurred: {e}")
    finally:
        # Cleanly close the network connection
        if 'writer' in locals():
            writer.close()
            await writer.wait_closed()
            print("[*] Connection closed.")

async def depart():
    pass

def get_terminal_input():
    """Synchronous prompt offloaded to a thread for universal OS support."""
    sys.stdout.write("\n[Peer Client]$ ")
    sys.stdout.flush()
    return sys.stdin.readline().strip()

async def terminal_input_loop(server: asyncio.Server, heartbeat_task: asyncio.Task,
                              conn: ConnectionManager):
    """Asynchronously captures terminal inputs and maps them to client commands."""
    loop = asyncio.get_running_loop()
    print("Terminal input active. Type 'list', 'request', 'status', 'help', or 'exit'.")

    while True:
        # Run blocking terminal input inside an isolated executor thread
        user_input = await loop.run_in_executor(None, get_terminal_input)
        command = user_input.lower().split()

        if not command:
            continue

        primary_cmd = command[0]

        if primary_cmd == "exit":
            print("Shutting down P2P server and exiting...")
            heartbeat_task.cancel()    # Stop the background heartbeat loop
            server.close()
            await server.wait_closed()
            break

        elif primary_cmd == "list":
            # TODO: send HTTP request to server to get list of hosts/files
            await request_list(conn)

        elif primary_cmd == "request":
            # TODO: Do we want user to say filename, or give list of numbers to choose?
            print(f"-> Select the file you want to request:")
            print(f"(display list of files with corresponding number option)")
            print(f"(...or handle user asking for filename directly)")

        elif primary_cmd == "status":
            print(f"-> [Status] Server is actively listening on {HOST}:{PORT} for tracker server")
            print(f"-> [Status] Server is actively listening on {HOST}:{P2P_PORT} for peers")
            print(f"-> [Status] Server serving connections: {server.is_serving()}")
            print(f"-> [Status] Tracker Heartbeat: Running every {HEARTBEAT_INTERVAL}s")

        elif primary_cmd == "help":
            # TODO: flesh out help output with short description of each command
            print("-> [Available Commands]: list, request, status, help, exit")

        else:
            print(f"-> [Unknown Command] '{user_input}'. Type 'help' for options.")

async def main(client_ip = HOST, client_port = PORT):
    # 1. Start the background socket server to listen for peers
    server = await asyncio.start_server(handle_peer_connection, HOST, P2P_PORT)
    print(f"[*] P2P File Server started on {client_ip}:{client_port}")

    # 2. Initialize persistent connection with tracker, and
    #    spawn the heartbeat loop as a background task
    tracker_conn = ConnectionManager(TRACKER_HOST, TRACKER_PORT)

    try:
        await tracker_conn.connect()
        heartbeat_task = asyncio.create_task(tracker_heartbeat_loop(tracker_conn))

        # 3. Keep the terminal input loop running
        async with server:
            await terminal_input_loop(server, heartbeat_task, tracker_conn)

    # 4. If input loop is escaped, program is ending; kill conns/tasks
    finally:
        heartbeat_task.cancel()

        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        await tracker_conn.close()

if __name__ == "__main__":
    # TODO: allow option for host IP and port to be passed in by the user when
    #       starting client using the argparse python library

    try:
        asyncio.run(main(HOST, PORT))
    except KeyboardInterrupt:
        print("\n[*] Process interrupted by user. Exiting safely.")

