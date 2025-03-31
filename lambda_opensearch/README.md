# Learning Snippets Vector Indexing System (Full Reindex Version)

A system for processing, embedding, and indexing educational content in OpenSearch to power the vector search capabilities of the Learning Snippet Assistant Bot. This variant implements a full reindex strategy rather than incremental updates.

## System Overview

This subsystem is responsible for:
1. Processing snippet data from DynamoDB
2. Creating structured document objects
3. Generating vector embeddings
4. Completely recreating the OpenSearch index with fresh data

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

Handles complete index recreation and document indexing in OpenSearch:

- `upsert_documents`: **Key difference** - Completely recreates the index rather than updating individual documents
- Creates index mapping with KNN vector search configuration
- Generates vector embeddings using Amazon Bedrock
- Handles bulk indexing operations

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
- Triggers complete reindexing of OpenSearch
- Handles error cases and returns appropriate responses

## Data Flow

1. The Lambda function is triggered
2. The function scans DynamoDB to retrieve all snippet data
3. Raw snippet data is parsed into Document objects with proper metadata
4. The existing OpenSearch index is completely deleted
5. A new index with proper mappings is created
6. Vector embeddings are generated for all documents
7. All documents are indexed in OpenSearch in a bulk operation

## Key Differences from Incremental Version

This version of the system differs in several important ways:

1. **Full Reindex Strategy**: Rather than updating only changed documents, this version completely recreates the index
2. **No Timestamp Tracking**: Since all documents are reindexed, there's no S3-based timestamp management
3. **Index Configuration**: Explicit index configuration is included with the KNN vector search settings
4. **Simplified Process**: No need to check for modified documents or handle deletions separately

## Environment Configuration

The system relies on several environment variables:
- `REGION`: AWS region
- `HOST`: OpenSearch endpoint
- `PORT`: OpenSearch port
- `INDEX`: OpenSearch index name
- `SnippetsTable`: DynamoDB table containing snippet data
- `TABLE_NAME`: Alternative for DynamoDB table name
- `dialectic-vector-db`: OpenSearch collection identifier

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

## Vector Search Configuration

This version includes explicit configuration for vector search:
- Uses HNSW (Hierarchical Navigable Small World) algorithm
- Configured with L2 distance metric
- Uses NMSLib as the engine
- Sets specific parameters for search efficiency:
  - `ef_construction`: 128
  - `m`: 16
  - `ef_search`: 100

## Error Handling

The system includes comprehensive error handling:
- Graceful handling of missing content
- Detailed logging
- Document-level exception handling to prevent batch failures
- Appropriate HTTP status codes for different error scenarios

## When to Use This Version

This full reindex approach is most appropriate when:
1. The total dataset size is manageable
2. Data consistency is critical
3. Incremental updates might leave stale data
4. Index configuration needs to be updated
5. The system can tolerate brief downtime during reindexing
