extends Control

var current_index = 0
var controls = []
var active = false

@onready var text_edit : TextEdit = get_parent().get_node("Arena/ChatBox/TextEdit2")
@onready var btn : TextureButton = get_parent().get_node("Arena/Controls Button")

func _ready():
	#Swap before building
	
	hideTutorial()
	#startTutorial() 

func startTutorial():
	get_parent().isInTutorial = true
	disable_text_edit()
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
	enable_text_edit() 
	for control in controls:
		control.visible = false
	current_index = 0
	active = false
	get_parent().isInTutorial = false

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
	btn.disabled = true

func enable_text_edit():
	text_edit.editable = true
	btn.disabled = false
