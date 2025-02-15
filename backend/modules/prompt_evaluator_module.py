import openai
import json
import re

# Function to read API key from a file
def load_api_key(filename: str) -> str:
    try:
        with open(filename, "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error: Could not read API key file. {e}")
        exit(1)

# Load API key from file
openai_api_key = load_api_key("../openai_key.txt")
client = openai.OpenAI(api_key=openai_api_key)

def extract_json_from_response(content: str) -> str:
    """
    Extracts a JSON string from the given content.

    If the content is wrapped in markdown code fences (e.g., ```json ... ```),
    this function will remove the fences and return the JSON string.

    Args:
        content (str): The raw text output from the LLM.

    Returns:
        str: The extracted JSON string.
    """
    json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
    if json_match:
        return json_match.group(1)
    return content

def parse_prompt_with_llm(prompt: str) -> dict:
    """
    Uses an LLM to parse the user prompt into key elements:
      - goal
      - context
      - instructions
      - constraints
      - style
    If any element is not found, the LLM should return an empty string for that field.
    """

    system_instructions = """
    You are a helper that extracts key elements from a user's prompt and returns a JSON object that strictly with this schema:
    {
      "goal": string,
      "context": string,
      "instructions": string,
      "constraints": string,
      "style": string
    }

    Definitions:
    - "goal": A concise statement of the target outcome.
    - "context": Relevant background or situational details.
    - "instructions": Specific directives for execution.
    - "constraints": Limitations or requirements.
    - "style": The tone or manner in which the content should be expressed.

    Rules:
    1. If a field is not identified in the input, return an empty string for that field.
    2. Include only the specified keys; do not add any additional keys.
    3. Do not include explanations; output only valid JSON.

    Examples:
    Input: "Draft a brief email requesting a meeting to discuss project timelines. The email should be professional and concise. Include project context and mention the deadline constraints."
    Expected Output:
    {
      "goal": "Request a meeting to discuss project timelines",
      "context": "Project context and deadline constraints",
      "instructions": "Draft a brief, professional, and concise email",
      "constraints": "Mention deadline constraints",
      "style": "Professional"
    }
    Input: "Write a Python function that sorts a list of numbers in ascending order.",
    Expected_output: 
    {
      "goal": "Write a Python function to sort a list of numbers",
      "context": "",
      "instructions": "Sort the list in ascending order",
      "constraints": "",
      "style": ""
    }
    """

    # We ask the model to parse the prompt
    response = client.chat.completions.create(
        model="gpt-4o",  # gpt-4o gpt-3.5-turbo
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()

    # Extract the JSON string using our helper function
    json_str = extract_json_from_response(content)

    try:
        extracted = json.loads(json_str)
    except json.JSONDecodeError:
        extracted = {
            "error": "JSON parsing failed",
            "raw_response": content
        }

    return extracted

def validate_prompt_elements(parsed_key_data: dict) -> dict:
    """
    Validates which fields are present/absent.
    Returns a dictionary with boolean flags: has_goal, has_context, has_instructions, etc.
    """
    return {
        "has_goal": bool(parsed_key_data.get("goal", "").strip()),
        "has_context": bool(parsed_key_data.get("context", "").strip()),
        "has_instructions": bool(parsed_key_data.get("instructions", "").strip()),
        "has_constraints": bool(parsed_key_data.get("constraints", "").strip()),
        "has_style": bool(parsed_key_data.get("style", "").strip())
    }

def evaluate_parsed_prompt(parsed_key_data: dict, user_prompt: str) -> dict:
    """
    Given the parsed prompt elements, ask the LLM to:
      - Rate clarity (0-10)
      - Decide difficulty (Easy / Hard)
      - Provide EXACTLY 3-5 reasons
      - Identify conflicts (if any) and list them
      - Provide a short coherence assessment
      - Suggest LLM parameters
    Return a dict with the structure described.
    """

    # Construct a "report" about the extracted data that we feed to the system instruction.
    # We can embed the parsed data in a structured way:
    evaluation_context = f"""
    PROMPT: {user_prompt}
    GOAL: {parsed_key_data.get("goal", "")}
    CONTEXT: {parsed_key_data.get("context", "")}
    INSTRUCTIONS: {parsed_key_data.get("instructions", "")}
    CONSTRAINTS: {parsed_key_data.get("constraints", "")}
    STYLE: {parsed_key_data.get("style", "")}
    """

    # System prompt that *strictly* enforces the JSON schema & 3–5 reasons.
    system_instructions = """
        "You are a Professional Prompt Evaluator with extensive experience. 
        Your task is to analyze a given prompt's key elements (prompt, goal, context, instructions, constraints, style) 
        and output a JSON object strictly adhering to the schema below:\n\n"
        
        {
            "clarity_rating": integer (0 to 10),
            "difficulty": "Easy" or "Hard",
            "reasons": [array of exactly 3 to 5 strings],
            "conflicts": {
                "flag": boolean,
                "items": [array of strings; list conflicting instructions, or an empty array if none]
            },
            "coherence_assessment": string,
            "suggested_parameters": {
                "temperature": float,
                "top_p": float,
                "max_tokens": integer,
                "frequency_penalty": float,
                "presence_penalty": float
            }
        }
        
        Use these factors when forming your 3–5 reasons:
        1. Is the goal explicit or vague?
        2. Is there sufficient background/context?
        3. Are instructions straightforward or contradictory?
        4. Do strict constraints (word limits, references, format) increase complexity?
        5. Are there time/resource constraints?
        6. Is crucial info missing, causing guesswork?
        7. Does everything (goal, context, instructions, constraints, style) fit together?
        8. Does the required output format clash with other instructions?
        
        Then:
        - Assign clarity_rating (0–10).
        - Mark difficulty ("Easy" or "Hard").
        - Provide exactly 3–5 reasons.
        - If there are conflicting instructions, set conflicts.flag=true and list them in conflicts.items; else conflicts.flag=false and conflicts.items=[].
        - Give a short coherence_assessment.
        - Suggest parameter values in suggested_parameters.

        Return only valid JSON with no extra commentary.
    """

    # We pass the "evaluation_context" as user content, so the model sees the actual prompt data.
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.0,  # Keep it deterministic for consistent structure
        messages=[
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": evaluation_context}
        ]
    )

    content = response.choices[0].message.content.strip()

    json_str = extract_json_from_response(content)

    try:
        eval_dict = json.loads(json_str)
    except json.JSONDecodeError:
        eval_dict = {
            "error": "Evaluation JSON parse error",
            "raw_response": content
        }

    return eval_dict

def evaluate_user_prompt(user_prompt: str) -> dict:
    """
    1. Parse the prompt into goal, context, instructions, constraints, style.
    2. Validate which elements are present or absent.
    3. Evaluate the parsed prompt to get clarity rating, difficulty, reasons, conflicts, etc.
    4. Return a final dictionary with all info combined.
    """

    # 1. Parse
    parsed_key_data = parse_prompt_with_llm(user_prompt)

    # 2. Validate
    presence_info = validate_prompt_elements(parsed_key_data)

    # 3. Evaluate
    evaluation = evaluate_parsed_prompt(parsed_key_data, user_prompt)

    # 4. Combine results in a structured way
    final_result = {
        "parsed_key_data": parsed_key_data,         # The extracted fields
        "presence_info": presence_info,     # Which fields are present/absent
        "evaluation": evaluation            # The rating, conflicts, reasons, etc.
    }

    return final_result

if __name__ == "__main__":

    user_input = input("Enter your query: ")

    result = evaluate_user_prompt(user_input)
    print("=== FINAL EVALUATION RESULTS ===")
    print(json.dumps(result, indent=2))

