"""
Helper utilities for the Dr. Snow Paws application.
"""

def format_response(message, status="success"):
    """
    Format a standard response object.
    
    Args:
        message (str): The message to include in the response
        status (str): The status of the response (success, error, etc.)
        
    Returns:
        dict: A formatted response dictionary
    """
    return {
        "status": status,
        "message": message
    }

def sanitize_input(text):
    """
    Sanitize user input to prevent any potential issues.
    
    Args:
        text (str): The input text to sanitize
        
    Returns:
        str: The sanitized text
    """
    if not text:
        return ""
    
    # Basic sanitization - remove any potentially problematic characters
    sanitized = text.strip()
    return sanitized 