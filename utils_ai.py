from constants import OpenAIConfig, GenAIConfig


def query_ai(query, config, client):
    if isinstance(config, OpenAIConfig):
        return query_chatgpt(query, client)
    elif isinstance(config, GenAIConfig):
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
    response_formatted = response.choices[0].message.content.strip().split("\n")
    return response_formatted


def query_genai(query, config):
    response = config.MODEL.generate_content(query)
    response_formatted = response.text.splitlines()
    return response_formatted
