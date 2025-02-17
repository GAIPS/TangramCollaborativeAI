import numpy as np

figures_names = ["Purple","Brown","Cream","Red","Yellow","Green","Blue"]
possible_directions = ["right", "left", "top", "bottom", "top-right", "top-left", "bottom-right", "bottom-left"]

direction_vectors = {
    "right": np.array([1, 0]),
    "left": np.array([-1, 0]),
    "top": np.array([0, -1]),
    "bottom": np.array([0, 1]),
    "top-right": np.array([1, -1]),
    "top-left": np.array([-1, -1]),
    "bottom-right": np.array([1, 1]),
    "bottom-left": np.array([-1, 1])
}

last_dir = None
last_piece = None

def square_pos(game_state, refPiece : str, movePiece : str):
    valid_pairs = [["Red", "Cream"], ["Yellow", "Green"]]

    if refPiece not in game_state["on_board"].keys() or movePiece not in game_state["on_board"].keys():
        return "ERROR"

    for pair in valid_pairs:
        if refPiece in pair and movePiece in pair and movePiece != refPiece:

            snap_pos = (game_state["on_board"][refPiece]["position"]["SquareSnap"]["x_pos"], game_state["on_board"][refPiece]["position"]["SquareSnap"]["y_pos"])

            if game_state["on_board"][refPiece]["rotation"].rotation_degrees+180 >= 360:
                ref_rotation = game_state["on_board"][refPiece]["rotation"]+180 - 360
            else:
                ref_rotation= game_state["on_board"][refPiece]["rotation"] + 180 
            
            return (movePiece, snap_pos, ref_rotation)
    
    return "ERROR"

def triangle_pos(game_state, refPiece : str, dir : str, movePiece : str):
    valid_pairs = [["Red", "Cream"], ["Yellow", "Green"]]
	
    if refPiece not in game_state["on_board"].keys() or movePiece not in game_state["on_board"].keys():
        return "ERROR"

    for pair in valid_pairs:
        if refPiece in pair and movePiece in pair and refPiece != movePiece:
			
			#Based on the different rotation values the reference triangle could have, 
			#pick the correct placement for the triangle
			
            if dir == "clockwise":
                snap_pos = (game_state["on_board"][refPiece]["position"]["TriangleSnap1"]["x_pos"], game_state["on_board"][refPiece]["position"]["TriangleSnap1"]["y_pos"])
                ref_rotation = game_state["on_board"][refPiece]["rotation"] + 90
            elif dir == "anticlockwise":
                snap_pos = (game_state["on_board"][refPiece]["position"]["TriangleSnap2"]["x_pos"], game_state["on_board"][refPiece]["position"]["TriangleSnap2"]["y_pos"])
                ref_rotation = game_state["on_board"][refPiece]["rotation"] + 270
			
            if ref_rotation >= 360:
                ref_rotation = ref_rotation - 360
			
            return (movePiece, snap_pos, ref_rotation)
    return "ERROR"

def rotate_pos(game_state, piece, rot):
    if piece not in game_state["on_board"].keys():
        return "ERROR"
    
    pos = (game_state["on_board"][piece]["position"]["VCenter"]["x_pos"], game_state["on_board"][piece]["position"]["VCenter"]["y_pos"])

    rot = game_state["on_board"][piece]["rotation"] + rot

    return (piece, pos, rot)

