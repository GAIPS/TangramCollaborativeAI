extends Node2D

var game_mode = ""
var current_turn = ""

var game_task

var obj_selected = "" 
var dragging = false
var overlapping = false
var last_move = ""
var report = ""

const figures_info = {"Red" : "", "Yellow" : "", "Green" : "", "Blue" : "", "Purple" : "" , "Brown" : "", "Cream" : ""}
var figures_on_board = []
var figures_outside_board = []


var movedPiece = ""
var originalPos
var originalRot
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

#Tasks

var possible_tasks = ["A house", "A fish", "A human", "A rocket", "A cat", "A robot"]

func _ready():
	game_task = possible_tasks[randi_range(0,possible_tasks.size()-1)]
	$"Arena/TargetDisplayText/Objective".text = game_task
	#$Arena/TargetDisplay/task.texture = load("res://PNG/Task_Colors_" + str(game_task) + ".png")
	game_mode = "Turn Based AI"
	current_turn = "Player"
	startTime = Time.get_datetime_dict_from_system()
	print(startTime)

	#AI_move_pice("Green", Vector2(100, 100), PI/2, 2.0)

func getElapsedTime():
	var currentTime = Time.get_datetime_dict_from_system()
	var elapsed_seconds = (Time.get_unix_time_from_datetime_dict(currentTime) - Time.get_unix_time_from_datetime_dict(startTime))
	return elapsed_seconds

func registerPlayerChat():
	chatSent += 1

func registerAIChat():
	chatReceived += 1

func SetHasRequest(value):
	hasRequest = value
	
func setPlayerTurn():
	current_turn = "Player"
	movedPiece = ""
	SetHasRequest(false)

# TODO: ADD INTERACTION TO INTERACTION HISTORY, may not use relative move grammar, and coordinates instead
func finishPlayerTurn():
	if movedPiece and not dragging and current_turn == "Player" and not hasRequest:		
		current_turn = "AI"
		thinking_asc = true
		time_elapsed = 0.0
		curr_think_state = 1
		SetHasRequest(true)
		ai_play() #TODO: ADD HISTORY AND INSTRUCTION AS CONTEXT 

func _undo_play():
	if movedPiece and not dragging and current_turn == "Player":
		get_node(movedPiece).position = originalPos
		get_node(movedPiece).rotation = originalRot
		movedPiece = ""

func _process(_delta):
	#DEBUG -- uncomment prints you need for testing
	#print(get_game_state())
	#print("FIGURES ON BOARD: " + ",".join(figures_on_board))
	#print("FIGURES OUTSIDE BOARD: " + ",".join(figures_outside_board))
	#print(get_game_state())
	
	time_elapsed += _delta
		
	if obj_selected != "" and get_node(obj_selected).overlapping and not dragging:
		undo()
	if current_turn == "Player":
		get_node("Arena/AITurn").hide()
		get_node("Arena/HumanTurn").show()
		get_node("Arena/End Turn Button").modulate = Color8(255, 255, 255, 255)
		if movedPiece and not debugMode:
			get_node("Arena/Undo Button").modulate = Color8(255, 255, 255, 255)
			for piece in ["Red", "Yellow", "Cream", "Blue", "Green", "Purple", "Brown"]:
				if piece != movedPiece:
					get_node(piece).get_child(0).modulate = Color8(145, 145, 145, 255)	
				else:
					get_node(piece).get_child(0).modulate = Color8(255, 255, 255, 255)
		else:
			get_node("Arena/Undo Button").modulate = Color8(145, 145, 145, 255)		
			for piece in ["Red", "Yellow", "Cream", "Blue", "Green", "Purple", "Brown"]:
				get_node(piece).get_child(0).modulate = Color8(255, 255, 255, 255)
		if hasRequest:
			get_node("Arena/End Turn Button").modulate = Color8(145, 145, 145, 255)
	else:
		get_node("Arena/AITurn").show()
		get_node("Arena/HumanTurn").hide()
		get_node("Arena/End Turn Button").modulate = Color8(145, 145, 145, 255)
		get_node("Arena/Undo Button").modulate = Color8(145, 145, 145, 255)		
		if time_elapsed > ANIM_THINK_TIME:
			print(time_elapsed)
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
	
	var figures_on_board_now = []
	for figure in $Arena/ArenaBoard.get_overlapping_areas():
		if figure.name in figures_info.keys():
			figures_on_board_now.append(figure.name)
	figures_on_board = figures_on_board_now
	
	var figures_outside_board_now = []
	for figure in figures_info.keys():
		if figure not in figures_on_board:
			figures_outside_board_now.append(figure)
	figures_outside_board = figures_outside_board_now
	
	
