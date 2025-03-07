# Simple Agent

## Core Functionality

This agent follows within the following workflow:

1. **Chat Handling**
   - Receives player messages
   - Analyzes conversation context and game state
   - Generates relevant responses about the current puzzle

2. **Move Generation**
   - Evaluates the current board state via images
   - Considers the objective shape and conversation history
   - Decides on a move and sends it using gpt4o

3. **Feedback Processing**
   - Receives information about move validity
   - Makes adjustments based on collision detection
   - Iteratively reviews the result with gpt4o and sends adjusted plays until the shape is properly placed.
   - Limits adjustment attempts to prevent endless loops

**Limitations**
- The agent can make up to 10 adjustment attempts before forcing a finish
