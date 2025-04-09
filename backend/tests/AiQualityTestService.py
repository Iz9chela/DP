import asyncio
import time
import logging
import random
from typing import Dict, Any, Optional, List, Union
from tabulate import tabulate

from torch.distributions.constraints import independent

from backend.config.config import load_config
from backend.db.db import get_database
from backend.llm_clients.ai_client_factory import get_ai_client
from backend.llm_clients.clients import AIClient
from backend.modules.automated_refinement_module import AutomatedRefinementModule
from backend.modules.evaluator_module import Evaluator
from backend.utils.path_utils import resolve_path
from backend.utils.prompt_parser_validator import extract_json_from_response
from backend.utils.render_prompt import load_and_render_prompt, build_user_message

logger = logging.getLogger(__name__)
config = load_config(resolve_path("config.yaml"))

class AIQualityTestService:

    def __init__(self):
        self.db = get_database()
        self.prompts = config.get("prompts", {})

    async def optimize_query(
            self,
            user_query: str,
            selected_technique: str,
            provider: str,
            model: str,
            iterations: int = 5
    ) -> List[Dict[str, Any]]:

        tasks = []
        for _ in range(iterations):
            tasks.append(asyncio.create_task(
                self._optimize_query_once(
                    user_query,
                    selected_technique,
                    provider,
                    model,
                    iterations=iterations
                )
            ))

        results = await asyncio.gather(*tasks)
        return results

    async def _optimize_query_once(
            self,
            user_query: str,
            selected_technique: str,
            provider: str,
            model: str,
            iterations: int = 3
    ) -> Dict[str, Any]:

        refinement_module = AutomatedRefinementModule(
            user_query=user_query,
            provider=provider,
            model=model,
            prompts=config.get("prompts", {}),
            max_iterations=iterations
        )

        start_time = time.time()
        raw_output = refinement_module.optimize_query(selected_technique=selected_technique)
        elapsed = time.time() - start_time

        final_optimized_query = ""
        if selected_technique in ["CoT", "SC", "ReAct", "PC", "CoD", "SC_ReAct"]:
            final_optimized_query = raw_output.get("Final_Optimized_Query", "")

        usage_data = raw_output.get("usage", {})
        total_tokens = usage_data.get("tokens_spent", None)

        doc_to_insert = {
            "user_query": user_query,
            "time_in_seconds": round(elapsed, 3),
            "tokens_spent": total_tokens,
            "technique_name": selected_technique,
            "final_optimized_query": final_optimized_query
        }

        await self.db["test_optimization_results"].insert_one(doc_to_insert)
        logger.info("Inserted optimization result into test_optimization_results")
        return doc_to_insert

    async def evaluate_prompt(
            self,
            user_query: str,
            provider: str,
            model: str,
            iterations: int = 1
    ) -> List[Dict[str, Any]]:

        tasks = []
        for _ in range(iterations):
            tasks.append(asyncio.create_task(
                self._evaluate_prompt_once(user_query, provider, model)
            ))

        results = await asyncio.gather(*tasks)
        return results

    async def _evaluate_prompt_once(
            self,
            user_query: str,
            provider: str,
            model: str
    ) -> Dict[str, Any]:
        """
            Makes one call to Evaluator.evaluate(), pulls out the prompt_rating,
            stores the result in MongoDB.
        """
        evaluator = Evaluator(
            user_query=user_query,
            provider=provider,
            model=model,
            human_evaluation=False,
            prompts=config.get("prompts", {}),
        )
        result = await evaluator.evaluate()

        prompt_rating = result.get("prompt_rating", None)

        doc_to_insert = {
            "user_query": user_query,
            "prompt_rating": prompt_rating,
        }

        await self.db["test_evaluation_results"].insert_one(doc_to_insert)
        logger.info("Inserted evaluation result into test_evaluation_results")
        return doc_to_insert

    async def generate_results(
            self,
            user_text: str,
            num_versions: int,
            provider: str,
            selected_model: str
    ) -> List[Dict[str, Any]]:

        tasks = []
        for _ in range(num_versions):
            tasks.append(asyncio.create_task(
                self._generate_one_result(user_text, provider, selected_model)
            ))

        results = await asyncio.gather(*tasks)
        return results

    async def _generate_one_result(
            self,
            user_text: str,
            provider: str,
            model: str
    ) -> Dict[str, Any]:

        client: AIClient = get_ai_client(provider)
        start_time = time.time()

        messages = [{"role": "user", "content": user_text}]

        response_dict = await asyncio.to_thread(client.call_chat_completion, model, messages)

        response_text = response_dict["text"]
        usage = response_dict["usage"]

        elapsed = time.time() - start_time

        doc_to_insert = {
            "user_query": user_text,
            "time_in_seconds": usage.get("time_in_seconds", None),
            "tokens_spent": usage.get("tokens_spent", None),
            "model_name": model,
            "raw_response": response_text
        }

        await self.db["test_answer_results"].insert_one(doc_to_insert)
        logger.info("Inserted answer result into test_answer_results")
        return doc_to_insert

    async def automatic_evaluation(
            self,
            provider: str,
            model: str,
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        1) Get from test_answer_results a number (limit) of documents
        that have not been automatically evaluated yet.
        2) For each document, call LLM, substituting user_query / raw_response.
        3) Extract overall_score from response.
        4) Write (test_answer_result_id, overall_score) to automatic_answer_evaluation.

        Return list of inserted documents.
        """
        client: AIClient = get_ai_client(provider)

        query = {}
        cursor = self.db["test_answer_results"].find(query).limit(limit)
        docs_to_evaluate = await cursor.to_list(length=limit)

        inserted_results = []

        for doc in docs_to_evaluate:
            doc_id = doc["_id"]  # Mongo ObjectId
            user_query = doc["user_query"]
            model_response = doc["raw_response"]

            rendered_prompt = load_and_render_prompt(
                self.prompts.get("independent_agent"),
                {
                    "user_query": user_query,
                    "model_response": model_response
                }
            )
            messages = build_user_message(rendered_prompt)

            response_dict = await asyncio.to_thread(client.call_chat_completion, model, messages)
            response_text = response_dict["text"]

            parsed = extract_json_from_response(response_text)

            if isinstance(parsed, dict):
                overall_score = parsed.get("overall_score", None)
            else:
                overall_score = None

            doc_to_insert = {
                "test_answer_result_id": str(doc_id),
                "overall_score": overall_score
            }

            result = await self.db["automatic_answer_evaluation"].insert_one(doc_to_insert)
            logger.info("Inserted new automatic evaluation with _id=%s for test_answer_results=%s",
                        result.inserted_id, doc_id)

            inserted_results.append({
                "_id": str(result.inserted_id),
                "test_answer_result_id": str(doc_id),
                "overall_score": overall_score
            })

        return inserted_results

    async def fetch_test_answers(
        self,
        shuffle: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Gets ALL records from the test_answer_results collection.
        If shuffle=True, shuffles them in random order.

        In real code, it's better to use pagination, limits, or
        filtering of already evaluated records. For simplicity, all in a row.
        """
        cursor = self.db["test_answer_results"].find({})
        all_docs = await cursor.to_list(None)
        if not all_docs:
            logger.info("No documents found in test_answer_results.")
            return []

        if shuffle:
            random.shuffle(all_docs)
        return all_docs

    async def single_person_evaluation(
            self,
            shuffle: bool = True
    ) -> List[Dict[str, Any]]:
        """
        1) Load all answers, shuffle if necessary.
        2) For each record, ask the person for an evaluation (1..10).
        3) Store it in human_answer_evaluation (separate record per answer).
        Returns a list of inserted documents.
        """
        docs_to_evaluate = await self.fetch_test_answers(shuffle)
        if not docs_to_evaluate:
            print("No answers to evaluate.")
            return []

        inserted_records = []
        for doc in docs_to_evaluate:
            doc_id = doc["_id"]
            user_query = doc["user_query"]
            model_response = doc["raw_response"]

            print("\n=== Next answer to evaluate ===")
            print(f"user_query: {user_query}")
            print(f"model_response: {model_response}")

            while True:
                rating_str = input("Please enter your rating (1-10): ").strip()
                try:
                    rating = int(rating_str)
                    if 1 <= rating <= 10:
                        break
                    else:
                        print("Rating must be between 1 and 10.")
                except ValueError:
                    print("Invalid rating. Please enter an integer between 1 and 10.")

            doc_to_insert = {
                "test_answer_result_id": str(doc_id),
                "overall_score": rating
            }

            result = await self.db["human_answer_evaluation"].insert_one(doc_to_insert)
            logger.info("Inserted new manual evaluation _id=%s for test_answer_results=%s",
                        result.inserted_id, doc_id)

            inserted_records.append({
                "_id": str(result.inserted_id),
                "test_answer_result_id": str(doc_id),
                "overall_score": rating
            })

        return inserted_records

    async def batch_evaluation(
            self,
            chunk_size: int = 5,
            shuffle: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Manual evaluation in batches. By default, batch = 5.
        1) Load all documents (test_answer_results), shuffle if needed.
        2) Divide them into chunks (batch) by chunk_size.
        3) For each group of chunk_size records, show them all, then
        the user enters ONE evaluation, and we save it in human_answer_evaluation
            (the same evaluation for all records in the current batch).
        """
        all_docs = await self.fetch_test_answers(shuffle=shuffle)
        if not all_docs:
            print("No answers to evaluate.")
            return []

        def chunkify(lst, size):
            for i in range(0, len(lst), size):
                yield lst[i: i + size]

        inserted_records = []

        for batch_index, chunk_docs in enumerate(chunkify(all_docs, chunk_size), start=1):
            print(f"\n=== Batch #{batch_index}: {len(chunk_docs)} documents ===")
            for i, doc in enumerate(chunk_docs, start=1):
                user_query = doc["user_query"]
                model_response = doc["raw_response"]
                print(f"\n--- Document #{i} in this batch ---")
                print(f"User Query: {user_query}")
                print(f"Model Response: {model_response}")

            while True:
                rating_str = input("\nEnter ONE rating (1-10) for this entire batch: ").strip()
                try:
                    rating = int(rating_str)
                    if 1 <= rating <= 10:
                        break
                    else:
                        print("Rating must be between 1 and 10.")
                except ValueError:
                    print("Invalid rating. Please enter an integer.")

            for doc in chunk_docs:
                doc_id = doc["_id"]
                doc_to_insert = {
                    "test_answer_result_id": str(doc_id),
                    "overall_score": rating
                }
                result = await self.db["human_answer_evaluation"].insert_one(doc_to_insert)
                logger.info("Inserted batch evaluation _id=%s for test_answer_results=%s",
                            result.inserted_id, doc_id)

                inserted_records.append({
                    "_id": str(result.inserted_id),
                    "test_answer_result_id": str(doc_id),
                    "overall_score": rating
                })

        return inserted_records

