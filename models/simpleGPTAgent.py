import asyncio
import os
from openai import OpenAI
from tangramAgent import TangramAgent

class ChatAgent():
    def __init__(self):
        super().__init__()
        self.chatLog = []
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.max_tokens = 1024
        self.historyLimit = 20
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Initial system message for chat
        self.chatLog.append({
            "role": "system",
            "content": """You and the human user are playing a tangram game, arranging the pieces to form an objective shape. 
The pieces are named by their colors: Red, Purple, Yellow, Green, Blue, Cream, and Brown.
Red and Cream are two large triangles, Yellow and green are two small triangles, Blue is a medium triangle, Purple is a small square, Brown is a tilted parallelogram.
We consider 0 degrees of rotation the triangles with their hypotenuse facing down, and the square in the square position (so the diamond shape corresponds to 45 degrees of rotation)
Example logical plays: Matching shapes can allow new larger shapes to appear, uniting two triangles of the same size by their Hypotenuse creates a square of that size in the location or a diamond (can be used as a circle) shape if the triangles are angled by 45 degrees. The Purple Square or a square created of 2 triangles can serve to form many things like heads, bodies, bases of structures. two triangles can also form a larger triangle when combined by their cathetus green and yellow can usually be used together or to fill similar objectives this could be used to make a another medium sized triangle like blue if used with yellow and green.
It often makes sense to use pieces of the same shape to furfil similar objectives, for example if theres 2 arms, it makes sense to use similar pieces for each. Maintain friendly, concise dialogue (1-3 sentences). Suggest ideas to progress us towards our objective, collaboratively, not demands. Follow all formatting rules from the prompt."""
        })

    async def handleChat(self, objective, game_state, user_msg, board_img, drawer_img):
        messages = self.chatLog[-self.historyLimit:]
        user_message = await self.makeChatMessage(objective, game_state, user_msg)
        messages.append(user_message)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            print(f"OpenAI API error in handleChat: {e}")
            return "I'm having trouble responding right now."

        assistant_message = response.choices[0].message.content
        self.chatLog.append({"role": "assistant", "content": assistant_message})
        return assistant_message

    async def makeChatMessage(self, objective, game_state, user_msg):
        return {
            "role": "user",
            "content": (
                f"Current Objective: {objective}\n"
                f"Game State:\n{game_state}\n"
                f"New message to reply to:\n{user_msg}"
            )
        }

class PlayAgent():
    def __init__(self, chat_agent):
        super().__init__()
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.max_tokens = 1024
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chat_agent = chat_agent
        self.last_play_context = []
        # System message for play decisions
        self.play_system_message = {
            "role": "system",
            "content": (
                "You and the human user are playing a tangram game, arranging the pieces to form an objective shape. "
                "You will be provided the last messages shared between both of you to help you take into consideration previous discussions and decisions. "
                "The pieces are named by their colors: Red, Purple, Yellow, Green, Blue, Cream, and Brown. "
                "Red and Cream are two large triangles, Yellow and green are two small triangles, Blue is a medium triangle, Purple is a small square, Brown is a tilted parallelogram. "
                "We consider 0 degrees of rotation the triangles with their hypotenuse facing down, and the square in the square position (so the diamond shape corresponds to 45 degrees of rotation). "
                "You generate tangram moves in exact format: {piece}, {rotation}, {x}, {y}\\n{message}. where piece is the name of one of our shapes, rotation is the angle in degrees (must be multiple of 45), "
                "and x, y are the float coordinates from 0 to 100, where 100,100 is the top right corner of the piece on the board. The message should be a short explanation of the move reasoning (1-3 lines at most)."
            )
        }

    async def generatePlay(self, objective, game_state, board_img, drawer_img):
        context = [
            self.play_system_message,
            {"role": "user", "content": f"Objective: {objective}\nGame State: {game_state}"}
        ]
        # Append last few chat messages (last 6) if available
        context.extend(self.chat_agent.chatLog[-6:])
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=context,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            print(f"OpenAI API error in generatePlay: {e}")
            return "Error generating play move."

        assistant_content = response.choices[0].message.content
        # Update last_play_context for feedback (retain context without altering feedback later)
        self.last_play_context = context + [{"role": "assistant", "content": assistant_content}]
        return assistant_content

