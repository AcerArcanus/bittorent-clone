import asyncio
import sys
import json
from pathlib import Path

# import client_http as http

HOST = '0.0.0.0'            # Local server bind address
PORT = 8888                 # Local server listening port
TRACKER_HOST = '127.0.0.1'  # Tracker server address
TRACKER_PORT = 8080         # Tracker server port
HEARTBEAT_INTERVAL = 3     # Send a heartbeat every 30 seconds

async def tracker_heartbeat_loop():
    # TODO: code here is designed to work with json messages;
    #       this should be changed to work with HTTP instead
    #
    # During the heartbeat, send a POST/provide request to tell the server
    # files available for download from the client
    """
    Background task that periodically registers/pings the tracker server.
    Runs continuously without interrupting network handling or terminal inputs.
    """
    print(f"[*] Heartbeat task started. Tracking with {TRACKER_HOST}:{TRACKER_PORT}")

    # Grab list of files from file-transfer directory
    files = [f.name for f in Path("file-transfer").iterdir()
             if f.is_file() and f.name != ".gitignore"]

    # POST/provide request telling tracker who we are and what files we have
    heartbeat_payload = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {TRACKER_HOST}\r\n"
        f"Accept: text/*\r\n"
        f"Connection: close\r\n"
        f"\r\n"
        f"provide\r\n"
        )

    for file in files:
        heartbeat_payload += f"{file}\r\n"

    # Create HTTP request to send to tracker
    # message = http.HTTPRequest(heartbeat_payload, HOST, PORT)
    # message = (json.dumps(heartbeat_payload) + "\n").encode()

    while True:
        try:
            # Open a connection to send the heartbeat
            reader, writer = await asyncio.open_connection(TRACKER_HOST, TRACKER_PORT)

            writer.write(heartbeat_payload)
            await writer.drain()

            # Optional: Read tracker acknowledgment response
            response = await reader.read(1024)

            writer.close()
            await writer.wait_closed()

            # Print a subtle visual indicator or log
            # sys.stdout.write("\n[Tracker] Heartbeat acknowledged.\nP2P-Client> ")
            # sys.stdout.flush()

        except (ConnectionRefusedError, OSError):
            # Fail silently or log so a down tracker doesn't crash the client
            sys.stdout.write("\n[Tracker Error] Tracker offline. Retrying next cycle...\n\n[Peer Client]$ ")
            sys.stdout.flush()

        # Sleep asynchronously for the designated interval
        await asyncio.sleep(HEARTBEAT_INTERVAL)

async def handle_peer_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # TODO: listen for HTTP request using ClientHTTP,
    #       send response with requested file
    """
    Triggered automatically whenever a peer connects to request a file.
    Runs concurrently without blocking the terminal input loop.
    """
    peer_address = writer.get_extra_info("peername")
    print(f"\n[Network Event] Peer connected from: {peer_address}")

    try:
        # Read the file request from the peer (up to 1024 bytes)
        data = await reader.read(1024)
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
    # TODO: use ClientHTTP to send HTTP request (GET?) to other peer
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

        # Read the peer's response stream (up to 4096 bytes)
        print("[*] Waiting for peer response...")
        response = await reader.read(4096)

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

def get_terminal_input():
    """Synchronous prompt offloaded to a thread for universal OS support."""
    sys.stdout.write("\n[Peer Client]$ ")
    sys.stdout.flush()
    return sys.stdin.readline().strip()

async def terminal_input_loop(server: asyncio.Server, heartbeat_task: asyncio.Task):
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
            print(f"-> Files available for download:")
            print(f"(list files from tracker server here)")

        elif primary_cmd == "request":
            # TODO: Do we want user to say filename, or give list of numbers to choose?
            print(f"-> Select the file you want to request:")
            print(f"(display list of files with corresponding number option)")
            print(f"(...or handle user asking for filename directly)")

        elif primary_cmd == "status":
            print(f"-> [Status] Server is actively listening on {HOST}:{PORT}")
            print(f"-> [Status] Server serving connections: {server.is_serving()}")
            print(f"-> [Status] Tracker Heartbeat: Running every {HEARTBEAT_INTERVAL}s")

        elif primary_cmd == "help":
            # TODO: flesh out help output with short description of each command
            print("-> [Available Commands]: list, request, status, help, exit")

        else:
            print(f"-> [Unknown Command] '{user_input}'. Type 'help' for options.")

async def main(client_ip = HOST, client_port = PORT):
    # 1. Start the background socket server to listen for peers
    server = await asyncio.start_server(handle_peer_connection, HOST, PORT)
    print(f"[*] P2P File Server started on {client_ip}:{client_port}")

    # 2. Spawn the heartbeat loop as a background task
    heartbeat_task = asyncio.create_task(tracker_heartbeat_loop())

    # 3. Keep the terminal input loop running
    async with server:
        await terminal_input_loop(server, heartbeat_task)

if __name__ == "__main__":
    # TODO: allow option for host IP and port to be passed in by the user when
    #       starting client using the argparse python library

    try:
        asyncio.run(main(HOST, PORT))
    except KeyboardInterrupt:
        print("\n[*] Process interrupted by user. Exiting safely.")

