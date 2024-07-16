import logging
import os
import streamlit as st
from constants import Globals, Colors
from openai import OpenAI
import google.generativeai as genai


def set_logger():
    logger = logging.getLogger()
    if Globals.DEBUG:
        logger.setLevel(logging.DEBUG)
        watchdog_logger = logging.getLogger('watchdog.observers')
        watchdog_logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)
    return logger


def set_st():
    st.set_page_config(layout="wide")
    st.title('Expenses Analyzer')
    st.markdown(
        f'<h4 style="color:{Colors.PRIMARY_COLOR};">Analyze your expenses to make smarter financial decisions.</h4>',
        unsafe_allow_html=True)

    st.markdown(
        f'<link rel="stylesheet" '
        f'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">',
        unsafe_allow_html=True)


def set_footer():
    footer = f"""
    <div style="color:{Colors.SECONDARY_TEXT}; width: 100%; text-align: left; padding: 10px 0;">
    <p>Please contact me for any bugs or feature requests: bellonet @ gmail</p>
    <p>Another amazing tool: 
    <a href="https://www.jonathanronen.com/time-to-retirement.html" target="_blank">Time to Retirement Calculator</a>
    , made by my better half ❤️</p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)


class OpenAIConfig:
    MODEL = "gpt-3.5-turbo-0125"  # "gpt-4o"
    CHUNK_SIZE = 15

    @classmethod
    def set_client(cls):
        with open(os.path.join('api_keys', 'openai_key.txt'), 'r') as file:
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
        with open(os.path.join('api_keys', 'gemini_key.txt'), 'r') as file:
            genai_key = file.read().strip()
        return genai.configure(api_key=genai_key)


def get_ai_config(name):
    if name == "openai":
        return OpenAIConfig
    elif name == "genai":
        return GenAIConfig
    else:
        raise ValueError("Unsupported model name")
