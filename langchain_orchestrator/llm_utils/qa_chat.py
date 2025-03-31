"""
Project: 
Dialectic Chatbot

Purpose: 
Define the QA prompt for the Dialectic chatbot.

Prepared for: 
Dialectic

Prepared by:
Andrew Mark Dale - Research Assistant, AI Hub, Durham College

Comments:
This module takes our defined prompt and generates a response based on the chat history and user input.
"""

from .load_prompts import main
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder

try:
    prompts = main()
    SNIPPET_PROMPT = prompts.SNIPPET_PROMPT
    SNIPPET_PROGRAM_PROMPT = prompts.SNIPPET_PROGRAM_PROMPT

except Exception as e:
    print(e)

question_answer_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", SNIPPET_PROMPT),
        MessagesPlaceholder("chat_history", n_messages=10),
        ("human", "{input}"),
    ]
)

snippet_program_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", SNIPPET_PROGRAM_PROMPT),
        MessagesPlaceholder("chat_history", n_messages=5),
        ("human", "{input}"),
    ]
)

def create_snippet_prompt(language: str, prompt: str = SNIPPET_PROMPT) -> ChatPromptTemplate:
    """
    
    Function to create a snippet prompt.
    
    Args:
        prompt: The prompt to use
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", prompt.replace("{language}", language)),
            MessagesPlaceholder("chat_history", n_messages=5),
            ("human", "{input}"),
        ]
    )

def create_program_prompt(language: str, prompt: str = SNIPPET_PROGRAM_PROMPT) -> ChatPromptTemplate:
    """
    
    Function to create a program prompt.
    
    Args:
        prompt: The prompt to use
    """

    return ChatPromptTemplate.from_messages(
        [
            ("system", prompt.replace("{language}", language)),
            MessagesPlaceholder("chat_history", n_messages=5),
            ("human", "{input}"),
        ]
    )