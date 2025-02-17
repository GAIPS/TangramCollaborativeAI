import asyncio
import websockets
import signal
import sys
import threading
import time
import os
from openai import OpenAI
from copy import deepcopy
import json

from perform_plays import last_dir, last_piece, calculate_pos, direction_vectors

model = "gpt-4o"
temperature = 0.7
max_tokens = 1024

historyLimit = 20

print(os.getenv("OPENAI_API_KEY"))

client          = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

lastPlay = None

figures_names = ["Purple","Brown","Cream","Red","Yellow","Green","Blue"]
possible_directions = ["right", "left", "top", "bottom", "top-right", "top-left", "bottom-right", "bottom-left"]

chatLog = []

gameLogic = {
"type": "text", "text":"""Reference Information about the game: 
You and the human user are playing a tangram game, arranging the pieces to form an objective shape. 
The pieces are named by their colors: Red, Purple, Yellow, Green, Blue, Cream, and Brown.
Red and Cream are two large triangles, Yellow and green are two small triangles, Blue is a medium triangle, Purple is a small square, Brown is a tilted parallelogram.
We consider 0 degrees of rotation the triangles with their hypotenuse facing down, and the square in the square position (so the diamond shape corresponds to 45 degrees of rotation)
Example logical plays: Matching shapes can allow new larger shapes to appear, uniting two triangles of the same size by their Hypotenuse creates a square of that size in the location or a diamond (can be used as a circle) shape if the triangles are angled by 45 degrees. The Purple Square or a square created of 2 triangles can serve to form many things like heads, bodies, bases of structures. two triangles can also form a larger triangle when combined by their cathetus green and yellow can usually be used together or to fill similar objectives this could be used to make a another medium sized triangle like blue if used with yellow and green.
It often makes sense to use pieces of the same shape to furfil similar objectives, for example if theres 2 arms, it makes sense to use similar pieces for each.
"""
}

chatPrompt = {
"type": "text", "text": """You are an AI chatting with a Human Player thats arraging tangram tangram pieces with you and your co-assistents to reach a certain objective. 
To answer them, you will have access to the message history, an image of the current board, an image of the current piece drawer where the unplaced pieces lie.
Your task:
1. Review what you know about the game state.
2. Consider the players message and reply logically in an approachable and friendly way.

Rules:
- If you suggest moves or plays, always explicity describe how pieces should be placed in relation to each other.
- If you suggest either the move to create a large square or to create a large triangle, say it explicity. Ex: "Make a big square by using Cream and Red" or "Make a big triangle, placing Red to clockwise direction of Cream"
- Each individual piece, if present in a suggested move, should have a explicit rotation (except for the moves that form big squares and big triangles).
- If you disagree with an idea given by the player on how you should approach the challege, try to find a middle ground.
- If the game already looks finished to you, you can say it looks done.

Consider the previous messages and keep your message short, at most 1-3 sentences, the objective is a human-like nice short reply.
Remember you are collaborating so don't order ideias suggest them in a collaborative manner.
This message may not be the first in the conversation, but u can see the chat history in the previous message.
Examples:
- "Hey, well i think we could begin with the tail, using the medium blue triagle for it."
- "Ok, got it, i'll try to help you achieve that."
- "Alright I'll try to use the brown piece to create a tail."
- "I don't think the yellow piece would make a good roof due to it's size, maybe we could use cream for the same objective."
- "Sounds great, let's begin then!"
- "I think the game already looks like our objective."
"""
}

