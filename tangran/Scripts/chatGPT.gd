extends Node
#
var api_key = OS.get_environment("OPENAI_API_KEY")
#var model = "ft:gpt-4o-mini-2024-07-18:gaips:rel-moves-test3:9vo0aEQ4"
var model = "gpt-4o"
var temperature = 0.7
var max_tokens = 1024
var messages = []
var headers =  ["Content-type: application/json", "Authorization: Bearer " + api_key]
var data
var request 
var url = "https://api.openai.com/v1/chat/completions"

var messageLog = []
var historyLimit = 20

var num_exchanges_to_keep_in_history = 3 #Keep the last 3 User/AI Exchanges in history. FEEL FREE TO CHANGE

func _ready():
	request = HTTPRequest.new()
	add_child(request)
	
	request.request_completed.connect(_on_request_completed)
	
	
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
	label.set_text(text)

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


func _on_request_completed(_result, _response_code, _headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())

	var response = json.get_data()
	
	#TODO: interpret whether response or tool call
	
	print(response)
	var response_message = response.choices[0].message 
	#print(response_message)
	
	var message = response["choices"][0].message.content
	add_message("AI: " + message, true)

	messageLog = get_node("../../AI_Player").getUpdatedLog()
	messageLog.append({"role": "assistant", "content": message})
	
	getRoot().registerAIChat()
	
func getRoot():
	return get_parent().get_parent().get_parent()

func _on_pressed():
	if not len($"../TextEdit2".text) > 0:
		return

	getRoot().registerPlayerChat()

	var current_board64 = $"../../..".get_board_screen()
	current_board64 = Marshalls.raw_to_base64(current_board64.save_png_to_buffer())
	
	var current_piece_drawer64 = $"../../..".get_piece_drawer_screen()
	current_piece_drawer64 = Marshalls.raw_to_base64(current_piece_drawer64.save_png_to_buffer())
	
	messages = []

	messages = messageLog.slice(messageLog.size() - historyLimit, messageLog.size()).duplicate(true)

	#messages.append({"role": "system", "content": "Chat history:" + get_full_chat_history()})
	messages.append({
		"role": "user",
		"content": [
			gameLogic,
			get_objective_text(),
			chatPrompt,
			{"type": "text", "text": "Game image:"},
			{"type": "image_url", "image_url": {
				"url": "data:image/png;base64," + current_board64
			}},
			{"type": "text", "text": "Current piece drawer image:\n"},
			{"type": "image_url", "image_url": {
				"url": "data:image/png;base64," + current_piece_drawer64
			}},
			{"type": "text", "text": "Current piece rotations:\n" + str(getRoot().get_game_state()) + '\n'}
		]
	})
	
	messages.append({"role": "user", "content": "Player Question:" + $"../TextEdit2".text})
	
	var body = JSON.stringify({
		"messages": messages,
		"temperature": temperature,
		"max_tokens": max_tokens,
		"model": model
	})
	
	request.request(url, headers, HTTPClient.METHOD_POST, body)
	add_message("User: " + $"../TextEdit2".text, false)

	messageLog = get_node("../../AI_Player").getUpdatedLog()
	messageLog.append({"role": "user", "content": $"../TextEdit2".text})

	print(messageLog)
	print("\n\n\n\n\n\n\n")
	
	$"../TextEdit2".text = ""

### Prompts ###
var gameLogic = {
"type": "text", "text":"""Reference Information about the game: 
You and the human user are playing a tangram game, arranging the pieces to form an objective shape. 
The pieces are named by their colors: Red, Purple, Yellow, Green, Blue, Cream, and Brown.
Red and Cream are two large triangles, Yellow and green are two small triangles, Blue is a medium triangle, Purple is a small square, Brown is a tilted parallelogram.
We consider 0 degrees of rotation the triangles with their hypotenuse facing down, and the square in the square position (so the diamond shape corresponds to 45 degrees of rotation)
Example logical plays: Matching shapes can allow new larger shapes to appear, uniting two triangles of the same size by their Hypotenuse creates a square of in the location. The Purple Square or a square created of 2 triangles can serve to form many things like heads, bodies, bases of structures. 
Two triangles can also form a larger triangle when combined.
"""
}

var chatPrompt = {
"type": "text", "text": """You are an AI chatting with a Human Player thats arraging tangram tangram pieces with you and your co-assistents to reach a certain objective. 
To answer them, you will have access to the message history, an image of the current board, an image of the current piece drawer where the unplaced pieces lie.
Your task:
1. Review what you know about the game state.
2. Consider the players message and reply logically in an approachable and friendly way.

Rules:
- If you suggest moves or plays, always explicity describe how pieces should be placed in relation to each other.
- If you suggest either the move to create a large square or to create a large triangle, say it explicity. Ex: "Make a big square by using Cream and Red" or "Make a big triangle, placing Red to clockwise direction of Cream"
- Each individual piece, if present in a suggested move, should have a explicit rotation (except for the moves that form big squares and big triangles).
- If you disagree with an idea given by the player on how you should approach the challege, try to find a middle ground.
- If the game already looks finished to you, you can say it looks done.

Consider the previous messages and keep your message short, at most 1-3 sentences, the objective is a human-like nice short reply.
Remember you are collaborating so don't order ideias suggest them in a collaborative manner.
This message may not be the first in the conversation, but u can see the chat history in the previous message.
Examples:
- "Hey, well i think we could begin with the tail, using the medium blue triagle for it."
- "Ok, got it, i'll try to help you achieve that."
- "Alright I'll try to use the brown piece to create a tail."
- "I don't think the yellow piece would make a good roof due to it's size, maybe we could use cream for the same objective."
- "Sounds great, let's begin then!"
- "I think the game already looks like our objective."
"""
}

func get_objective_text():
	return {"type": "text", "text": "Your objetive this game is to form the shape of " + $"../../..".game_task + "."}

func getUpdatedLog():
	return messageLog