func _on_DraggableObject_input_event(_viewport, event, _shape_idx, node_name):
	if event is InputEventMouseButton and !$"Start Menu".visible and current_turn == "Player" and obj_selected != "" and (not movedPiece or obj_selected == movedPiece or debugMode):
		if not movedPiece or debugMode:
			movedPiece = obj_selected
			originalPos = get_node(obj_selected).position
			originalRot = get_node(obj_selected).rotation
			print("moving " + obj_selected + " this turn")
		if event.is_action("Click"):
			if event.is_pressed():
				dragging = true
				get_node(obj_selected).start_drag()
			else:
				if not get_node(obj_selected).overlapping:
					dragging = false
					last_move = "drop"
					get_node(obj_selected).end_drag()
					
		elif Input.is_action_just_pressed("Ctrl_Right_click"):
			last_move = "turned x"
			get_node(obj_selected).scale.y *= -1
			
		elif Input.is_action_just_pressed("Right_click"):
			last_move = "rotated"
			if snappedf(get_node(obj_selected).rotation + PI/4, 0.0001) == snappedf(2*PI, 0.0001):
				get_node(obj_selected).rotation = 0
			else:
				get_node(obj_selected).rotation += PI/4
					
		elif Input.is_action_just_pressed("Ctrl_click"):
			last_move = "turned y"
			get_node(obj_selected).scale.x *= -1

func ai_play():
	obj_selected = ""
	await $Arena/AI_Player.ai_play(game_task)
	
func undo():
	dragging = true
	get_node(obj_selected).start_drag()
	last_move = ""

func _on_mouse_entered(node_name):
	if not dragging and current_turn == "Player":
		obj_selected = node_name

func error(err, format):
	$TextEdit2.text = ""
	$TextEdit2.placeholder_text = "syntax error: incorrect" + err + format
	
func _on_finish_button_pressed():
	for node in get_children():
		node.hide()
	get_node("Forms").show()


func _on_help_button_pressed():
	get_node("Controls").show()
	
# Converts a node's global coordinates into board coordinates
func get_coordinates_of_vertice_with_board_offset(node_path : String) -> Vector2:
	var board_origin_x = get_node("Arena/ArenaBoard/VOrigin").global_position.x
	var board_origin_y = get_node("Arena/ArenaBoard/VOrigin").global_position.y
	return Vector2(get_node(node_path).global_position.x - board_origin_x, get_node(node_path).global_position.y - board_origin_y)

# Gets all of a figure vertice's board coordinates
func get_figure_position_info(figure_name : String) -> Array:
	var figure_state = [] # index 0 -> center vertice, 1-4 -> other vertices
	figure_state.append(get_coordinates_of_vertice_with_board_offset(figure_name + "/VCenter"))
	for i in range(1,5):
		if has_node(figure_name + "/V" + str(i)):
			figure_state.append(get_coordinates_of_vertice_with_board_offset(figure_name + "/V" + str(i)))
	return figure_state
	
func get_relative_coordinates(node_path: String) -> Vector2:
	return Vector2(get_node(node_path).position.x, get_node(node_path).position.y) 

# Gets all of a figure vertice's relative coordinates towards center of the figure
func get_figure_relative_position_info(figure_name : String) -> Array:
	var figure_relative_state = [] # Center vertice is left out since it always is 0,0
	for i in range(1,5):
		if has_node(figure_name + "/V" + str(i)):
			figure_relative_state.append(get_relative_coordinates(figure_name + "/V" + str(i)))
	return figure_relative_state
	
