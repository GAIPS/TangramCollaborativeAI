extends Node2D

var api_key = OS.get_environment("OPENAI_API_KEY")
var model = "gpt-4o"

#TODO: MODEL FOR PLAY EXTRACTION 

var temperature = 0.7
var max_tokens = 1024
var messages = []
var headers =  ["Content-type: application/json", "Authorization: Bearer " + api_key]
var data
var request 
func get_base_url() -> String:
	var result = JavaScriptBridge.eval("window.location.origin")
	print("Base URL is " + result )
	return result

var base_url = get_base_url()
var url = base_url + "/api/v1/task/completions"

const figures_names = ["Purple","Brown","Cream","Red","Yellow","Green","Blue"]
const possible_directions = ["right", "left", "top", "bottom", "top-right", "top-left", "bottom-right", "bottom-left"]
var objective = ""

var is_request_in_progress = false
var last_request = ""
var current_play = {"move": "", "reasoning": ""}

var messageLog = []
var historyLimit = 20

func _ready():
	request = HTTPRequest.new()
	add_child(request)
	
	request.request_completed.connect(_on_request_completed)

signal play_treated

func _on_request_completed(_result, _response_code, _headers, body):
	
	is_request_in_progress = false
	
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var message = ""
	
	var response = json.get_data()
	if response.has("error"):
		print(response["error"]["message"])

		# Reset the tracked play, if an error occurs mid play
		current_play = {"move": "", "reasoning": ""}


		message = "An error ocurred while trying to play, I'll skip this turn."
		$"../ChatBox/AI_Chat".add_message("AI Player: " + message, true, false)
		#TODO: ADD MESSAGE TO CHAT HISTORY
		
	else:
		message = response["choices"][0].message.content
		
		if last_request == "GPT Play Extensive":
			print("GPT Play Extensive sent and received sucessfully")
			print(message)
			await send_GPT_Move_Extraction_Request(message)
			await send_GPT_Reasoning_Extraction_Request(message)
			
		elif last_request == "GPT Play Move Extraction":
			print("GPT Play Move Extraction sent and received sucessfully")
			print(message)
			current_play["move"] = message

			messageLog = get_node("../ChatBox/AI_Chat").getUpdatedLog()
			messageLog.append({"role": "assistant", "content": message})
			
		elif last_request == "GPT Play Reasoning Extraction":
			print("GPT Play Reasoning Extraction sent and received sucessfully")
			print(message)
			current_play["reasoning"] = message

			messageLog = get_node("../ChatBox/AI_Chat").getUpdatedLog()
			messageLog.append({"role": "assistant", "content": message})
		
		else:
			pass #FIXME
			
		
		if current_play["move"] != "" and current_play["reasoning"] != "":

			print("\n\n\n")
			print(current_play["move"])
			print("\n\n\n")
			if current_play["move"].begins_with("Square"):
				var move_data = current_play["move"].split(" ")
				await playSquare(move_data[1], move_data[2])
			elif current_play["move"].begins_with("Rotate"):
				var move_data = current_play["move"].split(" ")
				await playRotate(move_data[1], move_data[2])
			elif current_play["move"].begins_with("Finish"):
				var move_data = current_play["move"].split(":")
				await playFinish(move_data[1])
			elif current_play["move"].begins_with("Triangle"):
				var move_data = current_play["move"].split(" ")
				await playTriangle(move_data[1], move_data[2], move_data[3])
			else:
				var play_status = await performPlaySuggestedByAI(current_play["move"])
			
				if play_status == "invalid":
					message = "Invalid Play suggested by AI"

			$"../ChatBox/AI_Chat".add_message("AI Player: Did Move: " + current_play["move"] + "\nBecause: " + current_play["reasoning"], true, true) # Change the message to be user friendly
			
			emit_signal("play_treated")
			
			# Reset the track play, after playing
			current_play = {"move": "", "reasoning": ""}
	
