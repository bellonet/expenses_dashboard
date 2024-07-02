from openai import OpenAI


class ColumnNames:
    DATE = 'date'
    TEXT = 'text'
    COST = 'cost'
    CATEGORY = 'category'

    @classmethod
    def as_list(cls):
        return [cls.DATE, cls.TEXT, cls.COST, cls.CATEGORY]

    @classmethod
    def as_set(cls):
        return {cls.DATE, cls.TEXT, cls.COST, cls.CATEGORY}

    @classmethod
    def as_str(cls):
        # Returns column names as a formatted string with single quotes and commas
        return ", ".join(f"'{name}'" for name in cls.as_list())


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


class OpenAIConfig:
    MAX_TOKENS = 4096
    RESPONSE_TOKENS = 500
    CHUNK_SIZE = MAX_TOKENS - RESPONSE_TOKENS

    @staticmethod
    def set_openai_client():
        with open('openai_key.txt', 'r') as file:
            openai_key = file.read().strip()
        return OpenAI(api_key=openai_key)
