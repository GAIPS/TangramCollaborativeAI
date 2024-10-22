# ai_server.py

import signal
import sys
from flask import Flask, request, jsonify
import threading
import time
import os
from openai import OpenAI

app = Flask(__name__)

client          = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
assistantID     = "asst_pjIc9rfUQkWs383XVgMOWjGu"
assistantChatID = "asst_4L1QeC1VflNw6252h3ORbiI6"

thread = client.beta.threads.create()

files=[]
target = ""

@app.route('/ai_play', methods=['POST'])
def ai_play():
    global files, target, thread, client, assistantID, assistantChatID
    #print("my turn")
    #return jsonify({"response": "Chat: Let's use the green piece to start forming the base of the house. Since the green triangle is smaller, we can place it to form part of the roof.\n[Green, 50 60, 0]"})
    data = request.get_json()
    thread_id = thread.id
    move_input = data['move_input']

    print("DOING STUFF")
    if not target:
        target = client.files.create(
            file=open("PNG/Task_Colors_1.png", "rb"),
            purpose="vision"
        )
        files += target.id

    state = client.files.create(
        file=open("state.png", "rb"),
        purpose="vision"
    )

    files += state.id

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=[
            {"type": "text", "text": "This is our target"},
            {"type": "image_file", "image_file": {"file_id": target.id, "detail": "low"}},
            {"type": "text", "text": f"What move would you like to do for the state in this image, {move_input}"},
            {"type": "image_file", "image_file": {"file_id": state.id, "detail": "low"}},
        ],
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistantID
        #truncation_strategy={
        #    "type": "auto",
        #    "last_messages": 4
        #},
    )

    response = wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id)

    client.beta.threads.messages.delete(
        message_id=message.id,
        thread_id=thread_id,
    )

    print(response)
    return jsonify({"response": response})

@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    global files, target, thread, client, assistantID, assistantChatID
    data = request.get_json()
    thread_id = thread.id
    msg = data['msg']

    print("DOING Chat STUFF")

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=[
            {"type": "text", "text": f"This is our target {msg}"},
        ],
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistantChatID
        #truncation_strategy={
        #    "type": "auto",
        #    "last_messages": 4
        #},   
    )

    response = wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id, isChat=True)

    print(response)
    return jsonify({"response": response})

def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5, isChat=False):
    while True:
        print("Waiting for reply from openAI")
        time.sleep(sleep_interval)
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                if not isChat:
                    client.beta.threads.messages.delete(
                        message_id=last_message.id,
                        thread_id=thread_id,
                    )
                return response
        except Exception as e:
            print(f"An error occurred while retrieving the run: {e}")
            break

def shutDown(signal, frame):
    print("\Shutting down the server...")
    for file in files:
        client.files.delete(file.id)
    sys.exit(0)

# Register the signal handler for SIGINT (Ctrl-C) and SIGTERM (termination)
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)

if __name__ == '__main__':
    app.run(debug=True)