# Function to send the request and await its completion
func send_request(url, headers, body):
	if is_request_in_progress:
		print("Previous request is still in progress, waiting...")
		await request.request_completed  # Wait for the previous request to finish
		print("Previous request completed, sending a new one.")

	var result = await request.request(url, headers, HTTPClient.METHOD_POST, body)

	if result != OK:
		print("There was an error sending the HTTP request!")
	else:
		is_request_in_progress = true
	
	return result
		
func ai_play(game_task : String):
	
	objective = game_task
	
	var current_board64 = $"../..".get_board_screen()
	current_board64.save_png("res://Board.png")
	current_board64 = Marshalls.raw_to_base64(current_board64.save_png_to_buffer())
	 
	var current_piece_drawer64 = $"../..".get_piece_drawer_screen()
	current_piece_drawer64.save_png("res://Drawer.png")
	current_piece_drawer64 = Marshalls.raw_to_base64(current_piece_drawer64.save_png_to_buffer())
	
	var current_game_state = str($"../..".get_game_state())
	print("Game State: " + current_game_state)
	
	#UNCOMMET WHEN STOPPING DEBUGGING
	await send_GPT_Play_Request(current_board64, current_piece_drawer64, current_game_state)
	await play_treated #Wait for GPT to give a play to pass turn to player
	
	#DEBUG -- await playTriangle("Cream", "clockwise", "Red")
	#DEBUG -- await performPlaySuggestedByAI("Red, right, Cream, 0, 0, 0")
	$"../..".setPlayerTurn()

# Moves the piece to the target_position using an animation
# Always use await AI_move_piece when calling
func AI_move_piece(object_name: String, target_position: Vector2, target_rotation: float, duration: float):
	
	var obj = get_parent().get_parent().get_node(object_name) #Due to hierarchy on node tree
	
	if obj == null:
		print("Object not found: ", object_name)
		return

	var tween = get_tree().create_tween()

	tween.parallel().tween_property(obj, "position", target_position, duration)
	tween.parallel().tween_property(obj, "rotation", target_rotation, duration)
	
	#print(str(target_position[0]) + "," + str(target_position[1]) + " " + str(target_rotation))
	
	tween.play()
	await tween.finished
	tween = get_child(get_child_count() - 1)
	if tween is Tween:
		tween.queue_free()

func send_GPT_Play_Request(board_image_64, piece_drawer_image_64 ,game_state_str):
	var messages = []

	messageLog = get_node("../ChatBox/AI_Chat").getUpdatedLog()
	messages = messageLog.slice(messageLog.size() - historyLimit, messageLog.size()).duplicate(true)

	messages.append({
		"role": "system",
		"content": [
			gameLogic,
			{"type": "text", "text":"You are an AI-Player helping the Human Player arrange Tangram Pieces in a board in order to create " + objective + ". 
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
		list all moves that should be done in order to create " + objective + ", providing explanations for each one."
		}]
	})

	#messages.append({"role": "system", "content": "Chat history, smallest index entries are the oldest:" + game_interaction_history_str + chat_history_str})
	
	messages.append({
		"role": "user",
		"content": [
			{"type": "text", "text": "The image of the current board is: "},
			{"type": "image_url", "image_url": {
				"url": "data:image/png;base64," + board_image_64
			}},
			{"type": "text", "text": "The image of the current piece drawer is: "},
			{"type": "image_url", "image_url": {
				"url": "data:image/png;base64," + piece_drawer_image_64
			}},
			{"type": "text", "text": "The current rotation values of the pieces are: " + game_state_str},
			{"type": "text", "text": "Give me a list of the moves to play in order to create " + objective}
		]
	})
	
	var body = JSON.stringify({
			"messages": messages,
			"temperature": temperature,
			"max_tokens": max_tokens,
			"model": model
	})
	
	var send_request = await send_request(url,headers,body)
	if send_request != OK:
		print("There was an error sending the HTTP request!")
	else:
		last_request = "GPT Play Extensive"

