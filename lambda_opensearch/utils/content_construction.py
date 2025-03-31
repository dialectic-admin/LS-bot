"""
Purpose: Simple utility functions to construct the content for vector embedding
Created for: Dialectic
Created by: Andrew Mark Dale - Research Associate
"""

import logging
from langchain.schema import Document
import datetime
import math
from utils.general_utils import format_course_name
logger = logging.getLogger(__name__)
# English versions of the functions
def format_deeper_links_en(deeper_links: list) -> str:
    """
    
    Function to format the deeper links for embedding. The deeper links is returned as an object, here we are processing them into a usable format

    Args:
        deeper_links: The deeper links object
    
    Returns:
        str: The formatted deeper links
    
    """
    resources = ""
    for link in deeper_links:
        resources += f"""
        Title: {link['link_title_en']} - Contributor: {link['contributor_owner_en']}
        URL: {link['link_url_en']}\n\n"""
    return resources


def construct_content_for_embedding_en(data: dict, course: str) -> str:
    logger.info(f"Constructing content for embedding for {data['title']}")
    return f"""TITLE: {data['title']}
    SUBJECT: 
    {data['email_subject']}
    TOPIC: 
    {data['topic']}
    COURSE:
    {format_course_name(course)}
    
    CONTENT: 
    {data['pdf_content']}
    
    RESOURCES: 
    {format_deeper_links_en(data['deeper_urls'])}

    LINKS:
    URL: {data['snippet_url']}
    PDF: {data['pdf_url']}""" 


# French versions of the functions
def format_deeper_links_fr(deeper_links: list) -> str:
    resources = ""
    for link in deeper_links:
        resources += f"""
        Title: {link['link_title_fr']} - Contributor: {link['contributor_owner_fr']}
        URL: {link['link_url_fr']}\n\n"""
    return resources

def construct_content_for_embedding_fr(data: dict, course: str) -> str:
    logger.info(f"Constructing content for embedding for {data['title']}")
    return f"""TITLE: {data['title']}
    SUBJECT: 
    {data['email_subject']}
    TOPIC: 
    {data['topic']}
    COURSE:
    {format_course_name(course)}
    
    CONTENT: 
    {data['pdf_content']}
    
    RESOURCES: 
    {format_deeper_links_fr(data['deeper_urls'])}

    LINKS:
    URL: {data['snippet_url']}
    PDF: {data['pdf_url']}""" 

def create_content_for_programs(programs: set) -> str:
    programs_str = "All Snippet Programs:\n"
    for program in programs:
        programs_str += f"{program}\n"
    return programs_str

def create_content_for_specific_course(programs: dict, language: str) -> list[Document]:
    """
    Function to create content for a specific program
    Args:
    programs: The programs dictionary
    language: The language of the content, e.g., 'en' or 'fr'
    Returns:
    list[Document]: A list of Document objects
    """
    content = []
    
    for program_name, program_data in programs.items():
        # Skip if program_data is not a dictionary
        if not isinstance(program_data, dict):
            print(f"Warning: Skipping non-dictionary program '{program_name}'")
            continue
            
        this_program = f"All Snippets for Program: {program_name}"
        min_datetime = None  # Initialize as None instead of infinity
        
        # Process titles and data for this program
        for i, (title, snippet_data) in enumerate(program_data.items()):
            # Skip if snippet_data is not a dictionary
            if not isinstance(snippet_data, dict):
                print(f"Warning: Skipping non-dictionary entry '{title}' in program '{program_name}'")
                continue
                
            # Process modified date
            modified = snippet_data.get('modified')
            if modified:
                try:
                    # Convert string date to datetime object
                    if isinstance(modified, str):
                        # Handle ISO format dates (YYYY-MM-DDTHH:MM:SS)
                        modified_date = datetime.datetime.fromisoformat(modified.replace('Z', '+00:00'))
                    elif isinstance(modified, (int, float)):
                        # Handle timestamp
                        modified_date = datetime.datetime.fromtimestamp(modified)
                    elif isinstance(modified, datetime.datetime):
                        # Already a datetime object
                        modified_date = modified
                    else:
                        print(f"Warning: Unknown date format for '{title}': {modified}")
                        modified_date = None
                        
                    # Update min_datetime if this date is earlier or if min_datetime is not set yet
                    if modified_date and (min_datetime is None or modified_date < min_datetime):
                        min_datetime = modified_date
                        
                except Exception as e:
                    print(f"Error processing date for '{title}': {e}")
            
            # Process deeper URLs
            urls = snippet_data.get('deeper_urls', 'None')
            go_deeper = 'None'
            
            if urls != 'None':
                if language == 'fr':
                    go_deeper = format_deeper_links_fr(urls)
                elif language == 'en':
                    go_deeper = format_deeper_links_en(urls)
            
            # Get content fields safely
            summary = snippet_data.get('summary', 'No summary available')
            snippet_url = snippet_data.get('snippet_url', 'No URL available')
            options = snippet_data.get('options')
            
            # Add to content string
            this_program += f"\n\n Title: {title} \n Topic: {summary} \n Snippet URL: {snippet_url} \n Order: {i + 1} Go Deeper URLs: {go_deeper} \n Number of options for snippet: {options} \n"
        
        # Use a default value if no valid dates were found
        if min_datetime is None:
            last_modified = "No date available"
        else:
            # You can format the date however you need
            last_modified = min_datetime.isoformat()
        
        # Create the document
        if language == 'en':
            content.append(Document(
                page_content=this_program,
                metadata={
                    "program": program_name,
                    "id": f"all_programs_{program_name}_en",
                    "last_modified": last_modified,
                    "language": "en"
                }
            ))
        elif language == 'fr':
            content.append(Document(
                page_content=this_program,
                metadata={
                    "program": program_name,
                    "id": f"all_programs_{program_name}_fr",
                    "last_modified": last_modified,
                    "language": "fr"
                }
            ))
    
    return content

def create_overall_snippet_courses_en(courses: dict) -> Document:
    content = "Information for all courses: "

    for k, v in courses.items():   
        if k != 'modified':
            content += f"\nCourse: {k}\n Number of snippets: {v}\n"
    return Document(page_content=content, metadata={"id": "all_courses_en", "language": "en", "last_modified": courses['modified']})

def create_overall_snippet_courses_fr(courses: dict) -> Document:
    content = "Information for all courses: "

    for k, v in courses.items():   
        if k != 'modified':
            content += f"\nCourse: {k}\n Number of snippets: {v}\n"
    return Document(page_content=content, metadata={"id": "all_courses_fr", "language": "fr", "last_modified": courses['modified']})
