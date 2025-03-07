extends Node2D

const AI_PROFILE 	 	= "Arena/AITurn"
const HUMAN_PROFILE 	= "Arena/HumanTurn"
const END_TURN_BUTTON 	= "Arena/End Turn Button"
const UNDO_BUTTON    	= "Arena/Undo Button"
const FINISH_BUTTON 	= "Arena/Finish Button"
const CONTROLS_BUTTON  = "Arena/Controls Button"

var current_turn = ""
var game_task

var obj_selected = "" 
var dragging = false
var overlapping = false
var last_move = ""

var shapes = {
	"Red": 		{"onBoard": false},
	"Yellow": 	{"onBoard": false},
	"Green": 	{"onBoard": false},
	"Blue": 	{"onBoard": false},
	"Purple": 	{"onBoard": false},
	"Brown": 	{"onBoard": false},
	"Cream": 	{"onBoard": false}
}

var movedPiece = ""
var originalPos
var originalRot
var preMovePos
var preMoveRot
var hasRequest = false
var isInTutorial = false

var debugMode = false
var warnCon = true

#Stats
var startTime
var chatSent = 0
var chatReceived = 0
var turns = 0

#Thinking annimation
var time_elapsed = 0
var thinking_asc
var curr_think_state
const ANIM_THINK_TIME = 1

var pendingFeedback = false

#Websocket
var request
@export var websocket_url = "ws://localhost:5000"
var ws = WebSocketPeer.new()

#Tasks
var possible_tasks = ["A house", "A fish", "A human", "A rocket", "A cat", "A robot"]

func _ready():
	game_task = possible_tasks[randi_range(0,possible_tasks.size()-1)]
	$"Arena/TargetDisplayText/Objective".text = game_task
	current_turn = "Player"
	startTime = Time.get_datetime_dict_from_system()
	ws.connect_to_url(websocket_url)
	
	const outbound_buffer = 4194240 # Good size for two PNGS + text
	const incoming_buffer = 65535 # Default godot value, change if needed  
	ws.set_outbound_buffer_size(outbound_buffer) 

#### GameLogic ####
####################
func _process(_delta):
	time_elapsed += _delta
	
	ws.poll()
	var state = ws.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		if not warnCon:
			$"Arena/ChatBox/AI_Chat".add_message("Connection to AI Agent established.", true)
			warnCon = true

		while ws.get_available_packet_count():
			var packet = ws.get_packet()
			var json_string = packet.get_string_from_utf8()
			var json = JSON.new()
			var error = json.parse(json_string)

			if error == OK:
				var data = json.get_data()
				if typeof(data) == TYPE_DICTIONARY:

					if data.has("type"):
						var message_type = data["type"]

						if message_type == "play":
							aiPlayRequest(data)

						elif message_type == "finish":
							finishPlayRequest()

						elif message_type == "chat":
							if not data.has("message"):
								sendError("Error: Missing message field in received JSON")
							$"Arena/ChatBox/AI_Chat".add_message(data["message"], true)
							registerAIChat()
					else:
						sendError("Error: No message type in received JSON")
	elif state == WebSocketPeer.STATE_CONNECTING and warnCon and time_elapsed > 1:
		$"Arena/ChatBox/AI_Chat".add_message("Failed to find an AI Agent to connect to.", true)
		warnCon = false
	elif  state == WebSocketPeer.STATE_CLOSED:
		ws.connect_to_url(websocket_url)

	if current_turn == "Player":
		get_node(AI_PROFILE).hide()
		get_node(HUMAN_PROFILE).show()
		color(END_TURN_BUTTON, true)
		color(CONTROLS_BUTTON, true)
		color(FINISH_BUTTON, true)

		if movedPiece and not debugMode:
			color(UNDO_BUTTON, true)
			for piece in shapes:
				if piece != movedPiece:
					get_node(piece).get_child(0).modulate = Color8(145, 145, 145, 255)	
				else:
					get_node(piece).get_child(0).modulate = Color8(255, 255, 255, 255)
		else:
			color(UNDO_BUTTON, false)	
			for piece in shapes:
				get_node(piece).get_child(0).modulate = Color8(255, 255, 255, 255)

		if dragging:
			color(END_TURN_BUTTON, false)
			color(CONTROLS_BUTTON, false)
			color(FINISH_BUTTON, false)
			color(UNDO_BUTTON, false)

		if hasRequest:
			get_node(END_TURN_BUTTON).modulate = Color8(145, 145, 145, 255)

		if turns < 3:
			color(FINISH_BUTTON, false)
	else:
		get_node(AI_PROFILE).show()
		get_node(HUMAN_PROFILE).hide()
		color(END_TURN_BUTTON, false)
		color(UNDO_BUTTON, false)
		color(CONTROLS_BUTTON, true)
		color(FINISH_BUTTON, false)
		for piece in shapes:
			get_node(piece).get_child(0).modulate = Color8(255, 255, 255, 255)
		
	 # Probably can be called less often
	if pendingFeedback:
		ws.send_text(makeJson("playFeedback"))
		pendingFeedback = false

	if isInTutorial:
		color(END_TURN_BUTTON, true)
		color(CONTROLS_BUTTON, true)
		color(FINISH_BUTTON, true)
		color(UNDO_BUTTON, true)
		return

