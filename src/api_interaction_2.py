from openai import OpenAI
import os

import base64 # needed to convert images into prompt-ready base64 format

MODEL = "gpt-4o"

api_key_str = ""
#print(api_key_str)

client = OpenAI(api_key=api_key_str)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


image_objective_path = "../PNG/task1.png"
base64_objective = encode_image(image_objective_path)



response = client.chat.completions.create(
  model=MODEL,
  messages=[
    {"role": "system", "content": "You are an AI-Player helping the Human Player arrange Tangram Pieces in a board in order to reach a certain objective. You should suggest a single move that would make the piece arrangement in the board closer or equal to the objective. A move should be suggested in the format (pieceName, new_center_x, new_center_y, rotation_degrees, flip_x, flip_y). flip_x and flip_y  are bool values in case you need to flip the orientation of the pieces in the given axis; rotation_degrees can only be 0 or 90 or 180 or 270. You should only answer back with a move in the format, no more information"},
    {"role": "user", "content": [
      { "type": "text", "text": "The objective of the game is the following:"},
      { "type": "image_url", "image_url": {
            "url": f"data:image/png;base64,{base64_objective}"
        }
      },
      { "type": "text", "text": "The board has the following corners: (0,0), (440,0), (0,576), (440, 576). The placed pieces have the following vertices: Bt1: (142.8, 350.6), (194, 299.4), (245.2, 350.6); Bt2: (39.8, 29.4), (142.2, 29.4), (91, 80.60001); St1: (156.4, 352.4), (182, 378), (207.6, 352.4); St2: (182.8, 379), (157.2, 353.4), (157.2, 404.6); Mdt: (208.6, 351.2), (259.8, 402.4), (259.8, 351.2); Sqr: (247.1019, 313.1019), (247.1019, 276.8981), (210.8981, 276.8981), (210.8981, 313.1019); Par: (248, 313.8981), (284.2039, 350.1019), (211.7961, 313.8981), (248, 350.1019). All pieces are placed on the board. What move should I make to reach or get closer to objetive image."},
    ]}
  ],
  max_tokens=100,
)

print(response.choices[0].message.content)