func send_GPT_Move_Extraction_Request(play):
	var messages = []
	
	messages.append({
		"role": "system",
		"content": "
		You are currently extracting the first move from a detailed play suggestion by the AI. 
		You must convert that move into one of the following grammars formats: 
			- [PieceToMove], [Direction], [PieceOnBoard], (Optional: [Direction], [PieceOnBoard], ...), [DegreesOfRotation], [FlipXAxis], [FlipYAxis]. 
			Where any piece name is a valid name piece between the names " + str(figures_names) + ", any direction is one of the following " 
			+ str(possible_directions) + ", any rotation degrees value must be 0,45,90,135,180,225,270,315 and any flip value is 0 or 1 (if not mentioned 0).
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
		"
	})
	
	messages.append({
		"role": "user",
		"content": [
			{ "type": "text", "text" : "Extract the first move from this list of suggested moves: " + play}
		]
	})
	
	var body = JSON.stringify({
		"messages": messages,
		"temperature": temperature,
		"max_tokens": max_tokens,
		"model": model
	})

	var send_request = await send_request(url,headers,body)
	if send_request != OK:
		print("There was an error sending the HTTP request!")
	else:
		last_request = "GPT Play Move Extraction"
		
func send_GPT_Reasoning_Extraction_Request(play):
	var messages = []
	
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
	
	var body = JSON.stringify({
		"messages": messages,
		"temperature": temperature,
		"max_tokens": max_tokens,
		"model": model
	})

	var send_request = await send_request(url,headers,body)
	if send_request != OK:
		print("There was an error sending the HTTP request!")
	else:
		last_request = "GPT Play Reasoning Extraction"
	
##################################################
####### AI PLAY INTERPRETATION FUNCTIONS ########
##################################################
		
var direction_vectors = {
	"right": Vector2(1, 0),
	"left": Vector2(-1, 0),
	"top": Vector2(0, -1),
	"bottom": Vector2(0, 1),
	"top-right": Vector2(1, -1),
	"top-left": Vector2(-1, -1),
	"bottom-right": Vector2(1, 1),
	"bottom-left": Vector2(-1, 1)
}

