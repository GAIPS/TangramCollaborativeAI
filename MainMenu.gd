extends Control


# Called when the node enters the scene tree for the first time.
func _ready():
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	pass
	
func _on_no_ai_choice_pressed():
	get_node("../../MainScene").game_mode = "No AI"
	get_node("../../MainScene").current_turn = "Player"
	hide()
	
func _on_turn_based_ai_pressed():
	get_node("../../MainScene").game_mode = "Turn Based AI"
	get_node("../../MainScene").current_turn = "Player"
	hide()
