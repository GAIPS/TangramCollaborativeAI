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

image_board_path = "../PNG/GPT4_testing/tab_casa_falta_1.png"
image_objective_path = "../PNG/task1.png"
image_piecesleft_path = "../PNG/GPT4_testing/restam0.png"

base64_board = encode_image(image_board_path)
base64_objective = encode_image(image_objective_path)
#base64_piecesleft = encode_image(image_piecesleft_path)


response = client.chat.completions.create(
  model=MODEL,
  messages=[
    {"role": "system", "content": "You are an AI-Player helping the Human Player arrange Tangram Pieces in a board in order to reach a certain objective. You are currently playing your move which involves moving one of the tangram pieces on the board. You can flip or rotate a piece in a move. Don't move any pieces already in the correct position."},
    {"role": "user", "content": [
      { "type": "text", "text": "The following 2 images represent, in the given order: the objective, the current board. The names of the pieces are Bt1, Bt2, St1, St2, Mdt, Sqr, Par. Tell me which move should I make"},
      { "type": "image_url", "image_url": {
            "url": f"data:image/png;base64,{base64_objective}"
        }
      },
      { "type": "image_url", "image_url": {
            "url": f"data:image/png;base64,{base64_board}"
        }
      },
      #{ "type": "image_url", "image_url": {
      #      "url": f"data:image/png;base64,{base64_piecesleft}"
      #  }
      #},
    ]}
  ],
  max_tokens=1024,
)

print(response.choices[0].message.content)
play = response.choices[0].message.content

print("\n\n PROCESSING RESPONSE \n\n")

response = client.chat.completions.create(
  model=MODEL,
  messages=[
    {"role": "system", "content": "You are an AI-Player helping the Human Player arrange Tangram Pieces on a board to reach a certain objective. Convert the move suggestion into piece coordinates, rotation degrees, and possible flipping. Answer in the format: (name, posx, posy, rotation, orientation_x, orientation_y) followed by explanation. orientation_x or y should be only 0 or 1, depending on if you flipped the piece or not in that axis. rotation_degrees should only be 0, 90, 180 or 270"},
    {"role": "user", "content": 
      [
        {"type": "text", "text": f"This is the play you are supposed to perform: {play}"},
        {"type": "text", "text": "The board has the following corners: (0,0), (440,0), (0,576), (440,576). The placed pieces have the following vertices: Bt1: (142.8, 350.6), (194, 299.4), (245.2, 350.6); Bt2: (39.8, 29.4), (142.2, 29.4), (91, 80.60001); St1: (156.4, 352.4), (182, 378), (207.6, 352.4); St2: (182.8, 379), (157.2, 353.4), (157.2, 404.6); Mdt: (208.6, 351.2), (259.8, 402.4), (259.8, 351.2); Sqr: (247.1019, 313.1019), (247.1019, 276.8981), (210.8981, 276.8981), (210.8981, 313.1019); Par: (248, 313.8981), (284.2039, 350.1019), (211.7961, 313.8981), (248, 350.1019). All pieces are placed on the board. What move should I make to reach or get closer to the objective image."}
      ]
    }
  ],
  max_tokens=1024,
)

final_move = response.choices[0].message.content
print(final_move)

