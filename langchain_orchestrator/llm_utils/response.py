from collections.abc import AsyncGenerator
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from .session_history import get_session_history
import logging

async def get_ai_response(message: str, chain, session_id: str) -> AsyncGenerator:
    """
    Function to get the AI response, sending only incremental chunks
    Args:
    message: The message
    chain: The chain
    session_id: The session ID
    """
    logger = logging.getLogger()
    logger.info("Getting AI response")
    
    history = get_session_history(session_id)
    chat_history = []
    for msg in history.messages:
        if isinstance(msg, HumanMessage):
            chat_history.append({"type": "human", "content": msg.content})
        elif isinstance(msg, AIMessage):
            chat_history.append({"type": "ai", "content": msg.content})
    
    # For debugging
    chunk_counter = 0
    total_length = 0
    
    logger.info("Starting AI response stream")
    try:
        async for chunk in chain.astream(
            {"input": message},
            config={"configurable": {"session_id": session_id}}
        ):
            if 'answer' in chunk and chunk['answer'] != "":
                chunk_counter += 1
                new_content = chunk['answer']
                
                total_length += len(new_content)
                logger.info(f"Sending chunk #{chunk_counter}: {len(new_content)} chars, total so far: {total_length}")
                logger.info(f"Chunk content: {new_content}")
                
                yield new_content
        
        logger.info(f"Streaming complete: {chunk_counter} chunks, {total_length} total chars")
        
    except Exception as e:
        logger.error(f"Error in get_ai_response streaming: {str(e)}")
        yield f"Error generating response: {str(e)}"