func performPlaySuggestedByAI(_GPTPlay : String):
	var GPTPlay_parts = _GPTPlay.rsplit(", ")
	var num_directionPiece_pairs = ((GPTPlay_parts.size() - 6) / 2) + 1 # 6 fields are mandatory to be filled. 1 pair always exists for the mandatory direction-piece pair
	var pieceToMove = GPTPlay_parts[0]
	
	if pieceToMove not in figures_names:
		print("Invalid Suggested Move: pieceToMove Name invalid " + pieceToMove)
		return "invalid"
	
	# There is an edge case where multiple pieces have the same vector direction, we must find a common starting coordinate and apply the vector
	var is_all_same_direction = true
	var first_direction = GPTPlay_parts[1]
	
	var play_iterator = 1
	var direction_and_related_piece = {}
	while num_directionPiece_pairs != 0:
		var direction = GPTPlay_parts[play_iterator]
		if direction not in possible_directions:
			print("Invalid Suggested Move: invalid direction " + direction)
			return "invalid"
			
		var relatedPiece = GPTPlay_parts[play_iterator+1]
		if relatedPiece not in figures_names:
			print("Invalid Suggested Move: relatedPiece Name invalid " + relatedPiece)
			return "invalid"
			
		direction_and_related_piece[relatedPiece] = direction
		if direction != first_direction:
			is_all_same_direction = false
		
		play_iterator += 2
		num_directionPiece_pairs -= 1
	
	
	# TODO: for some reason whe it rotates already rotated pieces, it rotates into invalid positions
	# FIX: limit rotationDegrees to be only legal values by aproximating into closest rotation
	var rotationDegrees = deg_to_rad(float(GPTPlay_parts[play_iterator])) + get_parent().get_parent().get_node(pieceToMove).rotation
	var isFlippedOnX = 	int(GPTPlay_parts[play_iterator+1])
	var isFlippedOnY = 	int(GPTPlay_parts[play_iterator+2])
	
	var piecePreMoveCoordinates = get_parent().get_parent().get_node(pieceToMove).get_node("VCenter").global_position
	var piecePreMoveRotation = 	get_parent().get_parent().get_node(pieceToMove).rotation
	var piecePostMoveCoordinates = piecePreMoveCoordinates
	
	# CASE WHENEVER MORE THAN 1 REFERENCE PIECE IS USED, BUT ALL TOWARDS THE SAME DIRECTION
	if direction_and_related_piece.keys().size() > 1 and is_all_same_direction:
		
		var common_direction = first_direction
		piecePostMoveCoordinates = get_parent().get_parent().get_node(direction_and_related_piece.keys()[0]).global_position
		await AI_move_piece(pieceToMove,piecePostMoveCoordinates,rotationDegrees,0.5)
		
		if isFlippedOnX:
			get_parent().get_parent().get_node(pieceToMove).scale.x *= -1
		if isFlippedOnY:
			get_parent().get_parent().get_node(pieceToMove).scale.y *= -1
			
		piecePostMoveCoordinates = find_starting_coordinate_from_parallel_directions(common_direction, direction_and_related_piece)
		await AI_move_piece(pieceToMove,piecePostMoveCoordinates,rotationDegrees,0.5)
		
		
		var max_iter = 30
		var iter = 0
		var distance_increment = 5
		while get_parent().get_parent().get_node(pieceToMove).overlapping and iter < max_iter:
			piecePostMoveCoordinates = piecePostMoveCoordinates + direction_vectors[common_direction]*distance_increment
			await AI_move_piece(pieceToMove,piecePostMoveCoordinates,rotationDegrees,0.1)
			iter += 1
	
	# CASE WHENEVER MORE THAN 1 REFERENCE PIECE IS USED
	elif direction_and_related_piece.keys().size() > 1:
		piecePostMoveCoordinates = findCoordinatesMoreThanOneRelated(pieceToMove, direction_and_related_piece) 
			
		if(piecePreMoveCoordinates == piecePostMoveCoordinates):
			print("Invalid Suggested Move: coordinates of direction vectors applied on related pieces will never converge")
			return "invalid"
		
		await AI_move_piece(pieceToMove,piecePostMoveCoordinates,rotationDegrees,0.5)
		
		if isFlippedOnX:
			get_parent().get_parent().get_node(pieceToMove).scale.x *= -1
		if isFlippedOnY:
			get_parent().get_parent().get_node(pieceToMove).scale.y *= -1
			
	#CASE WHENEVER ONLY 1 REFERENCE PIECE IS USED
	else:
		var direction = direction_vectors[direction_and_related_piece[direction_and_related_piece.keys()[0]]]
		piecePostMoveCoordinates = get_parent().get_parent().get_node(direction_and_related_piece.keys()[0]).global_position
		await AI_move_piece(pieceToMove,piecePostMoveCoordinates,rotationDegrees,0.5)
		
		if isFlippedOnX:
			get_parent().get_parent().get_node(pieceToMove).scale.x *= -1
		if isFlippedOnY:
			get_parent().get_parent().get_node(pieceToMove).scale.y *= -1
		
		var max_iter = 30
		var iter = 0
		var distance_increment = 5
		while get_parent().get_parent().get_node(pieceToMove).overlapping and iter < max_iter:
			piecePostMoveCoordinates = piecePostMoveCoordinates + direction*distance_increment
			await AI_move_piece(pieceToMove,piecePostMoveCoordinates,rotationDegrees,0.1)
			iter += 1
	
	# if after suggested move, piece is overlapping, try to fix it.
	if get_parent().get_parent().get_node(pieceToMove).overlapping:
		var is_overlap_resolved = await resolve_overlap(get_parent().get_parent().get_node(pieceToMove), rotationDegrees)
		if is_overlap_resolved == false:
			get_parent().get_parent().get_node(pieceToMove).global_position = piecePreMoveCoordinates
			get_parent().get_parent().get_node(pieceToMove).rotation = piecePreMoveRotation
			print("Invalid Suggested Move: couldn't make play without overlapping with anything")
			return "invalid"
	
	return "Performed relative move: " + _GPTPlay

