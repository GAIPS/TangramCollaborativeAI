import asyncio
from models.templates.tangramAgent import TangramAgent

class CustomAgent(TangramAgent):
    def __init__(self):
        super().__init__()
        
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
        """
        Function to handle a new chat message from the player. Modify this function to implement your own agent.
        See Superclass TangramAgent or Api description for input/output formats.
        """
        return await super().chatRequest(data)

async def main():
    agent = CustomAgent()
    await agent.start_server()

if __name__ == "__main__":
    asyncio.run(main())
