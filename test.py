import openai

# Set your API key

# Assistant A
def get_fabia(user_message: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful Skoda Fabia assistant."},
        {"role": "user", "content": user_message},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
        max_tokens=512,
    )
    return response["choices"][0]["message"]["content"]


# Assistant B
def get_scala(user_message: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful Skoda Scala assistant."},
        {"role": "user", "content": user_message},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
        max_tokens=512,
    )
    return response["choices"][0]["message"]["content"]


# Assistant C
def get_kamiq(user_message: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful Skoda Kamiq assistant."},
        {"role": "user", "content": user_message},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
        max_tokens=512,
    )
    return response["choices"][0]["message"]["content"]

if __name__ == "__main__":
    # Prompt the user for their question at the command line
    user_question = input("Enter your question: ")

    if "fabia" in user_question:
        fabia_answer = get_fabia(user_question)
        scala_answer = "-"
        kamiq_answer = "-"
    elif "scala" in user_question:
        fabia_answer = "-"
        scala_answer = get_scala(user_question)
        kamiq_answer = "-"
    elif "kamiq" in user_question:
        fabia_answer = "-"
        scala_answer = "-"
        kamiq_answer = get_kamiq(user_question)

    # Print the responses
    print("[Fabia Assistant]:", fabia_answer)
    print("[Scala Assistant]:", scala_answer)
    print("[Kamiq Assistant]:", kamiq_answer)
