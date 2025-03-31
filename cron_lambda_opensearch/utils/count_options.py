import re
def count_options(text):
    """
    Extracts option numbers from text and returns the count of unique options.
    Looks for patterns like "OPTION 1", "OPTION 2", etc.
    """
    # Regular expression to match "OPTION" followed by a number
    regex = r"OPTION\s+(\d+)"
    
    # Find all matches and extract the numbers
    matches = re.findall(regex, text, re.IGNORECASE)
    
    # Convert matches to integers
    option_numbers = [int(match) for match in matches]
    
    # Create a set to get unique options
    unique_options = set(option_numbers)
    
    # Return the count of unique options
    return len(unique_options)
