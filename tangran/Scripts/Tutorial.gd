extends Control

var current_index = 0
var controls = []
var active = false

@onready var text_edit : TextEdit = get_parent().get_node("Arena/ChatBox/TextEdit2")

func _ready():
	#startTutorial()
	#get_parent().isInTutorial = true
	#disable_text_edit() 
	hideTutorial()
	pass

func startTutorial():
	get_parent().isInTutorial = true
	active = true
	current_index = 0
	controls = []
	for child in get_children():
		if child is Control:
			controls.append(child)
	
	for i in range(controls.size()):
		controls[i].visible = (i == 0)

func _input(event):
	if event is InputEventKey and event.pressed and event.keycode == KEY_SPACE and active:
		show_next_control()

func hideTutorial():
	for control in controls:
		control.visible = false
	current_index = 0
	get_parent().isInTutorial = false
	enable_text_edit() 
	active = false

func show_next_control():
	if controls.size() == 0:
		print("No controls to show!")
		return

	controls[current_index].visible = false

	current_index += 1

	if current_index >= controls.size():
		hideTutorial()
	else:
		controls[current_index].visible = true


func reset_visibility():
	for control in controls:
		control.visible = false
	current_index = 0

func disable_text_edit():
	text_edit.editable = false

func enable_text_edit():
	text_edit.editable = true
