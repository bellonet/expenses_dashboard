from constants import OpenAIConfig, GenAIConfig, Globals
import re


def query_ai(query, config, client):
    if config is OpenAIConfig:
        return query_chatgpt(query, client)
    elif config is GenAIConfig:
        return query_genai(query, config)
    else:
        raise ValueError("Invalid AI client.")


def query_chatgpt(query, client):
    messages = [
        {"role": "user",
         "content": query}
    ]
    response = client.chat.completions.create(
        model=OpenAIConfig.MODEL,
        messages=messages,
    )

    response = response.choices[0].message.content
    response = re.sub(r"(\w)'(\w)", r"\1\2", response)
    return response


def query_genai(query, config):
    response = config.MODEL.generate_content(query, generation_config=GenAIConfig.GENERATION_CONFIG).text
    response = re.sub(r"(\w)'(\w)", r"\1\2", response)

    if Globals.DEBUG:
        with open(Globals.LOG_AI_PATH, 'a') as f:
            f.write(f"Query: {query}\n")
            f.write(f"Response: {response}\n\n")
    return response