func get_game_state() -> Dictionary:	
	var state = {"on_board" : [],"off_board" : []}

	for figure_name in figures_info.keys():
		if figure_name in figures_on_board:
			state["on_board"].append({figure_name : {}})
			#state["on_board"][-1][figure_name]["position"] = get_figure_position_info(figure_name)
			state["on_board"][-1][figure_name]["rotation"] = get_node(figure_name).get_rotation_degrees()
		elif figure_name in figures_outside_board:
			state["off_board"].append({figure_name : {}})
			#state["off_board"][-1][figure_name]["position"] = get_figure_relative_position_info(figure_name)
			state["off_board"][-1][figure_name]["rotation"] = get_node(figure_name).get_rotation_degrees()
		
	return state


func get_game_state2(leftX: float, rightX: float, bottomY: float, topY: float) -> String:
	var state = {"on_board": [], "off_board": []}
	var figures = ["Red", "Green", "Yellow", "Brown", "Cream", "Blue", "Purple"]

	var positions_rotations = []
	var all_in_drawer = true

	for figure_name in figures:
		var figure_node = get_node(figure_name)
		var figure_position = figure_node.global_position
		var figure_rotation = figure_node.rotation_degrees

		var relative_x = snapped(remap(float(figure_position.x), 550, 825, 0, 100), 0.01)
		var relative_y = snapped(remap(float(figure_position.y), 110, 360, 0, 100), 0.01)
		if relative_y <= 120: 
			positions_rotations.append(
				str(figure_name) + " is at " + str(relative_x) + " " + str(relative_y) + " with rotation " + str(figure_rotation)
			)
			all_in_drawer = false

	if all_in_drawer:
		return "all pieces are in the drawer."  

	return ", ".join(positions_rotations) + ", all other pieces are in the drawer." + "\n\n"


# Scaling is not straightfoward in godot, this work fines for normal windown and fullscreen
func get_board_screen():
	var pos_x = get_node("Arena/ArenaBoard/VOrigin").global_position.x
	var pos_y = get_node("Arena/ArenaBoard/VOrigin").global_position.y
	var width = abs(get_node("Arena/ArenaBoard/VUpperRightCorner").global_position.x - pos_x)
	var height = abs(get_node("Arena/ArenaBoard/VBottomLeftCorner").global_position.y - pos_y)
	
	var region = Rect2(pos_x*1.67,pos_y*1.67,width*1.67,height*1.67)
	
	var image = get_viewport().get_texture().get_image().get_region(region)

	return image

func get_piece_drawer_screen():
	var pos_x = get_node("Arena/ArenaPieceDrawer/VOrigin").global_position.x
	var pos_y = get_node("Arena/ArenaPieceDrawer/VOrigin").global_position.y
	var width = abs(get_node("Arena/ArenaPieceDrawer/VUpperRightCorner").global_position.x - pos_x)
	var height = abs(get_node("Arena/ArenaPieceDrawer/VBottomLeftCorner").global_position.y - pos_y)
	
	var region = Rect2(pos_x*1.67,pos_y*1.67,width*1.67,height*1.67)
	
	var image = get_viewport().get_texture().get_image().get_region(region)

	return image
	

func _on_data_set_entry_button_pressed():
	get_data_set_entry()

# This needs the Training Data folder and the task folders to already exist
# These can be downloaded for local use from the onedrive link provided in github
func get_data_set_entry():
	
	var entry_index = DirAccess.get_directories_at("./TrainingData/Task" + str(game_task)).size() + 1
	var entry_path = "./TrainingData/Task" + str(game_task) + "/Entry" + str(entry_index)# + '/'
	if !DirAccess.dir_exists_absolute(entry_path):
		DirAccess.make_dir_absolute(entry_path)
	entry_path = entry_path + '/'
	
	var board_image = get_board_screen()
	board_image.save_png(entry_path + "board.png")
	
	#var drawer_image = get_left_pieces_screen()
	#drawer_image.save_png(entry_path + "drawer.png")
	
	var game_state_str = get_game_state()
	game_state_str = JSON.stringify(game_state_str, "\t")
	
	var game_state_file = FileAccess.open(entry_path + "game_state.txt", FileAccess.WRITE)
	game_state_file.store_string(game_state_str)
	game_state_file.close()

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


func _on_Debug_button_pressed():
	debugMode = !debugMode

func isDebug():
	return debugMode
