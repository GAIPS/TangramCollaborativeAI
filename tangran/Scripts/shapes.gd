extends Area2D

var dragging = false
var overlapping = false

func _process(_delta):
	
	'''
	var overlapping_areas = get_overlapping_areas().find(get_node("../Arena/ArenaBoard"))
	if !(overlapping_areas == -1):
		print("Is this piece colliding with Board? Yes")
	'''
		
	overlapping = get_overlapping()
	if overlapping:
		modulate = "#ff291784"
	else:
		modulate = "#ffffff"

	if dragging:
		global_position = get_global_mouse_position()

func start_drag():
	z_index = 2
	dragging = true

func end_drag():
	z_index = 0
	dragging = false


func get_overlapping():
	var overlapping_areas = get_overlapping_areas()
	var num_overlaps = overlapping_areas.size()
	
	# The third condition is for the stars in the Forms, since they also have collisions
	for area in overlapping_areas:
		if area == get_node("../Arena/ArenaBoard") || area ==  get_node("../Arena/ArenaPieceDrawer") || area.name.is_valid_int():
			num_overlaps = num_overlaps - 1

	#DEBUG
	#print(num_overlaps)
	#print(overlapping_areas)
	
	if num_overlaps != 0:
		return true
	else:
		return false