def find_starting_coordinate_from_parallel_directions(game_state, common_direction, direction_and_related_piece):
    coordinates_x = []
    coordinates_y = []
    
    # Iterate over each piece in the dictionary
    for piece in direction_and_related_piece.keys():
        coordinates_x.append(game_state["on_board"][piece]["position"]["VCenter"]["x_pos"])
        coordinates_y.append(game_state["on_board"][piece]["position"]["VCenter"]["y_pos"])
    
    # Get the highest and lowest coordinates in x and y
    highest_x = max(coordinates_x)
    highest_y = max(coordinates_y)
    lowest_x = min(coordinates_x)
    lowest_y = min(coordinates_y)
    
    # Initialize x and y coordinates
    x = 0
    y = 0
    
    # Handle common direction cases
    if common_direction == "top":
        x = sum(coordinates_x) / len(coordinates_x)
        y = highest_y
    elif common_direction == "top-right":
        x = highest_x
        y = highest_y
    elif common_direction == "right":
        x = highest_x
        y = sum(coordinates_y) / len(coordinates_y)
    elif common_direction == "bottom-right":
        x = highest_x
        y = lowest_y
    elif common_direction == "bottom":
        x = sum(coordinates_x) / len(coordinates_x)
        y = lowest_y
    elif common_direction == "bottom-left":
        x = lowest_x
        y = lowest_y
    elif common_direction == "left":
        x = lowest_x
        y = sum(coordinates_y) / len(coordinates_y)
    elif common_direction == "top-left":
        x = lowest_x
        y = highest_y
    
    return (x, y)

def find_intersection(p1, d1, p2, d2):
    # Calculate the denominator for the intersection formula
    denominator = d1[0] * d2[1] - d1[1] * d2[0]
    
    # If the denominator is too small, lines are parallel or coincident
    if abs(denominator) < 0.0001:
        return None  # Lines are parallel or coincident
    
    # Calculate the values of t and s
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / denominator
    s = ((p2[0] - p1[0]) * d1[1] - (p2[1] - p1[1]) * d1[0]) / denominator
    
    # If t and s are both greater than or equal to 0, the intersection is on both segments
    if t >= 0 and s >= 0:
        return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)  # Calculate the intersection point
    return None

def find_common_intersection(points, directions):
    # Check if there are fewer than 2 points (not enough lines to find an intersection)
    if len(points) < 2:
        return None  # Not enough lines to find an intersection
    
    # Find the initial intersection between the first two points and directions
    intersection = find_intersection(points[0], directions[0], points[1], directions[1])
    
    # If no intersection is found between the first two, return None
    if intersection is None:
        return None
    
    # Iterate over the remaining points and directions
    for i in range(2, len(points)):
        new_intersection = find_intersection(intersection, directions[0], points[i], directions[i])
        
        # If no intersection is found with the current point, return None
        if new_intersection is None:
            return None
        
        # Update the intersection to the new intersection found
        intersection = new_intersection
    
    # Return the final intersection point
    return intersection

def findCoordinatesMoreThanOneRelated(game_state, pieceToMove, direction_and_related_piece):
    # Get the current piece coordinates
    current_piece_coordinates = (game_state["on_board"][pieceToMove]["position"]["VCenter"]["x_pos"], game_state["on_board"][pieceToMove]["position"]["VCenter"]["y_pos"])
    
    related_pieces_coordinates = []
    directions = []
    
    # Iterate through the direction_and_related_piece dictionary
    for piece, direction in direction_and_related_piece.items():
        # Get the direction vector using the direction (assuming direction_vectors is defined elsewhere)
        directions.append(direction_vectors[direction])
        
        related_pieces_coordinates.append((game_state["on_board"][piece]["position"]["VCenter"]["x_pos"], game_state["on_board"][piece]["position"]["VCenter"]["y_pos"]))
    
    # Find the common intersection of the coordinates and directions
    final_coordinate = find_common_intersection(related_pieces_coordinates, directions)
    
    # If no convergence, return the current piece coordinates
    if final_coordinate is None:
        print("Convergence will not happen")
        return current_piece_coordinates
    else:
        return final_coordinate

