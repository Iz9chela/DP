import openai
import json
from typing import Dict, Any
from prompt_evaluator_module import evaluate_user_prompt


def load_api_key(filename: str) -> str:
    try:
        with open(filename, "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error: Could not read API key file. {e}")
        exit(1)


openai_api_key = load_api_key("../openai_key.txt")
client = openai.OpenAI(api_key=openai_api_key)


class AutomatedRefinementModule:
    """
    A class that uses the output of the prompt_evaluator_module
    to automatically refine and decompose complex user prompts.

    Key capabilities:
    1. Assess feasibility (0 to 10).
    2. Generate clarifying questions if needed.
    3. Resolve conflicts (if style, constraints, etc. are contradictory).
    4. Produce a refined version of the user prompt that addresses the evaluator’s feedback.
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name

    def assess_feasibility(self, user_prompt: str, evaluation_output: dict) -> Dict[str, Any]:
        """
        Performs a feasibility check (0 to 10) to see if the request is solvable 
        given the context, constraints, and the evaluator’s findings.

        Returns a dict:
        {
          "feasibility_score": int,  # 0 to 10
          "feasibility_explanation": str
        }
        """

        # Build a system message summarizing relevant evaluator data
        system_prompt = f"""
        You are a feasibility assessor. Read the user's prompt and the evaluator's findings, 
        then decide if the user prompt is fully solvable (score=10) or unsolvable (score=0), 
        or somewhere in-between.

        User Prompt: {user_prompt}

        Evaluator's Findings:
        clarity_rating = {evaluation_output["evaluation"].get("clarity_rating", "N/A")}
        difficulty = {evaluation_output["evaluation"].get("difficulty", "N/A")}
        reasons = {evaluation_output["evaluation"].get("reasons", [])}
        conflicts = {evaluation_output["evaluation"].get("conflicts", {})}
        coherence_assessment = {evaluation_output["evaluation"].get("coherence_assessment", "")}

        Rules:
        1. Return a JSON with exactly two fields: 'feasibility_score' (int) and 'feasibility_explanation' (string).
        2. feasibility_score ranges from 0 to 10.
        3. feasibility_explanation EXACTLY 1-3 sentences justifying your score.

        Return ONLY valid JSON. No extra text.
        """

        response = openai.ChatCompletion.create(
            model=self.model_name,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt}
            ]
        )

        content = response.choices[0].message.content.strip()

        # Attempt to parse the JSON output from the LLM
        try:
            feasibility_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if the LLM fails to produce valid JSON
            feasibility_data = {
                "feasibility_score": 5,
                "feasibility_explanation": (
                    "Could not parse LLM output. Defaulting feasibility_score=5."
                )
            }

        return feasibility_data

    def refine_prompt(
            self,
            user_prompt: str,
            evaluation_output: dict,
            feasibility_data: dict,
            interactive: bool = False
    ) -> Dict[str, Any]:
        """
        Refines the user prompt based on:
        - The evaluator's output (clarity, difficulty, reasons, conflicts, etc.)
        - The feasibility assessment

        If 'interactive' is True, it can prompt the user for clarifications.

        Returns a dict with:
        {
          "feasibility_score": int,
          "feasibility_explanation": str,
          "refined_prompt": str,
          "clarifying_questions": [array of questions],
          "style_decision": string
        }
        """

        # Extract data from the evaluator's output
        clarity = evaluation_output["evaluation"].get("clarity_rating", 5)
        difficulty = evaluation_output["evaluation"].get("difficulty", "Easy")
        conflicts = evaluation_output["evaluation"].get("conflicts", {})
        reasons = evaluation_output["evaluation"].get("reasons", [])
        coherence = evaluation_output["evaluation"].get("coherence_assessment", "")

        # Feasibility from the LLM
        feasibility_score = feasibility_data.get("feasibility_score", 5)
        feasibility_explanation = feasibility_data.get("feasibility_explanation", "")

        # Build a system message to refine the prompt
        system_refinement_prompt = f"""
        You are an Automated Refinement Agent.

        --- USER PROMPT ---
        {user_prompt}

        --- EVALUATOR OUTPUT ---
        Clarity: {clarity}/10
        Difficulty: {difficulty}
        Reasons: {reasons}
        Conflicts: {conflicts}
        Coherence: {coherence}

        --- FEASIBILITY ---
        Score: {feasibility_score}/10
        Explanation: {feasibility_explanation}

        --- TASK ---
        1. If feasibility_score < 4, the task might be missing info or is very difficult. 
           Suggest ways to fill in missing info or reduce complexity.
        2. If conflicts.flag == true, propose how to resolve the conflicting instructions 
           (e.g. unify style, relax constraints, etc.).
        3. Suggest up to 3 clarifying questions if more info is needed from the user.
        4. Propose a refined prompt that addresses the evaluator’s concerns:
           - Resolve conflicting instructions
           - Add missing details or clarifications if possible
           - Keep it coherent
           - Possibly override style or constraints to make it feasible

        Output a valid JSON with exactly these fields:
        {{
          "refined_prompt": string,
          "clarifying_questions": [array of strings],
          "style_decision": string  # e.g. "Adopted a formal style" or "Kept user’s requested informal style"
        }}

        Return ONLY valid JSON.
        """

        # Call the LLM to get the refinement suggestions
        response = openai.ChatCompletion.create(
            model=self.model_name,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_refinement_prompt}
            ]
        )

        content = response.choices[0].message.content.strip()

        # Attempt to parse as JSON
        try:
            refinement_data = json.loads(content)
        except json.JSONDecodeError:
            refinement_data = {
                "refined_prompt": user_prompt,
                "clarifying_questions": [],
                "style_decision": "No changes - parse error in LLM output"
            }

        # If interactive mode, ask the user for clarifications
        clarifying_qs = refinement_data.get("clarifying_questions", [])
        if interactive and clarifying_qs:
            user_answers = {}
            print("The system suggests the following clarifications:\n")
            for q in clarifying_qs:
                print(f"- {q}")
                ans = input("Your answer: ")
                user_answers[q] = ans

            # In a real system, you might do another LLM call to incorporate user answers
            # and finalize the refined prompt. Here, we'll just note them.

        result = {
            "feasibility_score": feasibility_score,
            "feasibility_explanation": feasibility_explanation,
            "refined_prompt": refinement_data.get("refined_prompt", user_prompt),
            "clarifying_questions": clarifying_qs,
            "style_decision": refinement_data.get("style_decision", "No style decision found"),
        }
        return result


def run_automated_refinement(user_prompt: str, interactive: bool = False) -> Dict[str, Any]:
    """
    High-level convenience function that:
    1) Calls evaluate_user_prompt from prompt_evaluator
    2) Assesses feasibility
    3) Refines the prompt
    4) Returns a final dictionary with refinement info
    """

    # 1) Evaluate
    evaluation_output = evaluate_user_prompt(user_prompt)

    # 2) Create an instance of AutomatedRefinementModule
    arm = AutomatedRefinementModule(model_name="gpt-3.5-turbo")

    # 3) Assess Feasibility
    feasibility_data = arm.assess_feasibility(user_prompt, evaluation_output)

    # 4) Refine
    refinement_result = arm.refine_prompt(
        user_prompt=user_prompt,
        evaluation_output=evaluation_output,
        feasibility_data=feasibility_data,
        interactive=interactive
    )

    return refinement_result


if __name__ == "__main__":
    """
    Example usage:
    1) The user enters a prompt.
    2) We run the automated refinement pipeline.
    3) Print out results.
    """

    sample_prompt = input("Enter the prompt to refine: ")

    result = run_automated_refinement(sample_prompt, interactive=False)

    print("\n=== AUTOMATED REFINEMENT RESULT ===")
    print(json.dumps(result, indent=2))
