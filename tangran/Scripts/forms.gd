extends Control

var values = [0]

# Called when the node enters the scene tree for the first time.
func _ready():
	pass # Replace with function body.

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	if 0 in values:
		get_node("Submit").modulate = Color8(145, 145, 145, 255)
	else:
		get_node("Submit").modulate = Color8(255, 255, 255, 255)
	
func _on_exit_pressed():
	$".".hide()

func _on_rate_click(_viewport, event, _shape_idx, question_no, star_no):
	if not event is InputEventMouseButton:
		return
	values[question_no] = star_no
	for n in range(1,6):
		if n > star_no:
			setActive(question_no, n, false)
		else:
			setActive(question_no, n, true)

func setActive(question_no, star_no, value):
	var star = get_node(str(question_no)).get_node(str(star_no))
	if value:
		star.get_node("Active").show()
		star.get_node("InActive").hide()
	else:
		star.get_node("Active").hide()
		star.get_node("InActive").show()
		
func _on_Submit():
	if 0 in values:
		return
	
	#get_parent().saveStatistics(values)
	get_tree().quit(0)