func color(nodeName, b: bool):
	if b:
		get_node(nodeName).modulate = Color8(255, 255, 255, 255)
	else:
		get_node(nodeName).modulate = Color8(145, 145, 145, 255)

func _on_DraggableObject_input_event(_viewport, event, _shape_idx, _node_name):
	if not isInTutorial and event is InputEventMouseButton and current_turn == "Player" and obj_selected != "" and (not movedPiece or obj_selected == movedPiece or debugMode):
		if not movedPiece or debugMode:
			movedPiece = obj_selected
			originalPos = get_node(obj_selected).position
			originalRot = get_node(obj_selected).rotation
			print("moving " + obj_selected + " this turn")
		if event.is_action("Click"):
			if event.is_pressed():
				dragging = true
				get_node(obj_selected).start_drag()
				preMovePos = get_node(obj_selected).position
				preMoveRot = get_node(obj_selected).rotation
			else:
				get_node(movedPiece).updateOverlaps()
				if len(get_node(obj_selected).overlaps) == 0:
					dragging = false
					last_move = "drop"
					get_node(obj_selected).end_drag()
				else:
					dragging = false
					last_move = ""
					get_node(obj_selected).end_drag()
					get_node(movedPiece).position = preMovePos
					get_node(movedPiece).rotation = preMoveRot
					movedPiece = ""
			
		elif Input.is_action_just_pressed("Right_click"):
			last_move = "rotated"
			if snappedf(get_node(obj_selected).rotation + PI/4, 0.0001) == snappedf(2*PI, 0.0001):
				get_node(obj_selected).rotation = 0
			else:
				get_node(obj_selected).rotation += PI/4

#### Communication ####
########################
func makeJson(type="playRequest", message=""):
	var board_buffer = get_board_screen().save_png_to_buffer()
	var drawer_buffer = get_piece_drawer_screen().save_png_to_buffer()

	#drawer_buffer.resize(500)
	
	var board64 = Marshalls.raw_to_base64(board_buffer)
	var drawer64 = Marshalls.raw_to_base64(drawer_buffer)

	var body = {
		"objective": game_task, 
		"state": get_game_state(), 
		"board_img": board64,
		"drawer_img": drawer64,
		"timestamp": getElapsedTime()
	}
	if type == "chatRequest":
		body["message"] = message
	body["type"] = type

	return JSON.stringify(body)

func sendError(error):
	ws.send_text(JSON.stringify({"type": "error", "message": error}))

func ai_play():
	if isInTutorial:
		return
	obj_selected = ""
	movedPiece = ""
	ws.send_text(makeJson("playRequest"))

func sendChatMsg(message):
	registerPlayerChat()
	ws.send_text(makeJson("chatRequest", message))

