import json
import os
import asyncio
from typing import Dict, Any
import time
import logging
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain.retrievers.document_compressors import EmbeddingsFilter
from llm_utils.session_history import get_session_history
from llm_utils.history_aware import contextualize_q_prompt, contextualize_program_prompt
from llm_utils.qa_chat import create_program_prompt, create_snippet_prompt
from llm_utils.response import get_ai_response
from langchain.retrievers import ContextualCompressionRetriever
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import ChatPromptTemplate
import boto3
from requests_aws4auth import AWS4Auth
from opensearchpy import RequestsHttpConnection, AWSV4SignerAuth
from dotenv import load_dotenv
# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()
MODEL_NAME = os.environ.get("MODEL_NAME")
TEMPERATURE = float(os.environ.get("TEMPERATURE"))
OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL")
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX")
EMBEDDING_REGION = os.environ.get("REGION")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
EMBEDDING_FUNCTION = BedrockEmbeddings(model_id=EMBEDDING_MODEL, region_name=EMBEDDING_REGION)
CONNECTIONS_TABLE = os.environ.get("CONNECTIONS_TABLE")
SERVICE = 'aoss'
# Debug: Print environment configuration
print(f"DEBUG: Initialized with MODEL_NAME={MODEL_NAME}, TEMPERATURE={TEMPERATURE}")
print(f"DEBUG: Using OpenSearch at {OPENSEARCH_URL}, index {OPENSEARCH_INDEX}")

CREDENTIALS = boto3.Session().get_credentials()
auth = AWS4Auth(
    CREDENTIALS.access_key,
    CREDENTIALS.secret_key,
    EMBEDDING_REGION,
    'aoss',
    session_token=CREDENTIALS.token
)

auth2 = AWSV4SignerAuth(
    credentials=CREDENTIALS,
    region=EMBEDDING_REGION,
    service=SERVICE
)
dynamodb = boto3.resource("dynamodb")
connections_table = dynamodb.Table(CONNECTIONS_TABLE)

def get_api_gateway_management_client(event: Dict[str, Any]) -> Any:
    """
    
    Create a client for the API Gateway Management API to send messages back to connected clients.

    Args:
        event: The lambda event containing connection information
    
    Returns:
        An API Gateway Management client
    """
    domain_name = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]
    endpoint_url = f"https://{domain_name}/{stage}"
    return boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)

async def send_to_connection(client: Any, connection_id: str, data: str, type: str) -> None:
    """
    Send a message to a connected WebSocket client.

    Args:
        client: The API Gateway Management client
        connection_id: The connection ID of the client
        data: The message to send
    """
    try:
        logger.info(f"Sending message to connection {connection_id}")
        await asyncio.to_thread(
            client.post_to_connection,
            ConnectionId=connection_id,
            Data=json.dumps({"type": type, "content": data}).encode('utf-8')
        )
    except client.exceptions.GoneException:
        logger.warning(f"Connection {connection_id} is gone, removing from connections table")
        await asyncio.to_thread(
            connections_table.delete_item,
            Key={"ConnectionId": connection_id}
        )
    except Exception as e:
        logger.error(f"Error sending message to connection {connection_id}: {str(e)}")

def init_llm() -> ChatBedrock:  
    print(f"DEBUG: Initializing Bedrock LLM with model {MODEL_NAME}")
    return ChatBedrock(model=MODEL_NAME, temperature=TEMPERATURE, streaming=True, region=EMBEDDING_REGION, max_tokens=4096)

def bot_creation(
        retriever: ContextualCompressionRetriever,
        llm: ChatBedrock,
        contextualize_q_prompt: ChatPromptTemplate,
        qa_prompt: ChatPromptTemplate
        ) -> RunnableWithMessageHistory:
    print("DEBUG: Creating bot chain with history-aware retriever")
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )

def create_chain(session_id: str, language: str, type_of_chat: str):
    """
    Create the LangChain chain based on the session ID and language.
    
    Args:
        session_id: The session ID for the conversation
        language: Optional language for code generation
    
    Returns:
        The LangChain chain with message history
    """
    start_time = time.time()
    print(f"DEBUG: Creating chain for session_id={session_id}, language={language}, type={type_of_chat}")
    
    # Set up embeddings
    print("DEBUG: Setting up BedrockEmbeddings")
    # Set up vector store
    vectorstore = OpenSearchVectorSearch(
            opensearch_url=OPENSEARCH_URL,
            http_auth=auth2,
            connection_class = RequestsHttpConnection,
            index_name=OPENSEARCH_INDEX,
            embedding_function=EMBEDDING_FUNCTION,
            is_aoss=True,
            use_ssl=True,
            verify_certs=True,
            vector_field="vector_field",
            text_field="content",
            space_type="l2",
            ef_search=512,
            engine="nmslib"
    )
    # Create base retriever with optional language filter
    search_kwargs = {
        "k": 15,
        "filter": {
            "term": {
                "metadata.language": language
            }
        },
    }

    
        
    print(f"DEBUG: Creating base retriever with search_kwargs={search_kwargs}")
    base_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    # Create embeddings filter for contextual compression
    print("DEBUG: Setting up embeddings filter with threshold 0.2")
    embeddings_filter = EmbeddingsFilter(
        embeddings=EMBEDDING_FUNCTION, 
        similarity_threshold=0.05
    )
    
    # Create contextual compression retriever
    print("DEBUG: Creating contextual compression retriever")
    retriever = ContextualCompressionRetriever(
        base_compressor=embeddings_filter,
        base_retriever=base_retriever
    )
    
    # Initialize LLM
    llm = init_llm()
    
    # Create appropriate chain based on language parameter
    if type_of_chat == "program":
        print(f"DEBUG: Creating program generation chain for language: {language}")
        chain = bot_creation(
            retriever=base_retriever,
            llm=llm,
            contextualize_q_prompt=contextualize_program_prompt,
            qa_prompt=create_program_prompt(language)
        )
    else:
        print(f"DEBUG: Creating standard QA chain for language {language}")
        chain = bot_creation(
            retriever=base_retriever,
            llm=llm,
            contextualize_q_prompt=contextualize_q_prompt,
            qa_prompt=create_snippet_prompt(language)
        )
    
    end_time = time.time()
    print(f"DEBUG: Chain creation completed in {end_time - start_time:.2f} seconds")
    return chain