async def send_GPT_play_request(objective : str, game_state : str, board_img, drawer_img):

    messages = chatLog[max(0,len(chatLog) - historyLimit):]

    messages.append()

    messages.append({
		"role": "system",
		"content": [
			gameLogic,
			{"type": "text", "text":"You are an AI-Player helping the Human Player arrange Tangram Pieces in a board in order to create " + objective + '''. 
		A move involves moving one of the tangram pieces on the board or placing a piece on the board from the piece drawer. 

		NEVER use a piece in the drawer as a reference in any of the following
		
		You will receive the current game state in an image format, an image showing the state of the piece drawer, 
		a dictionary specifying the current rotation value of each piece, the full chat history between you (you're the AI) and the player 
		and an history of all played moves, by the player and the AI.  

		After analysing the given image of the state you should suggest your moves in one of the following ways:
		
		You can describe a relative position, done in relation to pieces already placed on the board by indicating which side 
		(right, left, top, bottom, top-right, top-left, bottom-right, bottom-left) of them the piece to be moved should be placed. 
		A move can be done in relation to a reference piece or more.
		You can rotate a piece rotate in a move, always try to describe move rotation in terms of explicit degrees to add, 
		avoid using phrases which require deducting or interpreting the rotation values.
		Example: Place Red to the left of Cream with a 90º rotation.
		This is your main way to play, you should only use the next ones if they match exactly what you consider the best move.
		
		You can suggest to make a Square/diamond shape using a pair of triangles. By moving one of them to next to one already on the board.
		The triangle pair must consist of Cream and Red OR Green and Yellow, since these match in size.
		Whenever suggesting a square creation move, you need to say \"Form a Square\" and then the triangle that needs to be placed followed by the referenced triangle.
		Example: Form a Square by putting Cream next to Red (note, here red the one that MUST be already on the board, we would be moving cream, you can make this more clear in your replies)
		
		You can suggest to make a larger Triangle by using a pair of smaller triangles. One of them must already be on the board for the move to be valid.
		Since this move leads to two possible positions and may be applied on different orientations, you must indicate if the triangle is placed clockwise or anticlockwise from the reference triangle.
		The triangle pair must also consist of Cream and Red OR Green and Yellow.
		Whenever suggesting a triangle creation move, you need to say \"Form a Triangle by placing\" and then the triangle piece name to be placed, followed by clockwise or anticlockwise, and then the reference triangle piece name.
		Example: Form a Triangle by placing Cream anticlockwise from Red

		You can simply rotate a piece without moving it, \"Just rotate\" and then the piece and the rotation you intend for it to have.
		Example: Just rotate Blue 90

		If and only if you believe the objective has already been achieved, that is if you think it looks close enough to the objective then say \"Looks finished\" followed by a small friendly message to the human player.
		Example: Looks finished: I think this already resembles our objective well. Do you agree?
		
		KEEP IN MIND THE PLAY YOU SHOULD MAKE THE MOST IS THE RELATIVE MOVE
		
		You should always follow the commands and reasoning in the chat history behind the user and the AI. 
		ALWAYS check and respect if you promised something in a recent previous message that wasnt been done yet.
		User commands prevail above AI commands, in case they conflict, as well as newest messages above older ones. 
		Following the chat instructions and considering the state of the game, 
		list all moves that should be done in order to create ''' + objective + ", providing explanations for each one."
		}]
	})

    messages.append({
		"role": "user",
		"content": [
			{"type": "text", "text": "The image of the current board is: "},
			{"type": "image_url", "image_url": {
				"url": board_img
			}},
			{"type": "text", "text": "The image of the current piece drawer is: "},
			{"type": "image_url", "image_url": {
				"url": drawer_img
			}},
			{"type": "text", "text": "The current rotation values of the pieces are: " + game_state},
			{"type": "text", "text": "Give me a list of the moves to play in order to create " + objective}
		]
	})

    response = client.chat.completions.create(
        model=model,
        messages= messages,
        temperature=0.7,
        max_tokens = max_tokens
    )
    
    return response.choices[0].message.content

async def send_GPT_Move_Extraction_Request(play):
    messages = []

    messages.append({
		"role": "system",
		"content": f'''
		You are currently extracting the first move from a detailed play suggestion by the AI. 
		You must convert that move into one of the following grammars formats: 
			- [PieceToMove], [Direction], [PieceOnBoard], (Optional: [Direction], [PieceOnBoard], ...), [DegreesOfRotation], [FlipXAxis], [FlipYAxis]. 
			Where any piece name is a valid name piece between the names {str(figures_names)}, any direction is one of the following
			{str(possible_directions)}, any rotation degrees value must be 0,45,90,135,180,225,270,315 and any flip value is 0 or 1 (if not mentioned 0).
			This format is the default one, except when special moves for triangle and square creation are suggested.
			- Square [reference piece] [piece to move]
			This format is only used when a suggested move says something along the lines of \"Form a Square with\" and then two triangle pieces names, note which one is being moved and which one is already in place.
			- Triangle [reference piece] [direction] [piece to move]
			Where direction is either clockwise or anticlockwise.
			This format is only used when a suggested move says something along the lines of \"Form a triangle with\" and then two triangle pieces names and a direction, note which one is being moved and which one is already in place.
			- Finish: [Message]
			This format is only used when a suggested move says something along the lines of \"Looks finished\" or something of the type, message should be a friendly message to the human.
			- Rotate [piece to rotate] [rotation]
			This format is only used when a suggested move says something along the lines of \"Just rotate\" or something of the type, rotation should be the suggested one.
					
		For example (for each possible grammar): 
		Cream, right, Red, 90, 0, 0. 
		Square Cream Red
		Triangle Cream clockwise Red
		
		You should ONLY RESPOND WITH THE MOVE IN ONE OF THE THREE GRAMMAR FORMATS. 
		'''
	})
	
    messages.append({
		"role": "user",
		"content": [
			{ "type": "text", "text" : "Extract the first move from this list of suggested moves: " + play}
		]
	})
	
    response = client.chat.completions.create(
        model=model,
        messages= messages,
        temperature=temperature,
        max_tokens = max_tokens
    )
    
    return response.choices[0].message.content