func aiPlayRequest(data):
	if not data.has("shape"):
		sendError("Error: No shape field in received JSON")
		setPlayerTurn()
	if not data.has("position"):
		sendError("Error: No shape field in received JSON")
		setPlayerTurn()
	if not data.has("rotation"):
		sendError("Error: No shape field in received JSON")
		setPlayerTurn()
	if len(data["position"]) != 2 or typeof(data["position"][0]) != TYPE_FLOAT or typeof(data["position"][1]) != TYPE_FLOAT:
		sendError("Error: Invalid position field in received JSON")
		setPlayerTurn()
	if typeof(data["rotation"]) != TYPE_FLOAT:
		sendError("Error: Invalid rotation field in received JSON")
		setPlayerTurn()

	print(data)
	if movedPiece == "":
		movedPiece = data["shape"]
		preMovePos = get_node(data["shape"]).position
		preMoveRot = get_node(data["shape"]).rotation

	elif movedPiece != data["shape"]:
		get_node(movedPiece).position = preMovePos
		get_node(movedPiece).rotation = preMoveRot
		movedPiece = data["shape"]
		preMovePos = get_node(data["shape"]).position
		preMoveRot = get_node(data["shape"]).rotation

	var pos = Vector2(data["position"][0], data["position"][1]) # Should force 0 - 100
	var rot = data["rotation"]
	await movePiece(data["shape"], simpleToReal(pos), deg_to_rad(rot), 0.5)
	await updateFigureLocation()
	await get_tree().process_frame 
	ws.send_text(makeJson("playFeedback"))

func wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout

func finishPlayRequest():
	turns += 1
	if movedPiece in shapes:
		if shapes[movedPiece]["onBoard"]:
			get_node(movedPiece).updateOverlaps()
			if len(get_node(movedPiece).overlaps) > 0:
				$"Arena/ChatBox/AI_Chat".add_message("Sorry I had some trouble playing, I'll retry next round", true)
				get_node(movedPiece).position = preMovePos
				get_node(movedPiece).rotation = preMoveRot
				setPlayerTurn()
				return
	setPlayerTurn()

#####  Game State #####
#######################
func updateFigureLocation():
	var updated = false
	for shape in shapes:
		shapes[shape]["onBoard"] = false
		for figure in $Arena/ArenaBoard.get_overlapping_areas():
			if figure.name == shape:
				shapes[shape]["onBoard"] = true
				break
	
func getVerticePosition(node_path : String) -> Vector2:
	return realToSimple(get_node(node_path).global_position)

func getShapePosition(figure_name: String) -> Dictionary:
	var figure_state = {
		"position": null,
		"vertices": []
	}

	figure_state["position"] = getVerticePosition(figure_name + "/VCenter")

	for i in range(1, 5):
		if has_node(figure_name + "/V" + str(i)):
			figure_state["vertices"].append(getVerticePosition(figure_name + "/V" + str(i)))

	return figure_state

func get_game_state() -> Dictionary:	
	print("Getting game state")
	var state = {"on_board" : {},"off_board" : {}}
	updateFigureLocation()

	for shape in shapes:
		if shapes[shape]["onBoard"]:
			var rot = snapped(get_node(shape).get_rotation_degrees(), 0.01)
			var pos = getShapePosition(shape)
			get_node(shape).updateOverlaps()
			var collisions = get_node(shape).overlaps
			var entry = {"position": pos, "rotation": rot, "collisions": collisions}
			state["on_board"][shape] = entry
			
		else:
			var rot = snapped(get_node(shape).get_rotation_degrees(), 0.01)
			var entry = {"rotation": rot}
			state["off_board"][shape] = entry
	return state

#####  Calculations #####
#########################
func getElapsedTime():
	var currentTime = Time.get_datetime_dict_from_system()
	var elapsed_seconds = (Time.get_unix_time_from_datetime_dict(currentTime) - Time.get_unix_time_from_datetime_dict(startTime))
	return elapsed_seconds

func realToSimple(coords: Vector2) -> Vector2:
	var bottom_left_corner = $Arena/ArenaBoard/VBottomLeftCorner.global_position
	var upper_right_corner = $Arena/ArenaBoard/VUpperRightCorner.global_position

	var scale_x = 100.0 / (upper_right_corner.x - bottom_left_corner.x)
	var scale_y = 100.0 / (upper_right_corner.y - bottom_left_corner.y)
	
	
	var simple_x = (coords.x - bottom_left_corner.x) * scale_x
	var simple_y = (coords.y - bottom_left_corner.y) * scale_y
	
	return Vector2(simple_x, simple_y)

func simpleToReal(coords: Vector2) -> Vector2:
	var bottom_left_corner = $Arena/ArenaBoard/VBottomLeftCorner.global_position
	var upper_right_corner = $Arena/ArenaBoard/VUpperRightCorner.global_position

	var scale_x = (upper_right_corner.x - bottom_left_corner.x) / 100.0
	var scale_y = (upper_right_corner.y - bottom_left_corner.y) / 100.0
	
	var real_x = bottom_left_corner.x + (coords.x * scale_x)
	var real_y = bottom_left_corner.y + (coords.y * scale_y)
	
	return Vector2(real_x, real_y)

