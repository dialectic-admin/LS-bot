import boto3
from botocore.exceptions import ClientError
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
import os
from dotenv import load_dotenv
from utils.parse_to_document_objects import parse_to_document_objects
from utils.general_utils import sanitize_metadata
from utils.opensearch import update_documents

load_dotenv()
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table_name = os.environ.get('SnippetsTable') or event.get('SnippetsTable') or os.getenv('TABLE_NAME')
    if not table_name:
        return {
            'statusCode': 400,
            'body': json.dumps(
                {
                    'message': 'Table name is required. Please provide it as an environment variable or in the event payload.'
                }
            )
        }
    
    table = dynamodb.Table(table_name)

    try:

        all_items = []
        last_evaluated_key = None

        while True:
            scan_params = {}
            if last_evaluated_key:
                scan_params['ExclusiveStartKey'] = last_evaluated_key

            response = table.scan(**scan_params)
            all_items.extend(response['Items'])
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
        
        documents = parse_to_document_objects(all_items)
        response = update_documents(documents)
        if response == None:
            return {
                'statusCode': 200,
                'body': json.dumps(
                    {
                        'message': 'No documents to update'
                    }
                )
            }
        else: 
            return {
                'statusCode': 200,
                'body': json.dumps(
                    {
                        'message': f'Successfully updated documents'
                    }, default=str
                )
            }
    except ClientError as e:
        print(f"Error scanning DynamoDB table: {e.response['Error']['Message']}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to scan DynamoDB table',
                'error': e.response['Error']['Message']
            })
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to scan DynamoDB table',
                'error': str(e)
            })
        }
    

if __name__ == "__main__":
    val = lambda_handler({}, {})
    print(val)