# When all directions are equal, it retuns the adequate starting position
func find_starting_coordinate_from_parallel_directions(common_direction, direction_and_related_piece):
	
	var coordinates_x = []
	var coordinates_y = []
	for piece in direction_and_related_piece.keys():
		var coordinates = get_parent().get_parent().get_node(piece).get_node("VCenter").global_position	
		coordinates_x.append(coordinates[0])
		coordinates_y.append(coordinates[1])
	
	var highest_x = coordinates_x.max()
	var highest_y = coordinates_y.max()
	
	var lowest_x = coordinates_x.min()
	var lowest_y = coordinates_y.min()
	
	var x
	var y
	
	if common_direction == "top":
		x = (coordinates_x.reduce(func(accum,number): return accum+number,0)) / coordinates_x.size()
		y = highest_y
	if common_direction == "top-right":
		x = highest_x
		y = highest_y
	if common_direction == "right":
		x = highest_x
		y = (coordinates_y.reduce(func(accum,number): return accum+number,0)) / coordinates_y.size()
	if common_direction == "bottom-right":
		x = highest_x
		y = lowest_y
	if common_direction == "bottom":
		x = (coordinates_x.reduce(func(accum,number): return accum+number,0)) / coordinates_x.size()
		y = lowest_y
	if common_direction == "bottom-left":
		x = lowest_x
		y = lowest_y
	if common_direction == "left":
		x = lowest_x
		y = (coordinates_y.reduce(func(accum,number): return accum+number,0)) / coordinates_y.size()
	if common_direction == "top-left":
		x = lowest_x
		y = highest_y	
	
	return Vector2(x,y)

func findCoordinatesMoreThanOneRelated(piece_to_move : String, direction_and_related_piece: Dictionary):
	var current_piece_coordinates = get_parent().get_parent().get_node(piece_to_move).get_node("VCenter").global_position	
	
	var related_pieces_coordinates = []
	var directions = []

	for piece in direction_and_related_piece.keys():
		var direction = direction_and_related_piece[piece]
		directions.append(direction_vectors[direction])
		
		var coordinates = get_parent().get_parent().get_node(piece).get_node("VCenter").global_position	
		related_pieces_coordinates.append(coordinates)
	
	var final_coordinate = find_common_intersection(related_pieces_coordinates,directions)
	if final_coordinate == null:
		print("Convergence will not happen")
		return current_piece_coordinates
	else:
		return final_coordinate			

func find_common_intersection(points, directions):
	if points.size() < 2:
		return null  # Not enough lines to find an intersection
	
	var intersection = find_intersection(points[0], directions[0], points[1], directions[1])
	if not intersection:
		return null
	
	for i in range(2, points.size()):
		var new_intersection = find_intersection(intersection, directions[0], points[i], directions[i])
		if not new_intersection:
			return null
		intersection = new_intersection
	
	return intersection

func find_intersection(p1, d1, p2, d2):
	var denominator = d1.x * d2.y - d1.y * d2.x
	if abs(denominator) < 0.0001:
		return null  # Lines are parallel or coincident
	
	var t = ((p2.x - p1.x) * d2.y - (p2.y - p1.y) * d2.x) / denominator
	var s = ((p2.x - p1.x) * d1.y - (p2.y - p1.y) * d1.x) / denominator
	
	if t >= 0 and s >= 0:
		return p1 + d1 * t
	return null
	
# Since a godot frames take about 0.16 seconds, 
func resolve_overlap(node : Node, rotationDegrees):
	var distance = 8
	var distance_increment = 5
	var iter = 0
	var max_iter_count = 12
	var moved = false
	var directions = [[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1],[0,-1],[1,-1]]
	var startPos = node.position
	
	while node.overlapping and iter <= max_iter_count:
		for direction in directions:
			if not moved:
				moved = await testDirection(node, direction, distance, rotationDegrees, startPos)
			else:
				break

		# Increase distance for the next iteration if no move was successful
		if not moved:
			distance += distance_increment
			iter += 1
		else:
			break

	return moved

func moveDirection(node : Node, direction, distance : int, rotationDegrees, pos : Vector2):
	var target_position = Vector2(pos.x + direction[0] * distance, pos.y + direction[1] * distance)
	await AI_move_piece(node.name, target_position, rotationDegrees, 0.1)

