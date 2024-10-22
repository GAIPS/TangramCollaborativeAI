from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from openai import OpenAI
client = OpenAI()

files = client.files.list()

for file in files:
    if file.purpose == "vision":
        client.files.delete(file.id)