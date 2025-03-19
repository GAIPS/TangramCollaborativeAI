import asyncio
import os
from openai import OpenAI
from datetime import datetime
import re
from models.templates.tangramAgent import TangramAgent

class CustomAgent(TangramAgent):

    def __init__(self):
        super().__init__()
        self.chatLog = []
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.max_tokens = 1024
        self.historyLimit = 20
        self.client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

        self.gameLogic = {
"type": "text", "text":"""Reference Information about the game: 
You and the human user are playing a tangram game, arranging the pieces to form an objective shape. 
The pieces are named by their colors: Red, Purple, Yellow, Green, Blue, Cream, and Brown.
Red and Cream are two large triangles, Yellow and green are two small triangles, Blue is a medium triangle, Purple is a small square, Brown is a tilted parallelogram.
We consider 0 degrees of rotation the triangles with their hypotenuse facing down, and the square in the square position (so the diamond shape corresponds to 45 degrees of rotation)
Example logical plays: Matching shapes can allow new larger shapes to appear, uniting two triangles of the same size by their Hypotenuse creates a square of that size in the location or a diamond (can be used as a circle) shape if the triangles are angled by 45 degrees. The Purple Square or a square created of 2 triangles can serve to form many things like heads, bodies, bases of structures. two triangles can also form a larger triangle when combined by their cathetus green and yellow can usually be used together or to fill similar objectives this could be used to make a another medium sized triangle like blue if used with yellow and green.
It often makes sense to use pieces of the same shape to furfil similar objectives, for example if theres 2 arms, it makes sense to use similar pieces for each.
"""
}
        self.chatPrompt = {
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
        # Relative Moves Agent specific "global" variables
        self.figure_names = ["Purple","Brown","Cream","Red","Yellow","Green","Blue"]
        self.possible_directions = ["right", "left", "top", "bottom", "top-right", "top-left", "bottom-right", "bottom-left"]
        self.current_play = {"move": "", "reasoning": "", "is_more_than_one_step": False} #Guarantee to always step to False post these types of moves

        self.direction_vectors = {
                "right": [1, 0],
                "left": [-1, 0],
                "top": [0, 1],
                "bottom": [0, -1],
                "top-right": [1, 1],
                "top-left": [-1, 1],
                "bottom-right": [1, -1],
                "bottom-left": [-1, -1]
        }

        self.last_dir = [0,0]
        self.last_piece = ""
        self.distance_increment = 10 #Tweak accordingly, since websockets are used no problem in using small values
        
    async def playRequest(self, data):
        """
        Function to handle a new play request from the game. Modify this function to implement your own agent.
        See Superclass TangramAgent or Api description for input/output formats.

        RELATIVE MOVES AGENT:
        - 1st GPT query: Ask for an extensive play following prompt's rules
        - 2nd GPT query: Based on GPT extensive response, extract only the first move
        - 3rd GPT query: Based on GPT extensive response, extract the reasoning behind the suggested move
        """

        #TODO: add exceptions to handle GPT returning errors, NOTE: PROTOCOL DOESN'T ACCOUNT FOR ERRORS HERE YET, MUST FIX IT
        
        response_GPT_play_extensive_query =  await self.send_GPT_play_extensive_query(data)

        # print("DEBUG - EXTENSIVE PLAY:" + response_GPT_play_extensive_query)

        response_move_extraction = await self.send_GPT_move_extraction_query(response_GPT_play_extensive_query)
        response_reasoning_extraction = await self.send_GPT_reasoning_extraction_query(response_GPT_play_extensive_query)


        self.current_play["move"] = response_move_extraction
        self.current_play["reasoning"] = response_reasoning_extraction
        
        move_data = self.current_play["move"].split(" ")

        response_for_godot = {}

        if self.current_play["move"].startswith("Square"):
            response_for_godot = await self.getSquareResponse(data, move_data[1], move_data[2])
        #elif self.current_play["move"].startswith("Triangle"): #REMOVED
        #    response_for_godot = await self.getTriangleResponse(data, move_data[1], move_data[2], move_data[3]) #REMOVED
        elif self.current_play["move"].startswith("Finish"):
            pass # Currently not supported
        elif self.current_play["move"].startswith("Rotate"):
            response_for_godot = await self.getRotationResponse(data, move_data[1], move_data[2])
        else:
            response_for_godot = await self.getRelationalResponse(data, self.current_play["move"])
        
        #breakpoint() #DEBUG
        #if(response_for_godot['type'] != "error"):
        return response_for_godot
        #else:
        #    pass # Currently not supported

    
    async def send_GPT_play_extensive_query(self, data):
        
        # Add the previous chat history before the query
        messages = self.chatLog[max(0,len(self.chatLog) - self.historyLimit):]


        play_extensive_query_instructions = f'''
        You are an AI-Player helping the Human Player arrange Tangram Pieces in a board in order to create {data["objective"]}.
                                                
		A move involves moving one of the tangram pieces on the board or placing a piece on the board from the piece drawer. 

		NEVER use a piece in the drawer as a reference in any of the following
		
		You will receive the current game state in an image format, an image showing the state of the piece drawer, a dictionary specifying the current rotation value of each piece, the full chat history between you (you're the AI) and the player (available at the beginning of this prompt)
		and an history of all played moves, by the player and the AI.  

		After analysing the given image of the state you should suggest your moves in one of the following ways:
		
		You can describe a relative position, done in relation to pieces already placed on the board by indicating which side 
		(right, left, top, bottom, top-right, top-left, bottom-right, bottom-left) of them the piece to be moved should be placed. 
		A move can be done in relation to a single reference piece (ex: Blue right Purple) or more (ex: Blue right Purple top Red).
		You can rotate a piece rotate in a move, always try to describe move rotation in terms of explicit degrees to add, 
		avoid using phrases which require deducting or interpreting the rotation values.
		Example: Place Red to the left of Cream with a 90º rotation.
		This is your main way to play, you should only use the next ones if they match exactly what you consider the best move.
		
		You can suggest to make a Square/diamond shape using a pair of triangles. By moving one of them to next to one already on the board.
		The triangle pair must consist of Cream and Red OR Green and Yellow, since these match in size.
		Whenever suggesting a square creation move, you need to say \"Form a Square\" and then the triangle that needs to be placed followed by the referenced triangle.
		Example: Form a Square by putting Cream next to Red (note, here red the one that MUST be already on the board, we would be moving cream, you can make this more clear in your replies)
		
		You can simply rotate a piece without moving it, \"Just rotate\" and then the piece and the rotation you intend for it to have.
		Example: Just rotate Blue 90

		If and only if you believe the objective has already been achieved, that is if you think it looks close enough to the objective then say \"Looks finished\" followed by a small friendly message to the human player.
		Example: Looks finished: I think this already resembles our objective well. Do you agree?
		
		KEEP IN MIND THE PLAY YOU SHOULD MAKE THE MOST IS THE RELATIVE MOVE
		
		You should always follow the commands and reasoning in the chat history behind the user and the AI. 
		ALWAYS check and respect if you promised something in a recent previous message that wasnt been done yet.
		User commands prevail above AI commands, in case they conflict, as well as newest messages above older ones. 
		Following the chat instructions and considering the state of the game, 
		list all moves that should be done in order to create {data["objective"]}, providing explanations for each one.
        '''

        ''' REMOVED
		You can suggest to make a larger Triangle by using a pair of smaller triangles. One of them must already be on the board for the move to be valid.
		Since this move leads to two possible positions and may be applied on different orientations, you must indicate if the triangle is placed clockwise or anticlockwise from the reference triangle.
		The triangle pair must also consist of Cream and Red OR Green and Yellow.
		Whenever suggesting a triangle creation move, you need to say \"Form a Triangle by placing\" and then the triangle piece name to be placed, followed by clockwise or anticlockwise, and then the reference triangle piece name.
		Example: Form a Triangle by placing Cream anticlockwise from Red
        '''

        # Add the System messages, gameLogic + Explanation on how to find the next play based on info provided
        messages.append({  
            "role":"system",
            "content": [
                self.gameLogic,
                {"type":"text", "text":play_extensive_query_instructions}]
        })

        # Add the User messages
        messages.append({
		"role": "user",
		"content": [
			{"type": "text", "text": "The image of the current board is: "},
			{"type": "image_url", "image_url": {
				"url": "data:image/png;base64," + data["board_img"]
			}},
			{"type": "text", "text": "The image of the current piece drawer is: "},
			{"type": "image_url", "image_url": {
				"url": "data:image/png;base64," + data["drawer_img"]
			}},
			{"type": "text", "text": "The current values of the pieces are: " + str(data["state"])}, # FIX TO ONLY GIVE ROTATION VALUES, SINCE IT'S THE ONLY RELEVANT THING FOR THIS AGENT
			{"type": "text", "text": "Give me a list of the moves to play in order to create " + data["objective"]}
		]
	})
        
        # print("DEBUG - THIS IS WHAT IS BEING SENT TO GPT ON EXTENSIVE PLAY QUERY: " + str(messages))

        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature = self.temperature,
            max_tokens = self.max_tokens
        )
        
        return response.choices[0].message.content

    debug_num = 0

    async def send_GPT_move_extraction_query(self, response_GPT_play_extensive_query):
        messages = []

        play_move_extraction_instructions = f"""
        You are currently extracting the first move from a detailed play suggestion by the AI. 
		You must convert that move into one of the following grammars formats: 
			- [PieceToMove], [Direction], [PieceOnBoard], (Optional: [Direction], [PieceOnBoard], ...), [DegreesOfRotation], [FlipXAxis], [FlipYAxis]. 
			Where any piece name is a valid name piece between the names {str(self.figure_names)}, any direction is one of the following {str(self.possible_directions)}, any rotation degrees value must be 0,45,90,135,180,225,270,315 and any flip value is 0 or 1 (if not mentioned 0).
			This format is the default one, except when special moves for triangle and square creation are suggested.
			- Square [reference piece] [piece to move]
			This format is only used when a suggested move says something along the lines of \"Form a Square with\" and then two triangle pieces names, note which one is being moved and which one is already in place.
			- Finish: [Message]
			This format is only used when a suggested move says something along the lines of \"Looks finished\" or something of the type, message should be a friendly message to the human.
			- Rotate [piece to rotate] [rotation]
			This format is only used when a suggested move says something along the lines of \"Just rotate\" or something of the type, rotation should be the suggested one.
					
		For example (for each possible grammar): 
		Cream, right, Red, 90, 0, 0. 
		Square Cream Red
		
		You should ONLY RESPOND WITH THE MOVE IN ONE OF THE THREE GRAMMAR FORMATS. 
        """
		
        ''' Removed - Not really used and hard to implement oustide godot environment

		    - Triangle [reference piece] [direction] [piece to move]
			Where direction is either clockwise or anticlockwise.
			This format is only used when a suggested move says something along the lines of \"Form a triangle with\" and then two triangle pieces names and a direction, note which one is being moved and which one is already in place.

        Triangle Cream clockwise Red
        '''

        # System messages
        messages.append({
            "role":"system",
            "content":play_move_extraction_instructions
        })

        # User messages
        messages.append({
            "role":"user",
            "content":[
                {"type":"text","text" : "Extract the first move from this list of suggested moves: " + response_GPT_play_extensive_query}
            ]
        })

        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature = self.temperature,
            max_tokens = self.max_tokens
        )
        
        
        return response.choices[0].message.content



    async def send_GPT_reasoning_extraction_query(self, response_GPT_play_extensive_query):
        messages = []

        messages.append({
            "role": "system",
            "content": "You are currently extracting ONLY the reasoning behind the first move from a list of suggested moves. No need for any text beside the reasoning in the response you'll provide. Try to summarise the reasoning into non-technical terms when doing so."
            })

        messages.append({
            "role": "user",
            "content": [
                    { "type": "text", "text" : "What is the reasoning behind the first suggested step of the following list?" + response_GPT_play_extensive_query}
                ]
            })

        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature = self.temperature,
            max_tokens = self.max_tokens
        )

        return response.choices[0].message.content

    async def getSquareResponse(self, data, refPiece, movePiece):

        valid_pairs = [["Red", "Cream"], ["Yellow", "Green"]]

        if refPiece not in data["state"]["on_board"].keys() and movePiece not in data["state"]["on_board"].keys():
            return {"type":"error", "message": "At least one Piece used in a Square type move must be present on the board"}

        for pair in valid_pairs:
            if refPiece in pair and movePiece in pair and movePiece != refPiece:
                
                #NOTE: logic reworked since snap points are not returned by godot, it must be handled by the agent
                snap_pos = await self.calculateSquareSnapPos(data["state"]["on_board"][refPiece]["position"])
                
                if data["state"]["on_board"][refPiece]["rotation"]+180 >= 360:
                    ref_rotation = data["state"]["on_board"][refPiece]["rotation"]+180 - 360
                else:
                    ref_rotation= data["state"]["on_board"][refPiece]["rotation"]+180 
                
                #breakpoint()
                return await self.parsePlayResponse(movePiece,snap_pos,ref_rotation)
    
        return {"type":"error", "message": "The chosen pieces don't create a Square when used in a Square type move"}

    async def calculateSquareSnapPos(self, refPiecePositionData):
        
        #breakpoint() #DEBUG
        
        # Extract reference triangle data
        position = await self.extract_floats(refPiecePositionData["position"])  # [x, y]
        vertices = [ await self.extract_floats(x) for x in refPiecePositionData["vertices"]]  # [[x1, y1], [x2, y2], [x3, y3]]

        # Find the hypotenuse midpoint
        mid_x = (vertices[1][0] + vertices[2][0]) / 2
        mid_y = (vertices[1][1] + vertices[2][1]) / 2

        # Find the vector to apply to reach the mid hypotenuse point from the center
        vec_x =  mid_x - position[0]
        vec_y = mid_y - position[1]

        # To reach the other center, the vector needs to have double the length
        vec_x = vec_x*2.2 #NOTE: A little bit more than 2 to ensure no collision afterwards 
        vec_y = vec_y*2.2

        return [position[0]+vec_x, position[1]+vec_y]

    '''
    async def getTriangleResponse(self, data, refPiece, orientation, movePiece):
        valid_pairs = [["Red", "Cream"], ["Yellow", "Green"]]

        if refPiece not in data["state"]["on_board"].keys() and movePiece not in data["state"]["on_board"].keys():
            return {"type":"error", "message": "At least one Piece used in a Triangle type move must be present on the board"}

        for pair in valid_pairs:
            if refPiece in pair and movePiece in pair and refPiece != movePiece:
                
                #Based on the different rotation values the reference triangle could have, 
                #pick the correct placement for the triangle
                
                #breakpoint()

                #NOTE: logic reworked since snap points are not returned by godot, it must be handled by the agent
                snap_pos = await self.calculateTriangleSnapPos(data["state"]["on_board"][refPiece]["position"], orientation)

                if orientation == "clockwise":
                    ref_rotation = data["state"]["on_board"][refPiece]["rotation"] + 90
                elif orientation == "anticlockwise":
                    ref_rotation = data["state"]["on_board"][refPiece]["rotation"] + 270
                
                if ref_rotation >= 360:
                    ref_rotation = ref_rotation - 360
                
                return await self.parsePlayResponse(movePiece,snap_pos,ref_rotation)
            
        return {"type":"error", "message": "The chosen pieces don't create a Triangle when used in a Triangle type move"}

    async def calculateTriangleSnapPos(self, refPiecePositionData, orientation):
        
        
        # Extract reference triangle data
        position = await self.extract_floats(refPiecePositionData["position"])  # [x, y]
        vertices = [ await self.extract_floats(x) for x in refPiecePositionData["vertices"]]  # [[x1, y1], [x2, y2], [x3, y3]]

        # clockwise - snap to V1-V2, apply vec with direction of the other edge (V1-V3)
        # anticlockwise - snap to V1-V3, apply vec with direction of V1-V2

        vec_x = 0
        vec_y = 0

        if orientation == "clockwise":
            vec_x = (vertices[2][0] + vertices[0][0])*0.25 #ADJUST VALUE FOR BETTER PERFORMANCE
            vec_y = (vertices[2][1] - vertices[0][1])*0.25

        elif orientation == "anticlockwise":
            vec_x = (vertices[1][0] - vertices[0][0])*0.25 #ADJUST VALUE FOR BETTER PERFORMANCE
            vec_y = (vertices[1][1] - vertices[0][1])*0.25

        return [position[0]+vec_x,position[1]+vec_y]
    '''

    async def getRotationResponse(self, data, piece, rot):
        if piece not in data["state"]["on_board"].keys():
            return {"type":"error", "message": "It is only possible to rotate pieces currently on the board"}

        pos = self.extract_floats(data["state"]["on_board"][piece]["position"]["position"])
        rot = int(data["state"]["on_board"][piece]["rotation"]) + rot #Ensure no problems with possible negative rotation values

        return await self.parsePlayResponse(piece,pos,rot)

    async def getRelationalResponse(self,data,move):

        # print('DEBUG: Suggested play is:' + move)

        relational_play_parts = move.split(", ")
        num_direction_piece_pairs = ((len(relational_play_parts) - 6) / 2) + 1 # 4 fields are mandatory to be filled. 1 pair always exists for the mandatory direction-piece pair

        piece_to_move = relational_play_parts[0]
        if piece_to_move not in self.figure_names:
            return {"type":"error", "message": "Piece to be moved has invalid name"}

        piece_to_move_location = "on_board"
        if data["state"]["on_board"].get(piece_to_move) == None:
            piece_to_move_location = "off_board"

        #breakpoint()
        # There is an edge case where multiple pieces have the same vector direction, we must find a common starting coordinate and apply the vector
        is_all_same_direction = True
        first_direction = relational_play_parts[1]

        pairs_iterator = 1
        direction_and_related_piece = {}
        while num_direction_piece_pairs != 0:
            direction = relational_play_parts[pairs_iterator]
            if direction not in self.possible_directions:
                return {"type":"error", "message": "Direction provided is invalid"}
                
            relatedPiece = relational_play_parts[pairs_iterator+1]
            if relatedPiece not in self.figure_names:
                return {"type":"error", "message": "Piece to be moved has invalid name"}
                
            direction_and_related_piece[relatedPiece] = direction
            if direction != first_direction:
                is_all_same_direction = False
            
            pairs_iterator += 2
            num_direction_piece_pairs -= 1
        
        # TODO: for some reason whe it rotates already rotated pieces, it rotates into invalid positions
        # FIX: limit rotationDegrees to be only legal values by aproximating into closest rotation

        rotationDegrees = (int(relational_play_parts[pairs_iterator])) + data["state"][piece_to_move_location][piece_to_move]["rotation"]
        
        
        #breakpoint() #-- DEBUG

        # CASE WHENEVER MORE THAN 1 REFERENCE PIECE IS USED, BUT ALL TOWARDS THE SAME DIRECTION
        if len(direction_and_related_piece.keys()) > 1 and is_all_same_direction:

            self.current_play["is_more_than_one_step"] = True
            piecePostMoveCoordinates = await self.find_starting_coordinate_from_parallel_directions(data["state"], first_direction, direction_and_related_piece)
            self.last_dir = first_direction
            self.last_piece = piece_to_move
            return await self.parsePlayResponse(piece_to_move,piecePostMoveCoordinates,rotationDegrees)

        # CASE WHENEVER MORE THAN 1 REFERENCE PIECE IS USED
        elif len(direction_and_related_piece.keys()) > 1:
            piecePostMoveCoordinates = await self.findCoordinatesMoreThanOneRelated(data["state"],piece_to_move, piece_to_move_location, direction_and_related_piece) 
            
            
            if(piecePostMoveCoordinates == -1):
                return {"type":"error", "message": "coordinates of direction vectors applied on related pieces will never converge"}
            
            
            self.last_dir = first_direction
            self.last_piece = piece_to_move
            return await self.parsePlayResponse(piece_to_move,piecePostMoveCoordinates,rotationDegrees)

        #CASE WHENEVER ONLY 1 REFERENCE PIECE IS USED
        else:
            self.current_play["is_more_than_one_step"] = True
            direction = self.direction_vectors[list(direction_and_related_piece.values())[0]]
            piecePostMoveCoordinates = await self.extract_floats(data["state"]["on_board"][list(direction_and_related_piece.keys())[0]]["position"]["position"])

            self.last_dir = list(direction_and_related_piece.values())[0]
            self.last_piece = piece_to_move

            return await self.parsePlayResponse(piece_to_move,piecePostMoveCoordinates,rotationDegrees) 

    async def extract_integers(self, coord_str):
        """Extracts two integer values from a string formatted as '(-129, 73)'."""
        matches = re.findall(r"[-+]?\d+", coord_str)
        return [int(matches[0]), int(matches[1])] if len(matches) == 2 else None

    async def extract_floats(self, coord_str):
        """Extracts two float values from a string formatted as '(-129.0273, 73.60434)'."""
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", coord_str)
        return [float(matches[0]), float(matches[1])] if len(matches) == 2 else None

    async def find_starting_coordinate_from_parallel_directions(self,game_state, common_direction, direction_and_related_piece):
        coordinates_x = []
        coordinates_y = []
        
        # Iterate over each piece in the dictionary
        for piece in direction_and_related_piece.keys():

            piece_coordinates = await self.extract_floats(game_state["on_board"][piece]["position"]["position"])

            coordinates_x.append(piece_coordinates[0])
            coordinates_y.append(piece_coordinates[1])
        
        # Get the highest and lowest coordinates in x and y
        highest_x = max(coordinates_x)
        highest_y = max(coordinates_y)
        lowest_x = min(coordinates_x)
        lowest_y = min(coordinates_y)
        
        # Initialize x and y coordinates
        x = 0
        y = 0
        
        # Handle common direction cases
        if common_direction == "top":
            x = sum(coordinates_x) / len(coordinates_x)
            y = highest_y
        elif common_direction == "top-right":
            x = highest_x
            y = highest_y
        elif common_direction == "right":
            x = highest_x
            y = sum(coordinates_y) / len(coordinates_y)
        elif common_direction == "bottom-right":
            x = highest_x
            y = lowest_y
        elif common_direction == "bottom":
            x = sum(coordinates_x) / len(coordinates_x)
            y = lowest_y
        elif common_direction == "bottom-left":
            x = lowest_x
            y = lowest_y
        elif common_direction == "left":
            x = lowest_x
            y = sum(coordinates_y) / len(coordinates_y)
        elif common_direction == "top-left":
            x = lowest_x
            y = highest_y
        
        return [x, y]

    async def find_intersection(self, p1, d1, p2, d2):
        # Calculate the denominator for the intersection formula
        denominator = d1[0] * d2[1] - d1[1] * d2[0]
        
        # If the denominator is too small, lines are parallel or coincident
        if abs(denominator) < 0.0001:
            return None  # Lines are parallel or coincident
        
        # Calculate the values of t and s
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / denominator
        s = ((p2[0] - p1[0]) * d1[1] - (p2[1] - p1[1]) * d1[0]) / denominator

        # If t and s are both greater than or equal to 0, the intersection is on both segments
        if t >= 0 and s >= 0:
            return [p1[0] + d1[0] * t, p1[1] + d1[1] * t]  # Calculate the intersection point
        return None
    
    async def find_common_intersection(self, points, directions):
        # Check if there are fewer than 2 points (not enough lines to find an intersection)
        if len(points) < 2:
            return None  # Not enough lines to find an intersection
        
        # Find the initial intersection between the first two points and directions
        intersection = await self.find_intersection(points[0], directions[0], points[1], directions[1])
        
        # If no intersection is found between the first two, return None
        if intersection is None:
            return None
        
        # Iterate over the remaining points and directions
        for i in range(2, len(points)):
            new_intersection = await self.find_intersection(intersection, directions[0], points[i], directions[i])
            
            # If no intersection is found with the current point, return None
            if new_intersection is None:
                return None
            
            # Update the intersection to the new intersection found
            intersection = new_intersection
        
        # Return the final intersection point
        return intersection

    async def findCoordinatesMoreThanOneRelated(self, game_state, pieceToMove, pieceToMoveLocation, direction_and_related_piece):
        
        related_pieces_coordinates = []
        directions = []
        
        # Iterate through the direction_and_related_piece dictionary
        for piece, direction in direction_and_related_piece.items():
            # Get the direction vector using the direction (assuming direction_vectors is defined elsewhere)
            directions.append(self.direction_vectors[direction])
            
            related_pieces_coordinates.append(await self.extract_floats(game_state["on_board"][piece]["position"]["position"]))
        
        # Find the common intersection of the coordinates and directions
        final_coordinate = await self.find_common_intersection(related_pieces_coordinates, directions)
        
        # If no convergence, return the current piece coordinates
        if final_coordinate is None:
            return -1
        else:
            return final_coordinate

    async def playFeedback(self, data):
        """
        Function to handle a feedback about the latest play from the game. Modify this function to implement your own agent.
        See Superclass TangramAgent or Api description for input/output formats.

        In this Agent, this function only leads to following actions if:
        - play is performed with more than one move (such as using only one piece as reference, which needs multiple small increments until not overlapping)
        - play is one move only, but result led to overlapping
        """
        
        ## If the piece was moved off_board, then simply stop the turn and let Godot fix (most likely happens when an invalid relative move occurs) 
        if(data["state"]["on_board"].get(self.last_piece) == None):
            self.current_play["is_more_than_one_step"] = False
            return await self.parseFinishResponse()


        current_positions_as_floats = await self.extract_floats(data["state"]["on_board"][self.last_piece]["position"]["position"])

        if self.current_play["is_more_than_one_step"] == True and len(data["state"]["on_board"][self.last_piece]["collisions"]) > 0:
            return await self.parsePlayResponse(
                self.last_piece,
                [
                    current_positions_as_floats[0] +  float(self.direction_vectors[self.last_dir][0] * self.distance_increment),
                    current_positions_as_floats[1] + float(self.direction_vectors[self.last_dir][1] * self.distance_increment)
                ], 
                data["state"]["on_board"][self.last_piece]["rotation"]
            )
        else:

            if self.current_play["is_more_than_one_step"] == True and len(data["state"]["on_board"][self.last_piece]["collisions"]) == 0:
                self.current_play["is_more_than_one_step"] = False
            
            return [
                await self.parseFinishResponse(), 
                {"type": "chat", "message": self.current_play["reasoning"]}
            ]
        
    async def chatRequest(self, data):
        board_img = data["board_img"]
        drawer_img = data["drawer_img"]
        
        game_state_dict = data["state"]
        objective = data["objective"]
        user_msg = data["message"]

        ai_msg = await self.send_GPT_message_query(objective, str(game_state_dict), user_msg, board_img, drawer_img)

        return {"type": "chat", "message": ai_msg}
    
    async def send_GPT_message_query(self, objective : str, game_state : str, user_msg : str, board_img, drawer_img):
        messages = self.chatLog[max(0,len(self.chatLog) - self.historyLimit):]

        messages.append({
            "role": "user",
            "content": [
                self.gameLogic,
                {"type": "text", "text": "Your objective this game is to form the shape of " + objective + "."},
                self.chatPrompt,
                {"type": "text", "text": "Current Board image:"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{board_img}" 
                }},
                {"type": "text", "text": "Current piece drawer image:\n"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{drawer_img}"
                }},
                {"type": "text", "text": "Current piece rotations:\n" + game_state + '\n'}
            ]
        })

        
        messages.append({"role": "user", "content": user_msg})

        self.chatLog.append({"role": "user", "content": user_msg})
        
        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature = self.temperature,
            max_tokens = self.max_tokens
        )

        self.chatLog.append({"role": "assistant", "content": response.choices[0].message.content})

        return response.choices[0].message.content

    async def parsePlayResponse(self, piece, position, rotation):

        self.last_piece = piece
        

        return {    
            "type": "play",
            "shape": piece,
            "position": position,
            "rotation": float(rotation),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    async def parseFinishResponse(self):
        
        ##TODO: fix placement do chatLog
        self.chatLog.append({"role": "assistant", "content": self.current_play["reasoning"]})
        
        return {
            "type": "finish",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

async def main():
    agent = CustomAgent()
    await agent.start_server()

if __name__ == "__main__":
    asyncio.run(main())
