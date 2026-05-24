"""
Input compatibility layer for XTAgent web endpoints.

Problem: Five interaction endpoints each expect different JSON field names.
A user who guesses wrong gets a crash instead of a response.

Solution: One normalizer that accepts any reasonable field name.
Any of: query, question, message, text, q, input → works everywhere.
"""


def extract_user_input(data: dict, fallback: str = '') -> str:
    """Extract user input from request data, regardless of field name used.
    
    Checks fields in priority order:
      query, question, message, text, q, input, prompt
    
    Returns the first non-empty string found, or fallback.
    """
    if not isinstance(data, dict):
        return fallback
    
    field_names = ['query', 'question', 'message', 'text', 'q', 'input', 'prompt']
    
    for field in field_names:
        value = data.get(field)
        if value and isinstance(value, str) and value.strip():
            return value.strip()
    
    return fallback