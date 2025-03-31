from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
import os
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from dotenv import load_dotenv

load_dotenv()

DYNAMODB_TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME")
DYNAMODB_MESSAGE_TTL = int(os.environ.get("DYNAMODB_MESSAGE_TTL"))  # 24 hours default TTL

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Retrieve chat message history for a session from DynamoDB.
    
    Args:
        session_id: The session ID for the conversation
    
    Returns:
        BaseChatMessageHistory: The chat message history for the session
    """
    return DynamoDBChatMessageHistory(
        table_name=DYNAMODB_TABLE_NAME,
        session_id=session_id,
        primary_key_name="SessionId",
        ttl=DYNAMODB_MESSAGE_TTL
    )