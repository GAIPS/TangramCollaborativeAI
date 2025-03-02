from flask import Flask, request, jsonify
import random
import signal
import sys

class TangramAgent:
    def __init__(self):
        
        self.angles = list(range(0, 361, 45))
        self.shapes = ["Red", "Green", "Blue", "Yellow", "Purple", "Cream", "Brown"]
        self.randomShape = random.choice(self.shapes)
        self.app = self._create_flask_app()
        
        signal.signal(signal.SIGINT, self.shutDown)
        signal.signal(signal.SIGTERM, self.shutDown)

    def playRequest(self, data):
        """
        Function to handle a new play request from the game.
        This method can be overridden by subclasses.

        **Input:**
        - `data` (dict): Dictionary containing the play request data.  

        **Output:**
        Single play type reply or list containing one play type reply and chat type replies.
        """
        self.randomShape = random.choice(self.shapes)
        return {
                "type": "play",
                "shape": self.randomShape,
                "position": (random.randint(5, 95), random.randint(5, 95)),
                "rotation": random.choice(self.angles)
            }

    def playFeedback(self, data):
        """
        Function to handle a feedback about the latest play from the game.
        This method can be overridden by subclasses.

        **Input:**
        - `data` (dict): Dictionary containing play feedback.  

        **Output:**
        Single play type reply or list containing one play type reply and chat type replies.
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

    def chatRequest(self, data):
        """
        Function to handle a new chat message from the player.
        This method can be overridden by subclasses.

        **Input:**
        - `data` (dict): Dictionary containing chat request data.  

        **Output:**
        - `response` (dict): The reply message.  
        """
        return {"type": "chat", "message": "Test Reply"}

    def handleError(self, data):
        """
        Function to handle errors from the game.
        This method can be overridden by subclasses.

        **Input:**
        - `data` (dict): Dictionary containing error data.

        **Output:**
        - `response` (dict): Error handling response.
        """
        print("Error: ", data["message"])
        return {"type": "error", "message": "Error received and processed"}

    def shutDown(self, signal_num, frame):
        """
        Function to handle shutdown signals.
        This method can be overridden by subclasses.
        """
        print("Shutting down the server...")
        sys.exit(0)

    def _create_flask_app(self):
        """
        Internal method to create and configure the Flask application.
        This method sets up all the routes for the Tangram game interactions.
        """
        app = Flask(__name__)
        
        @app.route('/play-request', methods=['POST'])
        def play_request():
            data = request.json
            print(f"Received play request: {data}")
            response = self.playRequest(data)
            print("Sending response:", response)
            return jsonify(response)
        
        @app.route('/play-feedback', methods=['POST'])
        def play_feedback():
            data = request.json
            print(f"Received play feedback: {data}")
            response = self.playFeedback(data)
            
            # If response is a list, handle it accordingly
            if isinstance(response, list):
                return jsonify({"multi_response": True, "responses": response})
            else:
                return jsonify(response)
        
        @app.route('/chat-request', methods=['POST'])
        def chat_request():
            data = request.json
            print(f"Received chat request: {data}")
            response = self.chatRequest(data)
            print("Sending response:", response)
            return jsonify(response)
        
        @app.route('/error', methods=['POST'])
        def error_handler():
            data = request.json
            print(f"Received error: {data}")
            response = self.handleError(data)
            return jsonify(response)
        
        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "up", "message": "Tangram agent is running"})
            
        return app
    

    def run(self, host="localhost", port=5001, debug=False):
        """
        Start the Flask server for the Tangram agent.
        
        Args:
            host (str): The host to bind to
            port (int): The port to bind to
            debug (bool): Whether to run Flask in debug mode
        """
        print(f"Starting Flask server for TangramAgent on {host}:{port}...")
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    agent = TangramAgent()
    agent.run()