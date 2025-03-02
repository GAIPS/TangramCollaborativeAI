# Relational Agent

This agent implements a relational move strategy for playing tangram puzzles. Instead of using coordinates, moves are defined in relation to other pieces already on the board.

## Workflow

The agent operates through the following sequence:

1. **Move Planning**
   - The server sends a prompt to ChatGPT requesting reasoning for the best next moves
   - ChatGPT responds with potential moves described in natural language
   - These moves reference relationships between pieces (e.g., "place Red to the right of Blue")
   - The agent has access to chat history, though limited to a certain number of previous messages to manage costs

2. **Dual Prompt Processing**
   - The server issues two follow-up prompts:
     - First prompt requests a detailed explanation of the chosen move
     - Second prompt requests the move formatted for parsing

3. **Coordinate Calculation**
   - The server interprets the relational move description
   - It calculates coordinates based on the referenced piece's position

4. **Iterative Placement**
   - The piece is initially placed at the reference piece's position
   - After each feedback response, the system:
     - Checks for conflicts with other pieces
     - If conflicts exist, shifts the piece along the relational vector
     - If no conflicts exist, finalizes the placement with "FINISH"

5. **Move Communication**
   - After completing each move, the server sends the AI's reasoning to the game
   - This provides context and explanation for the move that was just executed

## Chat Handling

The agent uses separate dedicated prompts specifically for chat interactions:
- Each player message receives a response from the agent
- The chat functionality operates independently from the move generation system
- This ensures the agent maintains engaging conversation while still focusing on gameplay
- Chat history is maintained but limited to control API costs while preserving context

`The limited chat history is also sent during the move generation.`  
This approach allows the agent to think about piece placement conceptually rather than with precise coordinates, creating more natural and intuitive gameplay while maintaining responsive communication with the player.