import asyncio

from AiQualityTestService import AIQualityTestService

async def main():
    service = AIQualityTestService()

    # optimize_res = await service.optimize_query(
    #     user_query="Analyze the impact of remote work on global productivity trends over the past decade, providing key data and insights. Use authority sources and provide their links.",
    #     selected_technique="ReAct",
    #     provider="claude",
    #     model="claude-3-7-sonnet-latest",
    #     iterations=1
    # )
    # print("=== OPTIMIZATIONS RESULTS ===", optimize_res)

    # evaluate_res = await service.evaluate_prompt(
    #     user_query="Hi, I want to create a snake game in python. I want to have functionality such as collision, food, counting and make a traditional design.",
    #     provider="openai",
    #     model="gpt-4o",
    #     iterations=20
    # )
    # print("=== EVALUATIONS RESULTS ===", evaluate_res)

    generate_res = await service.generate_results(
        user_text="Create a scenario for a 15-minute short film about aliens with ambiguous intentions visiting a rural area on Earth. The scenario should include a clear plot, development, and climax while leaving room for interpretation of the aliens' true motives, appearance, and the nature of their interaction with humans. The tone should blend mystery and drama, with potential for either wonder or horror depending on interpretation. Focus on visual storytelling elements that would work well in a short film format.",
        num_versions=20,
        provider="claude",
        selected_model="claude-3-7-sonnet-latest"
    )
    print("=== ANSWERS RESULTS ===", generate_res)

    generate_res = await service.automatic_evaluation(
        provider="claude",
        model="claude-3-7-sonnet-latest",
        limit=20
    )
    print("=== AUTOMATIC EVALUATIONS RESULTS ===", generate_res)

    # generate_res = await service.single_person_evaluation(
    #     shuffle=False
    # )
    # print("=== SINGLE HUMAN EVALUATIONS RESULTS ===", generate_res)

    # generate_res = await service.batch_evaluation(
    #     chunk_size=5,
    #     shuffle=True
    # )
    # print("=== BATCH HUMAN EVALUATIONS RESULTS ===", generate_res)
if __name__ == "__main__":
    asyncio.run(main())
