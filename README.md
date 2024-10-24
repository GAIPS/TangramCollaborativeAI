# Tangram Collaboration platform: Build puzzles with an assistant's help

Our main goal on this research project was to develop an easy-to-use online turn-based game where people, aided by our AI assistants, could build tangram patterns for any given objective.

The agents are powered by GPT4o and each perform individual tasks:

- **Chatting**: Text communication with human player for strategy planning, explanations, idea suggestion and other topic-related questions.
- **Playing**: Draws plays to be made on the AI turn by taking into account various context cues (current game state, previous plays and the chat history). The game state is given by images of both the board and the "drawer" (where the pieces yet to be placed are waiting), and a json-like dictionary containing rotation values for each piece (can be toggled to also include piece coordinates).
- **Action-Converter**: Makes the Playing agent plays into actual actions in the godot platform. Expert in our internal play-conversion grammars.

Below is a video showcasing a normal game interaction:
