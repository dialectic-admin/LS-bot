import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

class S3TimestampManager:
    def __init__(self, region_name='ca-central-1', aws_access_key=None, aws_secret_access_key=None):
        """
        
        Intializing S3 client with optional credentials

        Args:
            region_name (str): AWS region name
            aws_access_key (str): AWS access key
            aws_secret_access_key (str): AWS secret access key
        """

        self.s3 = boto3.client(
            's3',
            region_name=region_name,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_access_key
        )

    def get_json_data(self, bucket, key):
        try:
            print(f"Retrieving JSON data from s3://{bucket}/{key}")
            response = self.s3.get_object(Bucket=bucket, Key=key)

            json_data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"JSON data retrieved successfully")
            return json_data
        except ClientError as e:
            print(f"Error retrieving JSON data: {e}")
            raise

    def get_timestamp(self, bucket, key, timestamp_key = "timestamp"):
        try:
            json_data = self.get_json_data(bucket, key)
            timestamp_value = json_data.get(timestamp_key)

            if timestamp_value is None:
                print(f"Warning: '{timestamp_key}' key not found in the JSON data")
            else:
                print(f"Retrieved timestamp: {timestamp_value}")
            
            return timestamp_value
        
        except Exception as e:
            print(f"Error retrieving timestamp: {e}")  
            raise 

    def update_json_data(self, bucket, key, json_data):
        """
        Updates the JSON file in S3
        
        Args:
            bucket (str): S3 bucket name
            key (str): Object key for the JSON file
            json_data (dict): JSON data to update
        
        Returns:
            dict: Response from S3 put
        """
        try:
            # Convert dictionary to JSON string
            data_json = json.dumps(json_data, indent=2)
            
            print(f"Updating JSON at s3://{bucket}/{key}")
            response = self.s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=data_json,
                ContentType='application/json'
            )
            print('JSON updated successfully')
            return response
        except ClientError as e:
            print(f"Error updating JSON: {e}")
            raise
    
    def update_timestamp_key(self, bucket, key, timestamp_key='timestamp'):
        """
        Updates only the timestamp key in a JSON file with the current time
        
        Args:
            bucket (str): S3 bucket name
            key (str): Object key for the JSON file
            timestamp_key (str): Key to update with the current time
        
        Returns
        """
        try:
            # Get the existing data first
            json_data = self.get_json_data(bucket, key)
            
            # Update the timestamp key with current time
            current_time = datetime.now().isoformat()
            json_data[timestamp_key] = current_time
            print(f"Updated '{timestamp_key}' to: {current_time}")
            
            # Save the updated data
            return self.update_json_data(bucket, key, json_data)
        except ClientError as e:
            print(f"Error updating timestamp key: {e}")
            raise
