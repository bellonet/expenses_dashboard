from settings import OpenAIConfig, GenAIConfig
import google.generativeai as genai
from constants import Globals
import re


def query_ai(query, config, client, max_tokens=None):
    if config is OpenAIConfig:
        return query_chatgpt(query, client)
    elif config is GenAIConfig:
        return query_genai(query, config, max_tokens)
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


def query_genai(query, config, max_tokens):

    generation_config = (genai.types.GenerationConfig(temperature=GenAIConfig.TEMPERATURE))
                         # , max_output_tokens=max_tokens)

    response = config.MODEL.generate_content(query, generation_config=generation_config).text
    response = re.sub(r"(\w)'(\w)", r"\1\2", response)

    if Globals.DEBUG:
        with open(Globals.LOG_AI_PATH, 'a') as f:
            f.write(f"Query: {query}\n")
            f.write(f"Response: {response}\n\n")
    return response
