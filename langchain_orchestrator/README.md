# Dialectic Snippet Bot

A sophisticated chatbot system designed to provide programming assistance with context-aware responses. Built with AWS services and LangChain, this system retrieves relevant code snippets from a knowledge base and generates tailored responses.

## System Architecture

The Dialectic Snippet Bot is built as a WebSocket-based service leveraging several AWS technologies:
- Amazon Bedrock for LLM capabilities
- Amazon DynamoDB for session management
- AWS Lambda for serverless execution
- Amazon OpenSearch for vector search
- API Gateway for WebSocket communication

## Core Components

### History-Aware Context Processing (`history_aware.py`)

This module enables the bot to understand and process user questions in the context of previous conversation. It contains:

- `contextualize_q_system_prompt`: A system prompt that helps reformulate user questions based on chat history
- `contextualize_q_prompt`: A ChatPromptTemplate for general questions
- `contextualize_program_prompt`: A ChatPromptTemplate specialized for program-related questions

### Prompt Loading System (`load_prompts.py`)

This module allows dynamic loading of prompts from S3:

- `load_prompts_from_s3()`: Downloads and imports a Python module from an S3 bucket
- `main()`: Convenience function that loads the core snippet prompts

### QA Chat System (`qa_chat.py`)

Defines the prompt templates for question answering:

- `question_answer_prompt`: General question-answering template
- `snippet_program_prompt`: Template specific to program snippets
- `create_snippet_prompt()`: Factory function for language-specific snippet prompts
- `create_program_prompt()`: Factory function for language-specific program prompts

### Response Generation (`response.py`)

Handles AI response generation and streaming:

- `get_ai_response()`: Asynchronous generator function that streams AI responses chunk by chunk
- Includes logging for debugging response streaming

### Session Management (`session_history.py`)

Manages chat history using DynamoDB:

- `get_session_history()`: Retrieves chat history for a specific session
- Uses DynamoDB for persistent chat history with configurable TTL

### LangChain Orchestrator (`langchain_orchestrator.py`)

The core component that ties everything together:

- WebSocket connection management (`handle_connect()`, `handle_disconnect()`)
- Message processing (`handle_message()`, `process_message()`)
- LangChain setup with retrieval-augmented generation (RAG)
- Vector search configuration with OpenSearch
- Streaming response handling
- Session-based chat history

## Key Features

1. **Context-Aware Responses**: Understands follow-up questions by maintaining chat history
2. **Language-Specific Code Generation**: Can generate code snippets in specified programming languages
3. **Retrieval-Augmented Generation**: Uses vector search to find relevant code snippets
4. **Streaming Responses**: Sends responses in chunks for better user experience
5. **Session Management**: Maintains conversation context across interactions

## Flow of Operations

1. Client establishes WebSocket connection (handled by `handle_connect()`)
2. User sends a message with optional language specification
3. `process_message()` creates appropriate LangChain chain
4. The system retrieves relevant documents using vector search
5. A context-aware retriever processes the question with chat history
6. The LLM generates a response using retrieved context
7. Response is streamed back to the client in chunks
8. Chat history is updated in DynamoDB

## Environment Configuration

The system relies on several environment variables:
- `MODEL_NAME`: Bedrock model to use
- `TEMPERATURE`: LLM temperature setting
- `OPENSEARCH_URL`: OpenSearch endpoint
- `OPENSEARCH_INDEX`: OpenSearch index name
- `REGION`: AWS region
- `EMBEDDING_MODEL`: Model used for embeddings
- `CONNECTIONS_TABLE`: DynamoDB table for WebSocket connections
- `DYNAMO_TABLE_NAME`: DynamoDB table for chat history
- `DYNAMODB_MESSAGE_TTL`: Time-to-live for chat messages

## Usage

The bot is accessed via WebSocket connections and supports the following operations:

1. **Connect**: Establish a WebSocket connection
2. **Send Message**: Send a message with the following structure:
   ```json
   {
     "message": "Your question here",
     "language": "python",  // Optional language specification
     "type": "chat"         // "chat" or "program"
   }
   ```
3. **Disconnect**: Close the WebSocket connection

The response is streamed back in chunks with the following format:
```json
{
  "type": "stream",
  "content": "chunk of content"
}
```

When the response is complete, a message with `"type": "done"` is sent.

## Error Handling

The system includes comprehensive error handling and logging:
- Connection errors are handled gracefully
- Processing errors are reported back to the client
- Extensive logging for debugging purposes

## Development and Extension

To extend the bot:
1. New prompts can be added to the S3 bucket
2. Additional language support can be added by updating the vector search filters
3. The system can be extended with new chain types for different response formats