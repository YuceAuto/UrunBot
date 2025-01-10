# main.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List

# Import the logic and the bot access functions
from bots.fabiabot import get_fabia_answer
from bots.scalabot import get_scala_answer  # you'll define similarly
from bots.kamiqbot import get_kamiq_answer  # you'll define similarly
from logic.decision import should_compare, decide_which_bots

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    combined_answer: str
    bot_responses: dict

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_prompt = request.prompt

    # 1. Decide which bots to invoke
    bots_to_invoke = decide_which_bots(user_prompt)

    # 2. Check if we need comparison
    comparison_mode = should_compare(user_prompt)

    # 3. Collect responses
    bot_responses = {}
    for bot_name in bots_to_invoke:
        if bot_name == "fabia":
            bot_responses["FabiaBot"] = get_fabia_answer(user_prompt)
        elif bot_name == "scala":
            bot_responses["ScalaBot"] = get_scala_answer(user_prompt)
        elif bot_name == "kamiq":
            bot_responses["KamiqBot"] = get_kamiq_answer(user_prompt)

    # 4. Combine or compare the responses
    if comparison_mode and len(bot_responses) > 1:
        # Example approach: Summarize differences
        # In practice, you might feed the responses into another LLM
        # that produces a structured comparison. For now, let's just
        # do a naive string with each response labeled.
        combined = "Comparing answers:\n\n"
        for name, resp in bot_responses.items():
            combined += f"{name}: {resp}\n"
        # Possibly add a final comparison statement here
        combined += "\n(End of comparison.)"
    else:
        # If not in comparison mode or there's only one bot,
        # we can just return the single (or first) response
        # or merge them in a simpler way.
        combined = " | ".join(bot_responses.values())

    return ChatResponse(combined_answer=combined, bot_responses=bot_responses)