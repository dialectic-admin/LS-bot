from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from requests_aws4auth import AWS4Auth
import boto3
import uuid
from langchain_aws import BedrockEmbeddings
from utils.S3TimeStampManager import S3TimestampManager
import os
REGION = os.environ.get('REGION')
SERVICE = 'aoss'
HOST = os.environ.get('HOST')
PORT = int(os.environ.get('PORT'))
INDEX = os.environ.get('INDEX')
CREDENTIALS = boto3.Session().get_credentials()
AWSAUTH = AWSV4SignerAuth(
    credentials=CREDENTIALS,
    region=REGION,
    service=SERVICE,
)

BUCKET = os.environ.get('BUCKET')
KEY = os.environ.get('KEY')

client = OpenSearch(
    hosts=[{'host': HOST, 'port': PORT}],
    http_auth=AWSAUTH,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

def update_documents(documents, index=INDEX, client=client):
    """
    
    Upserting the documents into the OpenSearch index

    Args:
        documents (list): The list of documents to upsert
        index (str): The index to upsert the documents to
        client (OpenSearch): The OpenSearch client
    
    """
    timemanager = S3TimestampManager()
    last_update = timemanager.get_timestamp(BUCKET, KEY)

    # If it doesn't exist, create the index
    if not client.indices.exists(index=INDEX):
        raise Exception(f"Index {INDEX} does not exist, create the index prior to updating documents")
    
    docs_to_update = []
    metadata_ids_to_delete = set()
    embedding = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", region_name="ca-central-1")
    print(f"Checking {len(documents)} documents for updates")
    for doc in documents:
        if doc.metadata['last_modified'] > last_update:
            docs_to_update.append(doc)

            if 'id' in doc.metadata:
                metadata_ids_to_delete.add(doc.metadata['id'])

    if metadata_ids_to_delete:
        print(f"Deleting {len(metadata_ids_to_delete)} outdated documents")
        for metadata_id in metadata_ids_to_delete:
            delete_response = client.delete_by_query(
                index=index,
                body={
                    "query": {
                        "term": {
                            "metadata.id": metadata_id
                        }
                    }
                },
                refresh=True
            )
            if delete_response.get('failures') or delete_response.get('deleted', 0) == 0:
                print(f"Warning: Issue deleting document with metadata.id={metadata_id}: {delete_response}")
    bulk_data = []
    embedding = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", region_name="ca-central-1")
    
    for doc in docs_to_update:
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
        timemanager.update_timestamp_key(BUCKET, KEY)
        response = client.bulk(body=bulk_data)
        failures = response.get('errors', False)
        if failures:
            print(f"Bulk indexing had errors: {response}")
        else:
            print(f"Successfully indexed {len(docs_to_update)} documents")
        return response
    
    timemanager.update_timestamp_key(BUCKET, KEY)
    print("No documents to index")
    return None
