import asyncio
import os
from openai import OpenAI
from models.templates.tangramAgent import TangramAgent

class CustomAgent(TangramAgent):

    def __init__(self):
        super().__init__()
        self.chatLog = []
        self.model = "gpt-4o"
        self.temperature = 0.7
        self.max_tokens = 1024
        self.historyLimit = 20
        self.client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

        self.gameLogic = {
"type": "text", "text":"""Reference Information about the game: 
You and the human user are playing a tangram game, arranging the pieces to form an objective shape. 
The pieces are named by their colors: Red, Purple, Yellow, Green, Blue, Cream, and Brown.
Red and Cream are two large triangles, Yellow and green are two small triangles, Blue is a medium triangle, Purple is a small square, Brown is a tilted parallelogram.
We consider 0 degrees of rotation the triangles with their hypotenuse facing down, and the square in the square position (so the diamond shape corresponds to 45 degrees of rotation)
Example logical plays: Matching shapes can allow new larger shapes to appear, uniting two triangles of the same size by their Hypotenuse creates a square of that size in the location or a diamond (can be used as a circle) shape if the triangles are angled by 45 degrees. The Purple Square or a square created of 2 triangles can serve to form many things like heads, bodies, bases of structures. two triangles can also form a larger triangle when combined by their cathetus green and yellow can usually be used together or to fill similar objectives this could be used to make a another medium sized triangle like blue if used with yellow and green.
It often makes sense to use pieces of the same shape to furfil similar objectives, for example if theres 2 arms, it makes sense to use similar pieces for each.
"""
}
        self.chatPrompt = {
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

    async def playRequest(self, data):
        """
        Function to handle a new play request from the game. Modify this function to implement your own agent.
        See Superclass TangramAgent or Api description for input/output formats.
        """
        return await super().playRequest(data)
    
    async def playFeedback(self, data):
        """
        Function to handle a feedback about the latest play from the game. Modify this function to implement your own agent.
        See Superclass TangramAgent or Api description for input/output formats.
        """
        return await super().playFeedback(data)

    async def chatRequest(self, data):
        board_img = data["board_img"]
        drawer_img = data["drawer_img"]
        
        game_state_dict = data["state"]
        objective = data["objective"]
        user_msg = data["message"]

        ai_msg = await self.send_GPT_message_query(objective, str(game_state_dict), user_msg, board_img, drawer_img)

        return {"type": "chat", "message": ai_msg}
    
    async def send_GPT_message_query(self, objective : str, game_state : str, user_msg : str, board_img, drawer_img):
        messages = self.chatLog[max(0,len(self.chatLog) - self.historyLimit):]

        messages.append({
            "role": "user",
            "content": [
                self.gameLogic,
                {"type": "text", "text": "Your objective this game is to form the shape of " + objective + "."},
                self.chatPrompt,
                #{"type": "text", "text": "Game image:"},
                #{"type": "image_url", "image_url": {
                #    "url": f"data:image/png;base64,{board_img}" 
                #}},
                #{"type": "text", "text": "Current piece drawer image:\n"},
                #{"type": "image_url", "image_url": {
                #    "url": f"data:image/png;base64,{drawer_img}"
                #}},
                {"type": "text", "text": "Current piece rotations:\n" + game_state + '\n'}
            ]
        })

        
        messages.append({"role": "user", "content": user_msg})

        self.chatLog.append({"role": "user", "content": user_msg})
        
        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
            temperature = self.temperature,
            max_tokens = self.max_tokens
        )

        return response.choices[0].message.content


async def main():
    agent = CustomAgent()
    await agent.start_server()

if __name__ == "__main__":
    asyncio.run(main())
