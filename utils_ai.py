from constants import OpenAIConfig, GenAIConfig


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
    response_formatted = response.choices[0].message.content
    return response_formatted


def query_genai(query, config):
    response = config.MODEL.generate_content(query).text
    return response