async def process_message(message: str,
                          connection_id: str,
                          apigw_client: Any,
                          type_of_chat: str,
                          language: str) -> str:
    """
    Process a user message through the LangChain pipeline.
    
    Args:
        message: The user message
        connection_id: The connection ID for the WebSocket client
        apigw_client: The API Gateway Management client
        type_of_chat: The type of chat (program or chat)
        language: Optional language for code generation
    
    Returns:
        str: The AI response
    """
    start_time = time.time()
    
    # Get the appropriate chain based on whether it's a code generation request
    chain = create_chain(connection_id, language, type_of_chat)
    
    # Process the message and get the response
    try:
        # Debug counters
        chunk_counter = 0
        total_bytes_sent = 0
        full_response = ""
        # Stream each chunk to the client
        async for chunk in get_ai_response(message, chain, connection_id):
            chunk_counter += 1
            chunk_size = len(chunk.encode('utf-8'))  # Get byte size
            total_bytes_sent += chunk_size
            full_response += chunk
            
            # Log chunk info for debugging
            logger.info(f"Sending chunk #{chunk_counter}, size: {chunk_size} bytes, total sent: {total_bytes_sent} bytes")
        
            # Send the individual chunk to the client
            await send_to_connection(apigw_client, connection_id, chunk, "stream")
        
        logger.info(f"Last 200 chars of response: {full_response[-200:]}")
        await send_to_connection(apigw_client, connection_id, "", "done")
        
        end_time = time.time()
        logger.info(f"Message processing completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Sent {chunk_counter} chunks, total {total_bytes_sent} bytes")
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await send_to_connection(apigw_client, connection_id, f"Error processing message: {str(e)}", "error")


def handle_connect(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $connect route
    
    Args:
        event: The WebSocket event
        context: The Lambda context
    
    Returns:
        Dict: The response to be returned to API Gateway
    """
    connection_id = event["requestContext"]["connectionId"]
    logger.info(f"New WebSocket connection: {connection_id}")
    try:
        connections_table.put_item(
            Item={
                "ConnectionId": connection_id,
                "ConnectedAt": int(time.time())
            }
        )
        return {"statusCode": 200, "body": "Connected"}
    except Exception as e:
        logger.error(f"Error connecting client: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

def handle_disconnect(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $disconnect route
    
    Args:
        event: The WebSocket event
        context: The Lambda context
    
    Returns:
        Dict: The response to be returned to API Gateway
    """
    connection_id = event["requestContext"]["connectionId"]
    logger.info(f"Disconnecting WebSocket connection: {connection_id}")
    try:
        connections_table.delete_item(
            Key={"ConnectionId": connection_id}
        )
        return {"statusCode": 200, "body": "Disconnected"}
    except Exception as e:
        logger.error(f"Error disconnecting client: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}


def handle_message(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket messages.
    
    Args:
        event: The WebSocket event
        context: The Lambda context
        

    Returns:
        Dict: The response to be returned to API Gateway

    """

    connection_id = event["requestContext"]["connectionId"]
    logger.info(f"Message from connection: {connection_id}")

    try:
        body = json.loads(event.get("body", "{}"))
        message = body.get("message")
        language = body.get("language")
        type_of_chat = body.get("type")
        if not message:
            logger.warning
            return {"statusCode": 400, "body": "Missing message in request body"}
        
        apigw_client = get_api_gateway_management_client(event)

        asyncio.run(process_message(message, connection_id, apigw_client, type_of_chat, language))
        return {"statusCode": 200, "body": "Message processed"}
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {str(e)}")
        return {"statusCode": 400, "body": f"Error: {str(e)}"}
    
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes WebSocket events to the appropriate handler

    Args:
        event: The Lambda event
        context: The Lambda context

    Returns:
        Dict: The response to be returned to API Gateway
    """

    logger.info(f"Websocket event: {json.dumps(event)}")
    route_key = event.get("requestContext", {}).get("routeKey")

    if route_key == "$connect":
        return handle_connect(event, context)
    elif route_key == "$disconnect":
        return handle_disconnect(event, context)
    elif route_key == "sendMessage":
        return handle_message(event, context)
    else:
        logger.warning(f"Unknown route: {route_key}")
        return {"statusCode": 400, "body": f"Unknown route: {route_key}"}
