import json
import openai
import re

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

class PromptDecomposer:
    def __init__(self, prompt: str, model: str, automated: bool):
        self.prompt = prompt
        self.model = model
        self.automated = automated
        self.result = None  # Store final result

    def _call_ai(self, system_prompt: str, user_prompt: str):
        """Interacts with the AI model to generate responses."""
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    def decompose_automatic(self) -> dict:
        system_prompt = """
            You are a prompt Decomposition assistant with extensive experience.
            Your task is to break down the user's request into clear, granular, and actionable subtasks.

            Return a JSON object that strictly with this schema:
            {
                "prompt": string,
                "subtasks": [array of strings]
            }

            Follow these instructions:
            1. Carefully examine the request to understand its full scope and requirements.
            2. Decompose the complex task into a MAXIMUM of 5 clear and actionable subtasks.
            3. Ensure each decomposed prompt is clear and focused.
            4. Organize decomposed prompts in a coherent sequence.

            Throughout this process, maintain a helpful and patient demeanor.
            Return only valid JSON with no extra commentary.
            """
        user_prompt = f"Decompose the following task: {self.prompt}"
        response_content = self._call_ai(system_prompt, user_prompt)
        self.result = extract_json_from_response(response_content)
        return self.result

    def decompose_interactively(self) -> dict:
        system_prompt = """
               You are an interactive prompt decomposition assistant with extensive experience.
               Your task is to break down the user's request into clear, granular, and actionable subtasks,
               and to engage the user interactively to clarify any ambiguities.

               Follow these instructions:
               1. Carefully examine the user's request to understand its full scope and requirements.
               2. Identify any ambiguous or unclear aspects of the request and ask the user for clarification if needed.
               3. Decompose the request into a maximum of 5 clear and actionable subtasks.
               4. Organize the subtasks in a coherent sequence.
               5. Return a JSON object with the following schema:

               {
                  "prompt": string,
                  "subtasks": [array of strings]
               }

               Maintain a helpful and patient demeanor and encourage interactive dialogue for further refinement.
               In your final answer, output only valid JSON with no extra commentary.
               """
        # Phase 1: Initial attempt at decomposition.
        initial_prompt = f"Decompose the following task: {self.prompt}"
        initial_response = self._call_ai(system_prompt, initial_prompt)
        json_result = extract_json_from_response(initial_response)

        if "error" not in json_result:
            self.result = json_result
            return self.result
        else:
            # The model likely asked clarifying questions (1-5 questions).
            print("The model has asked the following clarifying questions:")
            print(initial_response)
            clarifications = input("Please answer the above questions to clarify the task:\n")

            # Phase 2: Request the final answer in JSON format using both the original request and clarifications.
            final_prompt = (
                f"Based on the original request: '{self.prompt}'\n"
                f"and the following clarifications: {clarifications}\n"
                "now produce the final JSON decomposition strictly following this schema:\n"
                '{ "prompt": string, "subtasks": [array of strings] }.\n'
                "Your final answer must be valid JSON with no extra commentary."
            )
            final_response = self._call_ai(system_prompt, final_prompt)
            json_result = extract_json_from_response(final_response)
            if "error" in json_result:
                print("Final answer did not produce valid JSON. Raw response:")
                print(final_response)
            self.result = json_result
            return self.result


# Example Usage
if __name__ == "__main__":
    user_input = input("Enter your query: ")

    model = "gpt-4o"  # Replace with the appropriate model name if necessary

    automated_mode = input("Run in automated mode? (yes/no): ").strip().lower() == "yes"

    decomposer = PromptDecomposer(user_input, model, automated=automated_mode)

    if automated_mode:
        final_result = decomposer.decompose_automatic()
    else:
        final_result = decomposer.decompose_interactively()

    print("\nFinal Confirmed Breakdown:")
    print(json.dumps(final_result, indent=4))