async def send_GPT_Reasoning_Extraction_Request(play):
    messages = []
	
    messages.append({
		"role": "system",
		"content": "You are currently extracting ONLY the reasoning behind the first move from a list of suggested moves. No need for any text beside the reasoning in the response you'll provide."
	})
	
    messages.append({
		"role": "user",
		"content": [
			{ "type": "text", "text" : "What is the reasoning behind the first suggested step of the following list?" + play}
		]
	})
    
    response = client.chat.completions.create(
        model=model,
        messages= messages,
        temperature=temperature,
        max_tokens = max_tokens
    )

    chatLog.append({"role": "assistant", "content": response.choices[0].message.content})
    
    return response.choices[0].message.content
    

async def start_play(data):

    board_img = data["board_img"]
    drawer_img = data["drawer_img"]
    
    game_state_dict = data["state"]

    objective = data["objective"]

    lastPlay = await send_GPT_play_request(objective, str(game_state_dict), board_img, drawer_img)

    reasoning_req = send_GPT_Reasoning_Extraction_Request(lastPlay)
    move_req = send_GPT_Move_Extraction_Request(lastPlay)

    reasoning, move = asyncio.gather(reasoning_req, move_req)

    return {"reasoning": reasoning, "move": calculate_pos(move)}

async def continue_play(data):

    game_state_dict = data["state"]

    if last_dir == None or last_piece == None or not game_state_dict["on_board"][last_piece]["conflist"]["is_in_conflict"]: # Not sure if boolean from godot is interpreted as boolean here
        move = "FINISH"
    else:
        pos = (game_state_dict["on_board"][last_piece]["position"][0] + direction_vectors[last_dir][0], 
               game_state_dict["on_board"][last_piece]["position"][1] + direction_vectors[last_dir][1])
        move = (last_piece, pos, game_state_dict["on_board"][last_piece]["rotation"])
    
    return {"move": move}

async def send_GPT_message_query(objective : str, game_state : str, user_msg : str, board_img, drawer_img):

    messages = chatLog[max(0,len(chatLog) - historyLimit):]

    messages.append({
		"role": "user",
		"content": [
			gameLogic,
			{"type": "text", "text": "Your objetive this game is to form the shape of " + objective + "."},
			chatPrompt,
			{"type": "text", "text": "Game image:"},
			{"type": "image_url", "image_url": {
				"url": board_img
			}},
			{"type": "text", "text": "Current piece drawer image:\n"},
			{"type": "image_url", "image_url": {
				"url": drawer_img
			}},
			{"type": "text", "text": "Current piece rotations:\n" + game_state + '\n'}
		]
	})
	
    messages.append({"role": "user", "content": user_msg})

    chatLog.append({"role": "user", "content": user_msg})
	
    response = client.chat.completions.create(
        model=model,
        messages= messages,
        temperature=temperature,
        max_tokens = max_tokens
    )

    return response.choices[0].message.content


async def message_query(data):

    board_img = data["board_img"]
    drawer_img = data["drawer_img"]
    
    game_state_dict = data["state"]
    objective = data["objective"]
    user_msg = data["message"]

    ai_msg = await send_GPT_message_query(objective, str(game_state_dict), user_msg, board_img, drawer_img)

    return {"type": "chat", "message": ai_msg}

def shutDown(signal, frame):
    print("\Shutting down the server...")
    sys.exit(0)

# Register the signal handler for SIGINT (Ctrl-C) and SIGTERM (termination)
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)


async def handle_connection(websocket):
    print("Client connected")

    eventHandlers = {
        "playRequest" : start_play,
        "playFeedback" : continue_play,
        "chatRequest" : message_query
    }

    async for message in websocket:
        print(f"Received from client: {message}")
        message = json.loads(message)
        if(message["type"] not in eventHandlers):
            response = "ERROR: Unknown request type"
        
        else:
            response = await eventHandlers[message["type"]](message)

        await websocket.send(json.dumps(response))
        print(f"Sent to client: {response}")

async def start_server():
    async with websockets.serve(handle_connection, "localhost", 5000):
        print("WebSocket server started on ws://localhost:5000")
        await asyncio.Future()

asyncio.run(start_server())