from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from requests_aws4auth import AWS4Auth
import boto3
from langchain_aws import BedrockEmbeddings
import os
SERVICE = 'aoss'
PORT = int(os.environ.get('PORT'))
HOST = os.environ.get('HOST')
REGION = os.environ.get('REGION')
INDEX = os.environ.get('INDEX')

CREDENTIALS = boto3.Session().get_credentials()
AWSAUTH = AWS4Auth(
    CREDENTIALS.access_key,
    CREDENTIALS.secret_key,
    REGION,
    SERVICE,
    session_token=CREDENTIALS.token
)

AWSAUTH2 = AWSV4SignerAuth(
    credentials=CREDENTIALS,
    region=REGION,
    service=SERVICE,
)
client = OpenSearch(
    hosts=[{'host': HOST, 'port': PORT}],
    http_auth=AWSAUTH2,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300,
)

def upsert_documents(documents, index=INDEX, client=client):
    """
    
    Upserting the documents into the OpenSearch index

    Args:
        documents (list): The list of documents to upsert
        index (str): The index to upsert the documents to
        client (OpenSearch): The OpenSearch client
    
    """
    # Total update of the index
    if client.indices.exists(index=INDEX):
        print(f"Deleting existing index: {INDEX}")
        client.indices.delete(index=INDEX)
        print(f"Index {INDEX} deleted successfully.")

    index_mapping = {
        "mappings": {
            "properties": {
                "page_content": {
                    "type": "text"
                },
                "metadata": {
                    "type": "object"
                },
                "content": {  # Add this field explicitly since you're using it in the document
                    "type": "text"
                },
                "vector_field": {
                    "type": "knn_vector",
                    "dimension": 1024,
                    "method": {  # Add explicit method configuration
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 128,
                            "m": 16
                        }
                    }
                }
            }
        },
        "settings": {
            "index": {
                "knn": "true",  # Enable KNN explicitly
                "knn.algo_param.ef_search": 100,
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
    }
    client.indices.create(index=index, body=index_mapping)
    
    bulk_data = []
    embedding = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", region_name="ca-central-1")
    print("Upserting")
    for doc in documents:
        action = {
            "index": {
                "_index": index,
            }
        }
        document = {
            "text": doc.page_content,
            "metadata": doc.metadata,
            "page_content": doc.page_content,
            "vector_field": embedding.embed_query(doc.page_content)
        }
        bulk_data.append(action)
        bulk_data.append(document)

    if bulk_data:
        response = client.bulk(body=bulk_data)
        failures = response.get('errors', False)

        if failures:
            print(f"Bulk indexing had errors: {response}")
        else:
            print(f"Successfully indexed {len(documents)} documents")

        return response
    print("No documents to index")
    return None