class FeedbackAgent():
    def __init__(self, play_agent):
        super().__init__()
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.max_tokens = 256
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.playAgent = play_agent
        # System message for adjustments
        self.system_message = {
            "role": "system",
            "content": (
                "Adjust previous move based on recent feedback. Keep same format without additional messaging: {piece}, {rotation}, {x}, {y}."
                "Do not make completely different moves YOU MUST ONLY MOVE THE PIECE YOU WERE MOVING IN THIS TURN; simply suggest minor changes to avoid problems like overlapping or not creating the desired effect. "
                "However, if there are no overlaps and you are satisfied with the move, do not change the move and reply with exactly just the word, please avoid doing more that 3 adjustments but dont stop untill its not overlapping 'FINISH'."
            )
        }

    async def adjustPlay(self, game_state, hasOverlaps="No"):
        # Determine if there are any collisions in the game state
        for shape in game_state["on_board"]:
            if len(game_state["on_board"][shape]["collisions"]) > 0:
                hasOverlaps = "Yes"
                break

        messages = [msg for msg in self.playAgent.last_play_context if msg["role"] != "system"]
        messages.append(self.system_message)
        messages.append({
            "role": "user",
            "content": f"Feedback game state: {game_state}\nAre there Overlaps?: {hasOverlaps}\n"
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            print(f"OpenAI API error in adjustPlay: {e}")
            return "Error adjusting play move."

        assistant_content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_content})
        # Update last_play_context for future reference (without the play system message)
        self.playAgent.last_play_context = messages.copy()
        return assistant_content

class CustomAgent(TangramAgent):
    def __init__(self):
        super().__init__()
        self.chat_agent = ChatAgent()
        self.play_agent = PlayAgent(self.chat_agent)
        self.feedback_agent = FeedbackAgent(self.play_agent)
        self.recent_messages = []

    async def playRequest(self, data):      
        # Generate play with full game state and chat history
        play_response = await self.play_agent.generatePlay(
            data["objective"],
            data["state"],
            data["board_img"],
            data["drawer_img"]
        )
        print(play_response)
        a = await self.parsePlayResponse(play_response, data)
        print(a)
        return a

    async def playFeedback(self, data):
        # Get adjustments based on recent context (pass full feedback data)
        adjusted_play = await self.feedback_agent.adjustPlay(data["state"])
        return await self.parsePlayResponse(adjusted_play, data)

    async def chatRequest(self, data):
        # Store the incoming message
        self.recent_messages.append(data["message"])
        
        # Generate chat response with full history
        chat_response = await self.chat_agent.handleChat(
            data["objective"],
            data["state"],
            data["message"],
            data["board_img"],
            data["drawer_img"]
        )
        return {"type": "chat", "message": chat_response}

    async def parsePlayResponse(self, response, data=None):
        # Check if the response indicates no changes are needed
        if response.strip().upper() == "FINISH":
            return {"type": "finish", "timestamp": data["timestamp"] if data and "timestamp" in data else ""}
        
        try:
            # Split into move and message parts
            lines = response.split("\n", 1)
            move_part = lines[0]
            message_part = lines[1] if len(lines) > 1 else False
            parts = [part.strip() for part in move_part.split(",")]
            if len(parts) != 4:
                raise ValueError("Incorrect number of elements in move part.")
            piece, rotation, x, y = parts
            self.randomShape = piece
            res = [{
                "type": "play",
                "shape": piece,
                "position": (float(x), float(y)),
                "rotation": float(rotation),
                "timestamp": data["timestamp"] if data and "timestamp" in data else ""
            }]
            if message_part:
                res.append({"type": "chat", "message": message_part.strip()})
                return res
            return res[0]
        except Exception as e:
            print(f"Error parsing play response: {e}, response received: {response}")
            # Fallback to the base class implementation for a random move
            return await super().playRequest(data)

async def main():
    agent = CustomAgent()
    await agent.start_server()

if __name__ == "__main__":
    asyncio.run(main())
