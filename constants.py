from openai import OpenAI
import google.generativeai as genai
import os


class ColumnNames:
    DATE = 'date'
    TEXT = 'text'
    AMOUNT = 'amount'
    MERCHANT = 'merchant'
    CATEGORY = 'category'

    @classmethod
    def as_list(cls):
        return [cls.DATE, cls.TEXT, cls.AMOUNT, cls.MERCHANT, cls.CATEGORY]

    @classmethod
    def as_str(cls):
        # Returns column names as a formatted string with single quotes and commas
        return ", ".join(f"'{name}'" for name in cls.as_list())

    @classmethod
    def initial_columns_as_list(cls):
        return [cls.DATE, cls.TEXT, cls.AMOUNT]

    @classmethod
    def additional_columns_as_list(cls):
        return [cls.MERCHANT, cls.CATEGORY]


class PlotSettings:
    TITLE_SIZE = 24
    LABEL_SIZE = 14
    DEFAULT_COLORS = [
        "#FD4084", "#6AB43E", "#00A4EF", "#F70D1A",
        "#FFD700", "#8A2BE2", "#FF6347", "#4682B4",
        "#32CD32", "#FF4500", "#1E90FF", "#DAA520",
        "#D2691E", "#FF69B4", "#8B4513", "#7FFF00",
        "#DC143C", "#0000FF", "#006400", "#FF8C00",
        "#9400D3", "#FF1493", "#00CED1", "#FF0000"
    ]


class Colors:
    PRIMARY_COLOR = "#249d3c"
    SECONDARY_TEXT = "#a1a1a1"


class Globals:
    DEBUG = True
    DATE_FORMAT = '%d.%m.%Y'
    LOG_AI_PATH = os.path.join('logs', 'ai.log')
    MERCHANTS_MAX_WORDS = 7


class OpenAIConfig:
    MODEL = "gpt-3.5-turbo-0125"  # "gpt-4o"
    CHUNK_SIZE = 15

    @classmethod
    def set_client(cls):
        with open('openai_key.txt', 'r') as file:
            openai_key = file.read().strip()
        return OpenAI(api_key=openai_key)


class GenAIConfig:
    MODEL = genai.GenerativeModel("gemini-1.5-flash")
    CHUNK_SIZE = 40

    if Globals.DEBUG:
        TEMPERATURE = 1
    else:
        TEMPERATURE = 0.2

    GENERATION_CONFIG = genai.types.GenerationConfig(temperature=TEMPERATURE)

    @classmethod
    def set_client(cls):
        with open('gemini_key.txt', 'r') as file:
            genai_key = file.read().strip()
        return genai.configure(api_key=genai_key)


def get_ai_config(name):
    if name == "openai":
        return OpenAIConfig
    elif name == "genai":
        return GenAIConfig
    else:
        raise ValueError("Unsupported model name")


AIConfig = get_ai_config("genai")
