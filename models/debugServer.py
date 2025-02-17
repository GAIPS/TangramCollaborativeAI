import asyncio
import websockets
import json
import signal

async def handle_connection(websocket):
    print("Client connected")
    async for message in websocket:
        print(f"Received from client: {message}")
        response = "fail"
        try:
            data = json.loads(message)
            if isinstance(data, dict):
                if data.get("type") == "playRequest":
                    response = {
                        "type": "play",
                        "shape": "Red",
                        "position": [50, 50],
                        "rotation": 0
                    }
                elif data.get("type") == "playFeedback":
                    response = {
                        "type": "finish",
                    }
                elif data.get("type") == "chatRequest":
                    response = {
                        "type": "chat", 
                        "message": "bla bla bla"
                    }
            else:
                print("Received message is not a dictionary")
        except json.JSONDecodeError:
            print("Failed to parse incoming message as JSON")

        await websocket.send(json.dumps(response))
        print(f"Sent to client: {response}")

async def start_server():
    async with websockets.serve(handle_connection, "localhost", 5000):
        print("WebSocket server started on ws://localhost:5000")
        await asyncio.Future()

def shutDown(signal, frame):
    print("\Shutting down the server...")
    sys.exit(0)

# Register the signal handler for SIGINT (Ctrl-C) and SIGTERM (termination)
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)

asyncio.run(start_server())