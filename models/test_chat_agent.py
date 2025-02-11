import asyncio
import websockets
import json
import base64

def encode_image(image_path):
    """Reads an image file and encodes it in base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def send_game_state():
    uri = "ws://localhost:5000"

    # Specify your image paths
    board_img_path = "board_img.png"  # Change this to the actual file path
    drawer_img_path = "drawer_img.png"  # Change this to the actual file path

    # Encode images
    board_img_base64 = encode_image(board_img_path)
    drawer_img_base64 = encode_image(drawer_img_path)

    # Construct the JSON payload
    game_state = {
        "type" : "message_query",
        "objective": "A cat",
        "game_state_dict": {
            "on_board": {
                "piece_A": {
                    "position": {
                        "V1": {"x_pos": 10, "y_pos": 20},
                        "V2": {"x_pos": 30, "y_pos": 20},
                        "V3": {"x_pos": 20, "y_pos": 40},
                        "VCenter": {"x_pos": 20, "y_pos": 30}
                    },
                    "rotation": 90,
                    "conflict": {
                        "is_in_conflict": False,
                        "what": ["piece_B", "BOUNDARY"]
                    }
                },
                "piece_B": {
                    "position": {
                        "V1": {"x_pos": 50, "y_pos": 60},
                        "V2": {"x_pos": 70, "y_pos": 60},
                        "V3": {"x_pos": 60, "y_pos": 80},
                        "VCenter": {"x_pos": 60, "y_pos": 70}
                    },
                    "rotation": 45,
                    "conflict": {
                        "is_in_conflict": False,
                        "what": []
                    }
                }
            },
            "off_board": {
                "piece_C": {
                    "position": {
                        "V1": {"x_pos": 5, "y_pos": 10},
                        "V2": {"x_pos": 15, "y_pos": 10},
                        "V3": {"x_pos": 10, "y_pos": 20},
                        "VCenter": {"x_pos": 10, "y_pos": 15}
                    },
                    "rotation": 0,
                    "conflict": {
                        "is_in_conflict": False,
                        "what": []
                    }
                }
            }
        },
        "board_img": f"data:image/png;base64,{board_img_base64}",
        "drawer_img": f"data:image/png;base64,{drawer_img_base64}",
        "user_msg" : "What do you see ?"
    }

    async with websockets.connect(uri) as websocket:
        # Send JSON data
        await websocket.send(json.dumps(game_state))

        # Wait for a response
        response = await websocket.recv()
        print("Response from server:", response)

# Run the WebSocket client
asyncio.run(send_game_state())
