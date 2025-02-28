import re
import json

def extract_json_from_response(content: str) -> dict:
    """
    Extracts a JSON object from the AI response, trying multiple patterns.
    """
    # Try to extract from markdown code block
    json_pattern = r"```(?:json)?\s*(\{[\s\S]*\})\s*```"
    match = re.search(json_pattern, content)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: try to extract content between first '{' and last '}'
        try:
            start = content.index('{')
            end = content.rindex('}')
            json_str = content[start:end+1]
        except ValueError:
            return {"error": "JSON parsing failed", "raw_response": content}
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"error": "JSON parsing failed", "raw_response": content}