#####  Stats #####
##################
func registerPlayerChat():
	chatSent += 1

func registerAIChat():
	chatReceived += 1

func saveStatistics(formData):

	var file = FileAccess.open("Stats.txt", FileAccess.WRITE_READ) #WRITE_READ creates the file when it doesn't exist (which READ_WRITE does not do)

	file.seek_end()
	file.store_line("")
	
	# Store the variables in the file
	file.store_line(str(getElapsedTime()))
	file.store_line(str(chatSent))
	file.store_line(str(chatReceived))
	file.store_line(str(formData))

	var logs = $Arena/AI_Player.getUpdatedLog()
	var chatLogs = $Arena/ChatBox/AI_Chat.getUpdatedLog()

	if len(chatLogs) > len(logs):
		logs = chatLogs

	file.store_line(str(logs))

	# Close the file
	file.close()

	print("Data saved!")

#####  Actions  #####
#####################
func SetHasRequest(value):
	hasRequest = value
	
func setPlayerTurn():
	current_turn = "Player"
	movedPiece = ""
	SetHasRequest(false)

func finishPlayerTurn():
	if not isInTutorial and movedPiece and not dragging and current_turn == "Player" and not hasRequest:
		turns += 1

		if not warnCon:
			setPlayerTurn()
			return

		current_turn = "AI"
		thinking_asc = true
		time_elapsed = 0.0
		curr_think_state = 1
		SetHasRequest(true)
		ai_play()

func _undo_play():
	if not isInTutorial and movedPiece and not dragging and current_turn == "Player":
		get_node(movedPiece).position = originalPos
		get_node(movedPiece).rotation = originalRot
		movedPiece = ""

func movePiece(object_name: String, target_position: Vector2, target_rotation: float, duration: float):
	var obj = get_node(object_name) #Due to hierarchy on node tree
	
	if obj == null:
		print("Object not found: ", object_name)
		return

	var tween = get_tree().create_tween()

	tween.parallel().tween_property(obj, "position", target_position, duration)
	tween.parallel().tween_property(obj, "rotation", target_rotation, duration)
		
	tween.play()
	await tween.finished
	tween = get_child(get_child_count() - 1)
	if tween is Tween:
		tween.queue_free()

#####  Picture extraction #####
###############################
func extract_region_from_viewport(pos_x: int, pos_y: int, width: int, height: int) -> Image:
	var image = get_viewport().get_texture().get_image()
	
	var _width = image.get_width()
	var _height = image.get_height()
	var multH = (_height / 1080.0)
	var multW = (_width / 1920.0)

	# Adjust the image region based on the scaling factors
	if multH > multW:
		var region = Rect2(0, _height * (abs(multH - multW) / 2), _width, _height - _height * (abs(multH - multW)))
		image = image.get_region(region)
	elif multW > multH:
		var region = Rect2(_width * (abs(multH - multW) / 2), 0, _width - _width * (abs(multH - multW)), _height)
		image = image.get_region(region)

	# Recalculate dimensions and scaling factors after cropping
	_width = image.get_width()
	_height = image.get_height()
	multH = (_height / 1080.0)
	multW = (_width / 1920.0)

	# Extract the final region of interest
	var final_region = Rect2(pos_x * multW, pos_y * multH, width * multW, height * multH)
	return image.get_region(final_region)

func get_board_screen() -> Image:
	var image = extract_region_from_viewport(880, 115, 562, 540)
	#image.save_png("res://board.png")
	return image

func get_piece_drawer_screen() -> Image:
	var image = extract_region_from_viewport(1600, 425, 210, 210)
	#image.save_png("res://drawer.png")
	return image

#####  Input Handling  #####
############################
func _on_Debug_button_pressed():
	debugMode = !debugMode

func _on_finish_button_pressed():
	if current_turn != "Player" or isInTutorial or turns < 3:
		return
		
	for node in get_children():
		node.hide()
	get_node("Forms").show()

func _on_tutorial_button_pressed():
	if not isInTutorial:
		get_node("Tutorial").startTutorial()
	print("called2")

func _on_mouse_entered(node_name):
	if not dragging and current_turn == "Player":
		obj_selected = node_name
