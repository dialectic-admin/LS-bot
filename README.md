# Learning Snippets Bot

An intelligent chatbot system that provides context-aware learning snippet assistance and educational content in both English and French. The system leverages AWS services and LangChain to retrieve relevant code snippets and generate natural language responses.

## System Architecture

The Learning Snippets Bot combines several AWS services in a serverless architecture.


## Key Features

- **Context-Aware Conversations**: Maintains chat history to understand follow-up questions
- **Bilingual Support**: Provides content in both English and French
- **Language Expertise**: Offers specialized snippet assistance in French or English
- **Vector-Based Retrieval**: Uses semantic search to find relevant educational content
- **Real-Time Streaming**: Delivers responses in chunks for better user experience

## Core AWS Services

### Amazon Bedrock

- Powers the LLM (Large Language Model) capabilities
- Generates contextually relevant responses
- Creates vector embeddings for semantic search
- Provides built-in safeguards and content filtering

### AWS Lambda

#### Chatbot Lambda
- Processes user messages from WebSocket connections
- Orchestrates the LangChain components
- Streams responses back to clients
- Maintains conversation context

#### Indexing Lambda
- Processes educational content from DynamoDB
- Generates vector embeddings for search
- Updates or recreates the OpenSearch index
- Handles both full reindexing and incremental updates

#### Total Indexing Lambda 
- Deletes and recreates the vector database
- Useful for when you want to do a major overall of the database
- Processes educational content from DynamoDB
- Generates vector embeddings for search
- Updates or recreates the OpenSearch index
- Handles both full reindexing and incremental updates

### Amazon OpenSearch

- Stores vector embeddings for semantic search
- Powers the retrieval-augmented generation (RAG) system
- Supports KNN (k-nearest neighbors) queries for finding relevant content
- Configured with HNSW algorithm for efficient vector search

### Amazon API Gateway

- Provides WebSocket endpoint for real-time communication
- Manages client connections
- Routes messages to appropriate Lambda functions (connect, disconnect, handle messages)
- Handles authentication and authorization

### Amazon DynamoDB

#### Chat History Table
- Stores conversation history for each user session
- Enables context-aware responses
- Implements TTL (Time To Live) for automated cleanup

#### Snippets Table
- Stores educational content snippets
- Contains metadata, content, and resources
- Supports bilingual content with English and French versions

#### WebSocket Connections Table
- Stores information related to websocket connection ids
- Only stores this information while websockets are active. E.g., a table entry is created for when a websocket connects and it is deleted once it disconnects.

### Amazon S3

- Stores static resources and assets in the llm-learningsnippets-html-pages directory
- Hosts configuration files and prompts in the llm-aihub-prompts directory
- Maintains timestamps for incremental updates of the vector database in the llm-aihub-prompts-directory 
- Holds code for the lambda functions in the llm-aihub-code directory

### Amazon CloudFront

- Delivers frontend resources with low latency
- Caches static content
- Provides HTTPS encryption
- Improves global accessibility

## System Workflow

1. **User Connection**: Client connects via WebSocket to API Gateway
2. **Message Processing**: User sends a message with optional language preference
3. **Context Management**: System retrieves conversation history from DynamoDB
4. **Vector Search**: OpenSearch finds relevant snippet content
5. **LLM Processing**: Bedrock generates a response using retrieved context
6. **Streaming Response**: System streams response chunks back to the client
7. **History Update**: Conversation history is updated in DynamoDB

## Indexing Process

1. **Content Extraction**: Lambda retrieves content from DynamoDB
2. **Document Processing**: Content is transformed into structured documents
3. **Vector Embedding**: Bedrock generates vector embeddings
4. **Index Management**: OpenSearch index is updated (incrementally or fully)

## Development and Extension

The system is designed to be extensible:
- New prompts can be added to customize responses
- Additional languages can be supported
- New content types can be indexed
- Alternative LLM models can be integrated

## Environment Variables

The system relies on various environment variables for configuration, including:
- Model names and parameters
- Endpoint URLs
- Table names
- Authentication settings
- Performance tuning parameters
