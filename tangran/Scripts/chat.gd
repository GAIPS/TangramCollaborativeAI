extends Node
	
func add_message(text: String, is_ai: bool, explanation = false):
	# Create an HBoxContainer for the message
	var hbox = HBoxContainer.new()
	
	hbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Create a MarginContainer for the message bubble
	var margin_container = MarginContainer.new()

	# Set margin overrides for the MarginContainer
	var margin_value = 15
	margin_container.add_theme_constant_override("margin_top", margin_value)
	margin_container.add_theme_constant_override("margin_bottom", margin_value)
	margin_container.add_theme_constant_override("margin_left", margin_value)
	margin_container.add_theme_constant_override("margin_right", margin_value)
	
	
	margin_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Create the Label for the message
	var label = Label.new()
	label.set_text(text + "\n")

	label.add_theme_font_size_override("font_size", 70)
	
	label.set_autowrap_mode(TextServer.AUTOWRAP_WORD_SMART)

	
	margin_container.add_child(label)

	# If it's an AI message, align it to the right
	if is_ai:
		label.add_theme_color_override("font_color", Color(1, 1, 1))
		margin_container.add_theme_constant_override("margin_left", 250)
		hbox.add_child(margin_container)  # Add the message
	else:
		margin_container.add_theme_constant_override("margin_right", 250)
		hbox.add_child(margin_container)  # Add the message (left)

	# Add the HBoxContainer to the VBoxContainer (the chat window)
	get_node("../ScrollContainer/VBoxContainer").add_child(hbox)
	print(text)
	scroll_to_bottom_smooth()
	
func scroll_to_bottom_smooth():
	var v_scroll = $"../ScrollContainer".get_v_scroll_bar()
	var scroll_duration = 2.0
	
	if v_scroll:
		# Get the current scroll value and the target value (the bottom)
		var start_value = v_scroll.value
		var target_value = v_scroll.max_value

		# If we are not already at the bottom, animate the scroll
		if start_value != target_value:
			var time_passed = 0.0

			# Perform the scrolling over `scroll_duration` seconds
			while time_passed < scroll_duration:
				time_passed += get_process_delta_time()

				# Interpolate the scroll value between start and target
				v_scroll.value = lerp(start_value, target_value, time_passed / scroll_duration)

				# Wait for the next frame
				await get_tree().process_frame
	
func getRoot():
	return get_parent().get_parent().get_parent()

func _on_pressed():
	if not len($"../TextEdit2".text) > 0 or get_parent().get_parent().get_parent().isInTutorial:
		return

	getRoot().sendChatMsg($"../TextEdit2".text)

	add_message("User: " + $"../TextEdit2".text, false)
	
	$"../TextEdit2".text = ""

