extends Sprite2D

var undo = []

func _on_input_event(_viewport, event, _shape_idx, node_name):
	if event is InputEventMouseButton and visible:
		if event.is_action("Click"):
			if event.is_pressed():
				$"..".get_node(node_name).hide()
				undo.append(node_name)

func _on_undo_pressed():
	var node_name = undo.pop_back()
	$"..".get_node(node_name).show()
	var has_4 = true if $"..".get_node_or_null(node_name + "/V4") != null else false

func _on_done_pressed():
	hide()
