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

var debugMode = false

#Stats
var startTime
var chatSent = 0
var chatReceived = 0

#Thinking annimation
var time_elapsed = 0
var thinking_asc
var curr_think_state
const ANIM_THINK_TIME = 1

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

#### GameLogic ####
####################
func _process(_delta):
	time_elapsed += _delta
	ws.poll()
	var state = ws.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
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
							$"Arena/ChatBox/AI_Chat".add_message(data["message"], true)
							registerAIChat()

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
	else:
		get_node(AI_PROFILE).show()
		get_node(HUMAN_PROFILE).hide()
		color(END_TURN_BUTTON, false)
		color(UNDO_BUTTON, false)
		color(CONTROLS_BUTTON, true)
		color(FINISH_BUTTON, false)
		for piece in shapes:
			get_node(piece).get_child(0).modulate = Color8(255, 255, 255, 255)
		thinkingAnimation()	
		
	updateFigureLocation() # Probably can be called less often

func color(nodeName, b: bool):
	if b:
		get_node(nodeName).modulate = Color8(255, 255, 255, 255)
	else:
		get_node(nodeName).modulate = Color8(145, 145, 145, 255)

func thinkingAnimation():
	if time_elapsed > ANIM_THINK_TIME:
		if thinking_asc:
			if curr_think_state == 4:
				curr_think_state -= 1
				get_node("Arena/AITurn/Thinking"+str(curr_think_state)).hide()
				thinking_asc = false
				curr_think_state -= 1
			else:
				get_node("Arena/AITurn/Thinking"+str(curr_think_state)).show()
				curr_think_state += 1
		else:
			if curr_think_state == 1:
				curr_think_state += 1
				get_node("Arena/AITurn/Thinking"+str(curr_think_state)).show()
				thinking_asc = true
				curr_think_state += 1
			else:
				get_node("Arena/AITurn/Thinking"+str(curr_think_state)).hide()
				curr_think_state -= 1
		time_elapsed = 0

func _on_DraggableObject_input_event(_viewport, event, _shape_idx, _node_name):
	if event is InputEventMouseButton and current_turn == "Player" and obj_selected != "" and (not movedPiece or obj_selected == movedPiece or debugMode):
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
				if not get_node(obj_selected).overlapping:
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
	var board64 = Marshalls.raw_to_base64(board_buffer)
	var drawer_buffer = get_piece_drawer_screen().save_png_to_buffer()
	var drawer64 = Marshalls.raw_to_base64(drawer_buffer)

	var body = {
		"type": "playRequest", 
		"objective": game_task, 
		"state": get_game_state(), 
		"board_img": board64,
		"drawer_img": drawer64,
		"timestamp": getElapsedTime()
	}
	if type == "chat":
		body["message"] = message

	return JSON.stringify(body)

func ai_play():
	obj_selected = ""
	ws.send_text(makeJson("playRequest"))

func sendChatMsg(message):
	registerPlayerChat()
	ws.send_text(makeJson("chat", message))

func aiPlayRequest(data):
	var pos = Vector2(data["position"][0], data["position"][1]) # Should force 0 - 100
	var rot = data["rotation"]
	movePiece(data["shape"], simpleToReal(pos), rot, 0.5)
	wait(0.5)
	ws.send_text(makeJson("playFeedback"))

func wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout

func finishPlayRequest():
	setPlayerTurn()

#####  Game State #####
#######################
func updateFigureLocation():
	for shape in shapes:
		shapes[shape]["onBoard"] = false
		for figure in $Arena/ArenaBoard.get_overlapping_areas():
			if figure.name == shape:
				shapes[shape]["onBoard"] = true
				break

func getVerticePosition(node_path : String) -> Vector2:
	var board_origin_x = get_node("Arena/ArenaBoard/VOrigin").global_position.x
	var board_origin_y = get_node("Arena/ArenaBoard/VOrigin").global_position.y
	return realToSimple(Vector2(get_node(node_path).global_position.x - board_origin_x, get_node(node_path).global_position.y - board_origin_y))

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
	var state = {"on_board" : [],"off_board" : []}
	updateFigureLocation()

	for shape in shapes:
		if shapes[shape]["onBoard"]:
			var rot = snapped(get_node(shape).get_rotation_degrees(), 0.01)
			var pos = getShapePosition(shape)
			var entry = { shape: { "position": pos, "rotation": rot } }
			state["on_board"].append(entry)
			
		else:
			var rot = snapped(get_node(shape).get_rotation_degrees(), 0.01)
			var entry = { shape: { "rotation": rot } }
			state["off_board"].append(entry)
		
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
	if movedPiece and not dragging and current_turn == "Player" and not hasRequest:		
		current_turn = "AI"
		thinking_asc = true
		time_elapsed = 0.0
		curr_think_state = 1
		SetHasRequest(true)
		ai_play()

func _undo_play():
	if movedPiece and not dragging and current_turn == "Player":
		get_node(movedPiece).position = originalPos
		get_node(movedPiece).rotation = originalRot
		movedPiece = ""

func movePiece(object_name: String, target_position: Vector2, target_rotation: float, duration: float):
	print(target_position)
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
	return extract_region_from_viewport(880, 115, 562, 540)

func get_piece_drawer_screen() -> Image:
	return extract_region_from_viewport(1600, 425, 210, 210)

#####  Input Handling  #####
############################
func _on_Debug_button_pressed():
	debugMode = !debugMode

func _on_finish_button_pressed():
	if current_turn != "Player":
		return
		
	for node in get_children():
		node.hide()
	get_node("Forms").show()

func _on_help_button_pressed():
	get_node("Controls").show()

func _on_mouse_entered(node_name):
	if not dragging and current_turn == "Player":
		obj_selected = node_name
