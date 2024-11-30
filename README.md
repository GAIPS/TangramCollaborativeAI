# Tangram Collaboration platform: Build puzzles with an assistant's help

## Demo available at: https://gaips.github.io/TangramCollaborativeAI/

Our main goal on this research project was to develop an easy-to-use online turn-based game where people, aided by our AI assistants, could build tangram patterns for any given objective.

The agents are powered by GPT4o and each perform individual tasks:

- **Chatting**: Text communication with human player for strategy planning, explanations, idea suggestion and other topic-related questions.
- **Playing**: Draws plays to be made on the AI turn by taking into account various context cues (current game state, previous plays and the chat history). The game state is given by images of both the board and the "drawer" (where the pieces yet to be placed are waiting), and a json-like dictionary containing rotation values for each piece (can be toggled to also include piece coordinates).
- **Action-Converter**: Makes the Playing agent plays into actual actions in the godot platform. Expert in our internal play-conversion grammars.

Below is a video showcasing a normal game interaction:
[![Video showcasing platform interaction with the objective being the construct a human using tangram pieces](https://cdn-cf-east.streamable.com/image/daqlcb.jpg?Expires=1730069848460&Key-Pair-Id=APKAIEYUVEN4EVB2OKEQ&Signature=Nd60v6~XwzHorozDT0GRwM6wrxfaWcGnerdxlYUxzDITM-bKcUI23qZjNqZpFdomumjVyt72JCL0tmlem6PPQREm-Y0apVoOS0rp1FidTGpZdZxT3tDhISUrcwOKxOxYLxIIIPd4otaOBdHWAXCax58GIjABem9bxU-1Jdjdbg4bpvcmDJzz948l6Ahh2k2RK3PVykvw3Ww15t5wxMD3t033ckPje2WR3Dse7UOAI2lC9docWYwdFVtPVoy5UV1HFyA~jtIlRPEME69pcgNRaVWqDa8HGuVzU2MQybQM0L~tA2HWOd1VsCpwU61mKRY9p3f8hV2kj8WqxpAnGkVKDQ__)](https://streamable.com/daqlcb)
