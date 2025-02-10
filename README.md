# Tangram Collaboration platform: Build puzzles with an assistant's help

## Demo available at: https://gaips.github.io/TangramCollaborativeAI/

Our main goal on this research project was to develop an easy-to-use online turn-based game where people, aided by our AI assistants, could build tangram patterns for any given objective.

The agents are powered by GPT4o and each perform individual tasks:

- **Chatting**: Text communication with human player for strategy planning, explanations, idea suggestion and other topic-related questions.
- **Playing**: Draws plays to be made on the AI turn by taking into account various context cues (current game state, previous plays and the chat history). The game state is given by images of both the board and the "drawer" (where the pieces yet to be placed are waiting), and a json-like dictionary containing rotation values for each piece (can be toggled to also include piece coordinates).
- **Action-Converter**: Makes the Playing agent plays into actual actions in the godot platform. Expert in our internal play-conversion grammars.

Below is a video showcasing a normal game interaction:
[![Video showcasing platform interaction with the objective being the construct a human using tangram pieces](https://cdn-cf-east.streamable.com/image/daqlcb.jpg?Expires=1730069848460&Key-Pair-Id=APKAIEYUVEN4EVB2OKEQ&Signature=Nd60v6~XwzHorozDT0GRwM6wrxfaWcGnerdxlYUxzDITM-bKcUI23qZjNqZpFdomumjVyt72JCL0tmlem6PPQREm-Y0apVoOS0rp1FidTGpZdZxT3tDhISUrcwOKxOxYLxIIIPd4otaOBdHWAXCax58GIjABem9bxU-1Jdjdbg4bpvcmDJzz948l6Ahh2k2RK3PVykvw3Ww15t5wxMD3t033ckPje2WR3Dse7UOAI2lC9docWYwdFVtPVoy5UV1HFyA~jtIlRPEME69pcgNRaVWqDa8HGuVzU2MQybQM0L~tA2HWOd1VsCpwU61mKRY9p3f8hV2kj8WqxpAnGkVKDQ__)](https://streamable.com/daqlcb)

### Developer API

# Python Server - Godot Game Message Exchange Documentation

All exchanged messages will be in JSON format.
Currently, only 2 types of JSON messages are expected, each in its own socket channel:

- Playing messages
- Chat messages

## Game to Server

### G->S Playing

| Field       | Type   | Description |
|------------|--------|-------------|
| `type`     | string | "playRequest" or "playFeedback"|
| `objective`     | string          | Objective of the current game |
| `state` | object         | Contains game state info |
| &emsp; `on_board`    | object          | Info on pieces on the board |
| &emsp;&emsp; `{PIECE}`   | object[]        | `{PIECE}` is a piece's name and contains its info |
| &emsp;&emsp;&emsp; `position` | Vector Array         | (X, Y) coordinates of the center |
| &emsp;&emsp;&emsp; `vertices` | Array of Vector Array       | (X, Y) coordinates of the each vertice |
| &emsp;&emsp;&emsp; `rotation` | number         | Rotation in degrees |
| &emsp;&emsp;&emsp; `collisions` | Array of Strings        | Names of pieces currently colliding with `{PIECE}` or `BOUNDARY`, if out of bounds |
| &emsp;`off_board`   | object          |
| &emsp;&emsp; `{PIECE}`   | object[]        | `{PIECE}` is a piece's name and contains its info |
| &emsp;&emsp;&emsp; `vertices` | object       | X,Y coordinates of vertice in relation to center (0,0) |
| &emsp;&emsp;&emsp; `rotation` | number         | Rotation in degrees |
| `board_img`     | base64 image    | Image of the current board |
| `drawer_img`    | base64 image    | Image of the piece drawer |
| `timestamp`     | string          | |

### G->S Chatting

| Field       | Type   | Description |
|------------|--------|-------------|
| `type`     | string | "chatRequest"|
| `objective`     | string          | Objective of the current game |
| `message` | string | |
| `timestamp`     | string          | |

## Server to game

### S->G Playing

| Field       | Type   | Description |
|------------|--------|-------------|
| `type`     | string | "play"|
| `shape`    | string | "Red", "Cream", ... |
| `position` | Array Float | (X,Y) |
| `rotation` | Float | |
| `timestamp`     | string          ||

### S->G Chatting

| Field       | Type   | Description |
|------------|--------|-------------|
| `type`     | string | "chat"|
| `message`  | string | |
| `timestamp`     | string          ||