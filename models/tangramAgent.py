import websockets
import asyncio
import signal
import random
import json
import sys

class TangramAgent:
    def __init__(self):
        self.angles = list(range(0, 361, 45))
        self.shapes = ["Red", "Green", "Blue", "Yellow", "Purple", "Cream", "Brown"]
        self.randomShape = random.choice(self.shapes)
        signal.signal(signal.SIGINT, self.shutDown)
        signal.signal(signal.SIGTERM, self.shutDown)

    async def playRequest(self, data):
        """
        Function to handle a new play request from the game.

        **Input:**
        - `data` (dict): Dictionary containing the play request data.  
          - `type` (string): "playRequest"  
          - `objective` (string): The objective of the current game.  
          - `state` (dict): Game state information.  
            - `on_board` (dict): Information about pieces on the board.  
              - `{PIECE}` (dict): A piece’s name and its current state.  
                - `position` (array[float]): (X, Y) coordinates of the center.  
                - `vertices` (array[array[float]]): List of (X, Y) vertices.  
                - `rotation` (float): Rotation in degrees.  
                - `collisions` (array[string]): List of pieces colliding with `{PIECE}` or `BOUNDARY`.  
            - `off_board` (dict): Pieces not placed on the board.  
              - `{PIECE}` (dict): A piece’s name and its properties.  
                - `vertices` (dict): X, Y coordinates relative to center (0,0).  
                - `rotation` (float): Rotation in degrees.  
          - `board_img` (string, base64): Image of the current board.  
          - `drawer_img` (string, base64): Image of the piece drawer.  
          - `timestamp` (string): Timestamp of the request.  

        **Output:**
        Single play type reply or list containing one play type reply and chat type replies.

        - `response` (dict): The play action the agent wants to make.  
          - `type` (string): "play".  
          - `shape` (string): The name of the piece to place.  
          - `position` (array[float]): (X, Y) coordinates for placement.  
          - `rotation` (float): Rotation in degrees.  
          - `timestamp` (string): Timestamp of the response.  
        """
        self.randomShape = random.choice(self.shapes)
        return {
                "type": "play",
                "shape": self.randomShape,
                "position": (random.randint(5, 95), random.randint(5, 95)),
                "rotation": random.choice(self.angles)
            }

    async def playFeedback(self, data):
        """
        Function to handle a feedback about the latest play from the game.

        **Input:**
        - `data` (dict): Dictionary containing play feedback.  
          - `type` (string): "playFeedback".  
          - `objective` (string): The objective of the current game.  
          - `state` (dict): Game state information.  
            - `on_board` (dict): Details of pieces on the board.  
              - `{PIECE}` (dict): A piece's name and its current state.  
                - `position` (array[float]): (X, Y) center coordinates.  
                - `vertices` (array[array[float]]): List of (X, Y) vertices.  
                - `rotation` (float): Rotation in degrees.  
                - `collisions` (array[string]): List of colliding pieces or `BOUNDARY` if out of bounds.  
          - `board_img` (string, base64): Image of the board.  
          - `drawer_img` (string, base64): Image of the piece drawer.  
          - `timestamp` (string): Timestamp of the feedback.  

        **Output:**
        Single play type reply or list containing one play type reply and chat type replies.

        - If adjustments are needed, (likely collisions detected):
          - `response` (dict): Suggests a new move.  
            - `type` (string): "play".  
            - `shape` (string): The name of the piece to place.  
            - `position` (array[float]): (X, Y) placement coordinates.  
            - `rotation` (float): Rotation in degrees.  
            - `timestamp` (string): Timestamp of the response.  
        - If no adjustment is needed:
          - `response` (dict):  
            - `type` (string): "finish".  
            - `timestamp` (string): Timestamp of the response.  
        """
        print("Feedback data:", data, "\n")
        if len(data["state"]["on_board"][self.randomShape]["collisions"]) > 0:
            return [
                {
                    "type": "play",
                    "shape": self.randomShape,
                    "position": (random.randint(5, 95), random.randint(5, 95)),
                    "rotation": random.choice(self.angles)
                },
                {"type": "chat", "message": "Test message"}
            ]
        return {"type": "finish"}

    async def chatRequest(self, data):
        """
        Function to handle a new chat message from the player.

        **Input:**
        - `data` (dict): Dictionary containing chat request data.  
          - `type` (string): "chatRequest".  
          - `objective` (string): The objective of the current game.  
          - `message` (string): Chat message sent by the player.  
          - `state` (dict): Game state information.  
            - `on_board` (dict): Pieces currently placed on the board.  
            - `off_board` (dict): Pieces not yet placed.  
          - `board_img` (string, base64): Image of the current board.  
          - `drawer_img` (string, base64): Image of the piece drawer.  
          - `timestamp` (string): Timestamp of the chat request.  

        **Output:**
        - `response` (dict): The reply message.  
          - `type` (string): "chat".  
          - `message` (string): Reply message.  
          - `timestamp` (string): Timestamp of the response.  
        """
        return {"type": "chat", "message": "Test Reply"}

    async def handleError(self, data):
        print("Error: ", data["message"])

    async def handle_connection(self, websocket):
        print("Client connected")

        # Map message types to methods.
        eventHandlers = {
            "playRequest": self.playRequest,
            "playFeedback": self.playFeedback,
            "chatRequest": self.chatRequest,
            "error": self.handleError
        }

        async for message in websocket:
            message = json.loads(message)
            event_type = message.get("type")
            print(f"Received request of type {event_type}")
            if event_type not in eventHandlers:
                response = "ERROR: Unknown request type"
            else:
                response = await eventHandlers[event_type](message)

            # Support sending either a list of responses or a single response.
            if isinstance(response, list):
                for res in response:
                    await websocket.send(json.dumps(res))
            else:
                await websocket.send(json.dumps(response))
            print("Sent response to client:\n", response)

    async def start_server(self, host="localhost", port=5000):
        async with websockets.serve(self.handle_connection, host, port):
            print(f"WebSocket server started on ws://{host}:{port}")
            await asyncio.Future()

    def shutDown(self, signal_num, frame):
        print("Shutting down the server...")
        sys.exit(0)

async def main():
    agent = TangramAgent()
    await agent.start_server()

if __name__ == "__main__":
    asyncio.run(main())