func testDirection(node: Node, direction: Array, distance: int, rotationDegrees, pos):
	await moveDirection(node, direction, distance, rotationDegrees, pos)

	if not node.overlapping:
		return true
	else:
		await moveDirection(node, direction, distance, rotationDegrees, pos)
		return false

func getUpdatedLog():
	return messageLog

func playSquare(refPiece: String, movePiece: String):
	var valid_pairs = [["Red", "Cream"], ["Yellow", "Green"]]
	
	for pair in valid_pairs:
		if refPiece in pair and movePiece in pair and refPiece != movePiece:
			var ref_node  = get_parent().get_parent().get_node(refPiece)
			var move_node = get_parent().get_parent().get_node(movePiece)
			
			if ref_node and move_node:
				# Get the SquareSnap position from the reference node
				var snap_position = ref_node.get_node("SquareSnap").global_position
				var ref_rotation
				
				if ref_node.rotation_degrees+180 >= 360:
					ref_rotation = ref_node.rotation_degrees+180 - 360
				else:
					ref_rotation= ref_node.rotation_degrees + 180 
				
				#TODO: CORRECTLY ANIMATE
				
				move_node.position = snap_position
				move_node.rotation = deg_to_rad(ref_rotation)
		return

func playTriangle(refPiece: String, refCathethusDirectionFromSquareAngle: String, movePiece: String):
	var valid_pairs = [["Red", "Cream"], ["Yellow", "Green"]]
	
	for pair in valid_pairs:
		if refPiece in pair and movePiece in pair and refPiece != movePiece:
			var ref_node  = get_parent().get_parent().get_node(refPiece)
			var move_node = get_parent().get_parent().get_node(movePiece)
			
			var snap_position
			var ref_rotation
			
			#Based on the different rotation values the reference triangle could have, 
			#pick the correct placement for the triangle
			
			if refCathethusDirectionFromSquareAngle == "clockwise":
				snap_position = ref_node.get_node("TriangleSnap1").global_position
				ref_rotation = ref_node.rotation_degrees + 90
			elif refCathethusDirectionFromSquareAngle == "anticlockwise":
				snap_position = ref_node.get_node("TriangleSnap2").global_position
				ref_rotation = ref_node.rotation_degrees + 270
			
			if ref_rotation >= 360:
				ref_rotation = ref_rotation - 360
			
			# Call AI_move_piece with the necessary parameters
			move_node.position = snap_position
			move_node.rotation = deg_to_rad(ref_rotation)
	return

func playRotate(piece: String, rot: String):
	var pieceNode  = get_parent().get_parent().get_node(piece)
	pieceNode.rotation = deg_to_rad(float(rot))
	return

func playFinish(msg : String):
	$"../ChatBox/AI_Chat".add_message("AI Player: " + msg, true, false)
	return

var gameLogic = {
"type": "text", "text":"""Reference Information about the game: 
You and the human user are playing a tangram game, arranging the pieces to form an objective shape. 
The pieces are named by their colors: Red, Purple, Yellow, Green, Blue, Cream, and Brown.
Red and Cream are two large triangles, Yellow and green are two small triangles, Blue is a medium triangle, Purple is a small square, Brown is a tilted parallelogram.
We consider 0 degrees of rotation the triangles with their hypotenuse facing down, and the square in the square position (so the diamond shape corresponds to 45 degrees of rotation)
Example logical plays: Matching shapes can allow new larger shapes to appear, uniting two triangles of the same size by their Hypotenuse creates a square of that size in the location or a diamond (can be used as a circle) shape if the triangles are angled by 45 degrees. The Purple Square or a square created of 2 triangles can serve to form many things like heads, bodies, bases of structures. two triangles can also form a larger triangle when combined by their cathetus green and yellow can usually be used together or to fill similar objectives this could be used to make a another medium sized triangle like blue if used with yellow and green.
It often makes sense to use pieces of the same shape to furfil similar objectives, for example if theres 2 arms, it makes sense to use similar pieces for each.
"""
}