def relational_pos(game_state, move : str):
    global last_piece, last_dir
    GPTPlay_parts = move.rsplit(", ")
    num_directionPiece_pairs = ((GPTPlay_parts.size() - 4) / 2) + 1 # 4 fields are mandatory to be filled. 1 pair always exists for the mandatory direction-piece pair
    pieceToMove = GPTPlay_parts[0]
	
    if pieceToMove not in figures_names:
        print("Invalid Suggested Move: pieceToMove Name invalid " + pieceToMove)
        return "ERROR"
	
	# There is an edge case where multiple pieces have the same vector direction, we must find a common starting coordinate and apply the vector
    is_all_same_direction = True
    first_direction = GPTPlay_parts[1]
	
    play_iterator = 1
    direction_and_related_piece = {}
    while num_directionPiece_pairs != 0:
        direction = GPTPlay_parts[play_iterator]
        if direction not in possible_directions:
            print("Invalid Suggested Move: invalid direction " + direction)
            return "invalid"
			
        relatedPiece = GPTPlay_parts[play_iterator+1]
        if relatedPiece not in figures_names:
            print("Invalid Suggested Move: relatedPiece Name invalid " + relatedPiece)
            return "ERROR"
			
        direction_and_related_piece[relatedPiece] = direction
        if direction != first_direction:
            is_all_same_direction = False
		
        play_iterator += 2
        num_directionPiece_pairs -= 1
	
	
	# TODO: for some reason whe it rotates already rotated pieces, it rotates into invalid positions
	# FIX: limit rotationDegrees to be only legal values by aproximating into closest rotation
    rotationDegrees = (GPTPlay_parts[play_iterator]) + game_state["on_board"][pieceToMove]["rotation"]
    
	
    piecePreMoveCoordinates = (game_state["on_board"][pieceToMove]["position"]["VCenter"]["x_pos"], game_state["on_board"][pieceToMove]["position"]["VCenter"]["y_pos"])
    piecePreMoveRotation = 	game_state["on_board"][pieceToMove]["rotation"]
    piecePostMoveCoordinates = piecePreMoveCoordinates
	
	# CASE WHENEVER MORE THAN 1 REFERENCE PIECE IS USED, BUT ALL TOWARDS THE SAME DIRECTION
    if direction_and_related_piece.keys().size() > 1 and is_all_same_direction:
        piecePostMoveCoordinates = find_starting_coordinate_from_parallel_directions(game_state, first_direction, direction_and_related_piece)
        last_dir = first_direction
        last_piece = pieceToMove
        return(pieceToMove, piecePostMoveCoordinates, rotationDegrees)
        
		

	# CASE WHENEVER MORE THAN 1 REFERENCE PIECE IS USED
    elif direction_and_related_piece.keys().size() > 1:
        piecePostMoveCoordinates = findCoordinatesMoreThanOneRelated(pieceToMove, direction_and_related_piece) 
			
        if(piecePreMoveCoordinates == piecePostMoveCoordinates):
            print("Invalid Suggested Move: coordinates of direction vectors applied on related pieces will never converge")
            return "invalid"
		
        last_dir = first_direction
        last_piece = pieceToMove
        return(pieceToMove, piecePostMoveCoordinates, rotationDegrees)
		
			
	#CASE WHENEVER ONLY 1 REFERENCE PIECE IS USED
    else:
        direction = direction_vectors[direction_and_related_piece[direction_and_related_piece.keys()[0]]]
        piecePostMoveCoordinates = (game_state["on_board"][direction_and_related_piece.keys()[0]]["position"]["VCenter"]["x_pos"], game_state["on_board"][direction_and_related_piece.keys()[0]]["position"]["VCenter"]["y_pos"])

        last_dir = direction_and_related_piece[direction_and_related_piece.keys()[0]]
        last_piece = pieceToMove

        return(pieceToMove, piecePostMoveCoordinates, rotationDegrees)
        
def calculate_pos(move : str, game_state):
    global last_dir, last_piece
    last_piece = None
    last_dir = None
    if move.startswith("Square"):
        move_data = move.split(" ")
        return square_pos(game_state, move_data[1], move_data[2])
    elif move.startswith("Triangle"):
        move_data = move.split(" ")
        return triangle_pos(game_state, move_data[1], move_data[2], move_data[3])
    elif move.startswith("Finish"):
        return "FINISH"
    elif move.startswith("Rotate"):
        move_data = move.split(" ")
        return rotate_pos(game_state, move_data[1], move_data[2])
    else:
        return relational_pos(game_state, move)