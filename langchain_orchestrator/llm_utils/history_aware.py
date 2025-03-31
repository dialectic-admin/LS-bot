"""
This module contains the prompt for the history-aware retrieval model.
The purpose of this model is to take a user question and a chat history and return an answer to the user's question.

Project: 
Dialectic Snippet Bot

Prepared for: 
Dialectic

Prepared by:
Andrew Mark Dale - Research Assistant, AI Hub, Durham College
"""

from langchain_core.prompts import MessagesPlaceholder
from langchain.prompts import ChatPromptTemplate

# This prompt recontextualizes the user's question based on the context of the chat history
# Consider asking a question about a specific snippet and then asking a follow-up question about the same snippet.
contextualize_q_system_prompt: str = """
Given a chat history and the latest user input which might reference context in the chat history,
formulate a standalone question which can be understood without the chat history.

Consider the base prompt when reformulating the answer. If the prompt gives a conditional based on the input, include the formatting details in the output.

Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
"""

contextualize_q_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history", n_messages=5),
        ("human", "{input}"),
    ]
)

contextualize_program_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history", n_messages=5),
        ("human", "{input}"),
    ]
)