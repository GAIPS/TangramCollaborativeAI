Below is the revised documentation with updated naming for the "Game to Agent" section (now fully consistent with the "Agent to Game" section) and corrected index links in the table of contents.

---

# Developer API

The platform supports the implementation of custom AI agents. To facilitate this, we provide a [base class](models/templates/tangramAgent.py) that manages local connections with the game, along with a [template](models/templates/agentTemplate.py) to help you quickly get started with your custom agent development. You can find additional details and documentation [here](models/README.md).

Any AI agent that adheres to the API specifications outlined in this document will integrate seamlessly with the platform.

## Table of Contents

- [Message Exchange Documentation](#message-exchange-documentation)
  - [Agent to Game Overview](#agent-to-game-overview)
  - [Agent to Game Formats](#agent-to-game-formats)
    - [Playing Messages](#playing-messages)
    - [Conclude Playing Turn](#conclude-playing-turn)
    - [Chatting Messages](#chatting-messages)
  - [Game to Agent Overview](#game-to-agent-overview)
  - [Game to Agent Formats](#game-to-agent-formats)
    - [Playing Messages](#platform-playing-messages)
    - [Chatting Messages](#platform-chatting-messages)
    - [Error Messages](#platform-error-messages)

---

# Message Exchange Documentation

## Agent to Game Overview

All messages exchanged between the AI agent server and the Godot game are formatted in JSON. The protocol defines three primary message types:

- **play:** Sent after a `playRequest` or `playFeedback` is received. This message describes a play to be performed in the game. The game may reject an invalid request with an error (resulting in the agent’s turn being skipped) or it may return a `playFeedback` to allow adjustments.
- **finish:** Sent to conclude the agent’s turn. If the current state violates game rules, the agent’s turn will automatically be undone and skipped.
- **chat:** Sends a chat message to the chatbox.

---

### Agent to Game Formats

The agent server sends its responses to the Godot game using the following messages:

#### Playing Messages

This message specifies a play to be executed in the game.

| Field       | Type           | Description                                                                                   |
|-------------|----------------|-----------------------------------------------------------------------------------------------|
| `type`      | string         | Must be `"play"`.                                                                             |
| `shape`     | string         | The name of the piece to be played (e.g., "Red", "Cream", etc.).                              |
| `position`  | Array of Float | The (X, Y) coordinates representing the center of the piece.                                |
| `rotation`  | Float          | The rotation in degrees for the piece.                                                      |
| `timestamp` | string         | Timestamp of the message (ISO 8601 format is recommended).                                   |

#### Conclude Playing Turn

This message concludes the agent's turn.

| Field       | Type   | Description                                                       |
|-------------|--------|-------------------------------------------------------------------|
| `type`      | string | Must be `"finish"`.                                               |
| `timestamp` | string | Timestamp of the message (ISO 8601 format is recommended).        |

#### Chatting Messages

This message sends a chat reply to the game’s chatbox.

| Field       | Type   | Description                                                                  |
|-------------|--------|------------------------------------------------------------------------------|
| `type`      | string | Must be `"chat"`.                                                            |
| `message`   | string | The chat reply message to be displayed to the player.                      |
| `timestamp` | string | Timestamp of the message (ISO 8601 format is recommended).                   |

---

## Game to Agent Overview

All messages exchanged between the Godot game and the AI agent server are formatted in JSON. The protocol defines four primary message types:

- **playRequest:** Sent at the start of the AI's turn, including all necessary data for decision making.
- **playFeedback:** Sent after the platform receives a play request, providing data to adjust the play.
- **chatRequest:** Sends a chat message for the agent to reply to.
- **error:** Sent if the platform detects a problem with a received message format.

---

### Game to Agent Formats

The game sends messages to the agent server in two categories: playing actions and chatting.

#### Platform Playing Messages

The agent must be capable of responding to both `playRequest` and subsequent `playFeedback` messages. Upon receiving a `playFeedback`, the agent can either send an updated `play` or a `finish` response.

| Field                          | Type             | Description                                                                                                                                                                 |
|--------------------------------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `type`                         | string           | `"playRequest"` for the initial play, or `"playFeedback"` for subsequent adjustments.                                                                                      |
| `objective`                    | string           | The objective of the current game.                                                                                                                                          |
| `state`                        | object           | Contains game state information.                                                                                                                                            |
| &emsp; `on_board`              | object           | Information on pieces currently on the board.                                                                                                                               |
| &emsp;&emsp; `{PIECE}`         | object[]         | Each `{PIECE}` represents a piece’s name and its information. Valid pieces include "Red", "Cream", "Purple", "Brown", "Blue", "Yellow", and "Green".                    |
| &emsp;&emsp;&emsp; `position`  | Vector Array     | (X, Y) coordinates of the center of the piece.                                                                                                                              |
| &emsp;&emsp;&emsp; `vertices`  | Array of Vector Array | (X, Y) coordinates for each vertex of the piece.                                                                                                                       |
| &emsp;&emsp;&emsp; `rotation`  | number           | Rotation in degrees.                                                                                                                                                        |
| &emsp;&emsp;&emsp; `collisions`| Array of Strings | Names of pieces currently colliding with the piece, or `"BOUNDARY"` if the piece is out of bounds.                                                                          |
| &emsp; `off_board`             | object           | Information on pieces not yet placed on the board.                                                                                                                          |
| &emsp;&emsp; `{PIECE}`         | object[]         | Each `{PIECE}` represents a piece’s name and its information (same valid pieces as above).                                                                                  |
| &emsp;&emsp;&emsp; `vertices`  | object           | X,Y coordinates of each vertex relative to the center (0,0).                                                                                                                 |
| &emsp;&emsp;&emsp; `rotation`  | number           | Rotation in degrees.                                                                                                                                                        |
| `board_img`                    | base64 image     | A base64 encoded image of the current board state.                                                                                                                        |
| `drawer_img`                   | base64 image     | A base64 encoded image of the piece drawer.                                                                                                                                 |
| `timestamp`                    | string           | Timestamp of the message (ISO 8601 format is recommended).                                                                                                                |

#### Platform Chatting Messages

When the game sends a chat request, the following fields should be included:

| Field                          | Type             | Description                                                                                                                                                                 |
|--------------------------------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `type`                         | string           | `"chatRequest"`                                                                                                                                                             |
| `objective`                    | string           | The objective of the current game.                                                                                                                                          |
| `message`                      | string           | The chat message sent by the player.                                                                                                                                        |
| `state`                        | object           | Contains the current game state information.                                                                                                                                |
| &emsp; `on_board`              | object           | Information on pieces currently on the board.                                                                                                                               |
| &emsp;&emsp; `{PIECE}`         | object[]         | Each `{PIECE}` represents a piece’s name and its information. Valid pieces include "Red", "Cream", "Purple", "Brown", "Blue", "Yellow", and "Green".                    |
| &emsp;&emsp;&emsp; `position`  | Vector Array     | (X, Y) coordinates of the center of the piece.                                                                                                                              |
| &emsp;&emsp;&emsp; `vertices`  | Array of Vector Array | (X, Y) coordinates for each vertex of the piece.                                                                                                                       |
| &emsp;&emsp;&emsp; `rotation`  | number           | Rotation in degrees.                                                                                                                                                        |
| &emsp;&emsp;&emsp; `collisions`| Array of Strings | Names of pieces currently colliding with the piece, or `"BOUNDARY"` if the piece is out of bounds.                                                                          |
| &emsp; `off_board`             | object           | Information on pieces not yet placed on the board.                                                                                                                          |
| &emsp;&emsp; `{PIECE}`         | object[]         | Each `{PIECE}` represents a piece’s name and its information.                                                                                                               |
| &emsp;&emsp;&emsp; `vertices`  | object           | X,Y coordinates of each vertex relative to the center (0,0).                                                                                                                 |
| &emsp;&emsp;&emsp; `rotation`  | number           | Rotation in degrees.                                                                                                                                                        |
| `board_img`                    | base64 image     | A base64 encoded image of the current board state.                                                                                                                        |
| `drawer_img`                   | base64 image     | A base64 encoded image of the piece drawer.                                                                                                                                 |
| `timestamp`                    | string           | Timestamp of the message (ISO 8601 format is recommended).                                                                                                                |

#### Platform Error Messages

This message sends a chat reply to the game’s chatbox.

| Field       | Type   | Description                                                                  |
|-------------|--------|------------------------------------------------------------------------------|
| `type`      | string | `"error"`                                                           |
| `message`   | string | Error Message.                      |
| `timestamp` | string | Timestamp of the message (ISO 8601 format is recommended).                   |

---