# Simple Agent

## Core Functionality

The agent processes three main types of interactions:

1. **Chat Handling**
   - Receives player messages
   - Analyzes conversation context and game state
   - Generates relevant responses about the current puzzle

2. **Move Generation**
   - Evaluates the current board state via images
   - Considers the objective shape and conversation history
   - Formulates and executes strategic moves to progress toward the solution

3. **Feedback Processing**
   - Receives information about move validity
   - Makes adjustments based on collision detection
   - Iteratively refines moves until a valid placement is achieved
   - Limits adjustment attempts to prevent endless loops

**Limitations**
- The agent can make up to 10 adjustment attempts before forcing a finish
