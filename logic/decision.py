# logic/decision.py

from typing import List

def should_compare(prompt: str) -> bool:
    """
    Simple function to decide if we need a 'comparing question' mode.
    In real usage, you might parse the prompt or use an NLP classifier
    to decide if the user is asking for differences or comparisons.
    """
    keywords = ["compare", "difference", "which is better", "contrast", "vs"]
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in keywords)

def decide_which_bots(prompt: str) -> List[str]:
    """
    Decide which bot(s) should handle the user's query.
    For demonstration, let's say:
      - If the user mentions "fabia", we choose FabiaBot.
      - If the user mentions "scala", we choose ScalaBot.
      - If the user mentions "kamiq", we choose KamiqBot.
      - Otherwise, choose them all.
    Adjust this logic to your real needs.
    """
    prompt_lower = prompt.lower()

    selected_bots = []
    if "fabia" in prompt_lower:
        selected_bots.append("fabia")
    if "scala" in prompt_lower:
        selected_bots.append("scala")
    if "kamiq" in prompt_lower:
        selected_bots.append("kamiq")

    if not selected_bots:
        # If no specific mention, let's default to all
        selected_bots = ["fabia", "scala", "kamiq"]

    return selected_bots