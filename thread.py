from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

thread = client.beta.threads.create()

print(thread.id)