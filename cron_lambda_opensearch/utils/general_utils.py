from utils.count_options import count_options

def create_id(original_title: str, language: str) -> str:
    """
    Creating an ID for the document based on the original title in both languages

    1. Stripping whitespaces
    2. Converting to lowercase
    3. Replacing spaces with underscores
    4. Appending language code


    Args:
        original_title (str): The original title of the document
        language (str): The language of the document
    
    Returns:
        str: The ID for the document
    """

    return original_title.strip().lower().replace(" ", "_") + f"_{language}"


def replace_null(item):
    return item if item else ""

def sanitize_metadata(metadata_dict: dict, language: str) -> dict:
    """
    Convert Go Deeper Links to string representation.
    
    Args:
        metadata_dict (dict): Metadata dictionary
        language (str): Language of the metadata, either 'en' or 'fr'

    Returns:
        dict: Sanitized metadata dictionary with new language key and ID
    """
    
    if 'deeper_urls' in metadata_dict and isinstance(metadata_dict['deeper_urls'], list):
        metadata_dict['deeper_urls'] = str(metadata_dict['deeper_urls'])
    
    metadata_dict['language'] = language
    metadata_dict['id'] = create_id(metadata_dict['title'], language)
    return metadata_dict

def format_course_name(course_name):
    """
    
    Process a course name by replacing dashes with spaces and capitalizing the first letter of each word.

    Args:
        course_name (str): The course name to process

    Returns:
        str: The processed course name
    """

    words = course_name.replace('-', ' ').split()
    capitalized_words = []
    for word in words:
        if word and word[0].isalpha():
            capitalized_words.append(word[0].upper() + word[1:])
        else:
            capitalized_words.append(word)
    return ' '.join(capitalized_words)

def create_english_program_info(english_data, last_modified) -> dict:
    """
    Create a dictionary of English program information

    Args:
        english_data (dict): The English data dictionary

    Returns:
        dict: The English program information dictionary
    """

    text = english_data.get('pdf_content', "")
    if text == "":
        options = "No options due to missing PDF content"
    else:
        options = count_options(text)

    return {
        'summary': english_data.get('topic'),
        'snippet_url': english_data.get('snippet_url'),
        'deeper_urls': english_data.get('deeper_urls', 'None'),
        'options': str(options),
        'modified': last_modified
    }

def create_french_program_info(french_data, last_modified) -> dict:
    """
    Create a dictionary of French program information

    Args:
        french_data (dict): The French data dictionary

    Returns:
        dict: The French program information dictionary
    """
    text = french_data.get('pdf_content', "")
    if text == "":
        options = "No options due to missing PDF content"
    else:
        options = count_options(text)

    return {
        'summary': french_data.get('topic'),
        'snippet_url': french_data.get('snippet_url'),
        'deeper_urls': french_data.get('deeper_urls', 'None'),
        'options': str(options),
        'modified': last_modified
    }