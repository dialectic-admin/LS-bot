# Dialectic Vector Indexing System

A system for processing, embedding, and indexing educational content in OpenSearch to power the vector search capabilities of the Dialectic Snippet Bot.

## System Overview

This subsystem is responsible for:
1. Processing snippet data from DynamoDB
2. Creating structured document objects
3. Generating vector embeddings
4. Indexing content in OpenSearch
5. Managing document timestamps for incremental updates

The system supports bilingual content (English and French) and maintains metadata about courses, programs, and resources.

## Core Components

### Content Construction (`content_construction.py`)

Utility functions for constructing content for vector embedding:

- `format_deeper_links_en/fr`: Formats external resource links in English/French
- `construct_content_for_embedding_en/fr`: Creates structured content for embedding in English/French
- `create_content_for_programs`: Creates a summary of all available programs
- `create_content_for_specific_course`: Creates detailed content for a specific course
- `create_overall_snippet_courses_en/fr`: Generates a summary of all courses with snippet counts

### Document Parsing (`parse_to_document_objects.py`)

Transforms raw metadata into structured document objects for indexing:

- `parse_to_document_objects`: Converts snippet metadata into LangChain Document objects
- Maintains program/course information for both languages
- Handles missing content gracefully with appropriate logging
- Creates special document objects for course and program summaries

### OpenSearch Interface (`opensearch.py`)

Handles document indexing and updates in OpenSearch:

- `update_documents`: Upserts documents into OpenSearch
- Handles document deletion for outdated content
- Generates vector embeddings using Amazon Bedrock
- Handles bulk indexing operations

### S3 Timestamp Management (`S3TimeStampManager.py`)

Manages incremental update tracking:

- `get_timestamp`: Retrieves the last update timestamp from S3
- `update_timestamp_key`: Updates the timestamp after successful indexing
- `get_json_data`: Helper for JSON data retrieval from S3
- `update_json_data`: Helper for updating JSON data in S3

### Utility Functions (`general_utils.py`)

Various helper functions for processing data:

- `create_id`: Generates a unique ID for each document
- `sanitize_metadata`: Prepares metadata for indexing
- `format_course_name`: Standardizes course name formatting
- `create_english/french_program_info`: Creates program information with proper metadata

### Option Counting (`count_options.py`)

Utility for extracting options from content:

- `count_options`: Extracts and counts options in content using regex pattern matching

### Lambda Handler (`lambda_function.py`)

Main entry point for the AWS Lambda function:

- Scans DynamoDB for all snippets
- Calls document parsing functions
- Updates OpenSearch with new documents
- Handles error cases and returns appropriate responses

## Data Flow

1. The Lambda function is triggered (likely on a schedule or by content updates)
2. The function scans DynamoDB to retrieve all snippet data
3. Raw snippet data is parsed into Document objects with proper metadata
4. System checks which documents are new or updated since the last run
5. Outdated documents are deleted from OpenSearch
6. New vector embeddings are generated for updated documents
7. Updated documents are indexed in OpenSearch
8. The timestamp is updated in S3 to track the latest successful update

## Environment Configuration

The system relies on several environment variables:
- `REGION`: AWS region
- `HOST`: OpenSearch endpoint
- `PORT`: OpenSearch port
- `INDEX`: OpenSearch index name
- `BUCKET`: S3 bucket for timestamp storage
- `KEY`: S3 key for timestamp file
- `SnippetsTable`: DynamoDB table containing snippet data
- `TABLE_NAME`: Alternative for DynamoDB table name

## Bilingual Support

The system supports both English and French content:
- Separate document objects for each language
- Language-specific metadata
- Dedicated formatting functions for each language
- Language tagging for proper retrieval filtering

## Document Structure

Each snippet document includes:
- Title
- Subject
- Topic
- Course information
- Content (from PDF)
- External resources (deeper links)
- URLs for original content
- Language identifier
- Last modified timestamp
- Unique ID

## Special Document Types

Beyond individual snippets, the system also creates:
1. **Program Summary Documents**: List all snippets for a specific program
2. **Course Overview Documents**: Provide information about all available courses
3. **Option Information**: Track different options/variations within snippets

## Incremental Updates

The system implements an efficient incremental update strategy:
1. Tracks last update timestamp in S3
2. Only processes documents that have changed since last update
3. Deletes outdated documents before indexing new versions
4. Updates timestamp after successful processing

## Error Handling

The system includes comprehensive error handling:
- Graceful handling of missing content
- Detailed logging
- Document-level exception handling to prevent batch failures
- Appropriate HTTP status codes for different error scenarios