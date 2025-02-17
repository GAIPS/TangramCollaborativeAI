import websockets
import asyncio
import signal
import random
import json
import sys

angles = list(range(0, 361, 45))
shapes = ["Red", "Green", "Blue", "Yellow", "Purple", "Cream", "Brown"]
randomShape = random.choice(shapes)

async def playRequest(data):
    global randomShape
    randomShape = random.choice(shapes)
    return [{"type": "play", "shape": randomShape, "position": (random.randint(5, 95), random.randint(5, 95)),  "rotation": random.choice(angles)}, {"type": "chat", "message": "Test message"}]

async def playFeedback(data):
    print(data)
    print("\n")
    if len(data["state"]["on_board"][randomShape]["collisions"]) > 0:
        return [{"type": "play", "shape": randomShape, "position": (random.randint(5, 95), random.randint(5, 95)), "rotation": random.choice(angles)}, {"type": "chat", "message": "Test message"}]
    return {"type": "finish"}

async def chatRequest(data):
    return {"type": "chat", "message": "Test Reply"}

async def handle_connection(websocket):
    print("Client connected")

    eventHandlers = {
        "playRequest" : playRequest,
        "playFeedback" : playFeedback,
        "chatRequest" : chatRequest
    }

    async for message in websocket:
        message = json.loads(message)
        t = message["type"]
        print(f"Received request from client of type {t}")
        if(message["type"] not in eventHandlers):
            response = "ERROR: Unknown request type"
        else:
            response = await eventHandlers[message["type"]](message)

        if type(response) == list:
            for res in response:
                await websocket.send(json.dumps(res))
        else:   
            await websocket.send(json.dumps(response))
        print(f"Sent to client")

async def start_server():
    async with websockets.serve(handle_connection, "localhost", 5000):
        print("WebSocket server started on ws://localhost:5000")
        await asyncio.Future()

def shutDown(signal, frame):
    print("\Shutting down the server...")
    sys.exit(0)

signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)

asyncio.run(start_server())