import asyncio
import logging
import statistics
from Analysis import *



def demo_plot():
    data = [
        # {"model": "gpt-4o", "technique": "CoT",   "min_val": 6, "mean_val": 7.72, "max_val": 9},
        # {"model": "gpt-4o", "technique": "PC",    "min_val": 6, "mean_val": 7.7, "max_val": 10},
        # {"model": "gpt-4o", "technique": "ReAct", "min_val": 7, "mean_val": 8.0, "max_val": 10},
        #
        # {"model": "o3-mini", "technique": "CoT",   "min_val": 6, "mean_val": 7.92, "max_val": 10},
        # {"model": "o3-mini", "technique": "PC",    "min_val": 1, "mean_val": 7.72, "max_val": 10},    # Snake
        # {"model": "o3-mini", "technique": "ReAct", "min_val": 4, "mean_val": 7.78, "max_val": 10},
        #
        # {"model": "claude-3-7",  "technique": "CoT",   "min_val": 7, "mean_val": 8.0, "max_val": 10},
        # {"model": "claude-3-7",  "technique": "PC",    "min_val": 6, "mean_val": 7.7, "max_val": 9},
        # {"model": "claude-3-7",  "technique": "ReAct", "min_val": 7, "mean_val": 8.12, "max_val": 10}

        # {"model": "gpt-4o", "technique": "CoT",   "min_val": 6, "mean_val": 7.67, "max_val": 9},
        # {"model": "gpt-4o", "technique": "PC",    "min_val": 5, "mean_val": 7.67, "max_val": 10},
        # {"model": "gpt-4o", "technique": "ReAct", "min_val": 5, "mean_val": 7.45, "max_val": 9},
        #
        # {"model": "o3-mini", "technique": "CoT",   "min_val": 4, "mean_val": 7.85, "max_val": 10},
        # {"model": "o3-mini", "technique": "PC",    "min_val": 5, "mean_val": 7.62, "max_val": 9},    # Scenario
        # {"model": "o3-mini", "technique": "ReAct", "min_val": 6, "mean_val": 7.42, "max_val": 9},
        #
        # {"model": "claude-3-7",  "technique": "CoT",   "min_val": 6, "mean_val": 7.5, "max_val": 9},
        # {"model": "claude-3-7",  "technique": "PC",    "min_val": 5, "mean_val": 7.4, "max_val": 9},
        # {"model": "claude-3-7",  "technique": "ReAct", "min_val": 6, "mean_val": 7.42, "max_val": 9},

        {"model": "gpt-4o", "technique": "CoT", "min_val": 5, "mean_val": 6.65, "max_val": 8},
        {"model": "gpt-4o", "technique": "PC", "min_val": 5, "mean_val": 7.0, "max_val": 9},
        {"model": "gpt-4o", "technique": "ReAct", "min_val": 6, "mean_val": 7.12, "max_val": 9},

        {"model": "o3-mini", "technique": "CoT", "min_val": 5, "mean_val": 7.12, "max_val": 9},
        {"model": "o3-mini", "technique": "PC", "min_val": 5, "mean_val": 7.17, "max_val": 9},  # Analysis
        {"model": "o3-mini", "technique": "ReAct", "min_val": 6, "mean_val": 7.2, "max_val": 8},

        {"model": "claude-3-7", "technique": "CoT", "min_val": 6, "mean_val": 7.55, "max_val": 9},
        {"model": "claude-3-7", "technique": "PC", "min_val": 5, "mean_val": 7.45, "max_val": 9},
        {"model": "claude-3-7", "technique": "ReAct", "min_val": 6, "mean_val": 7.37, "max_val": 9},
    ]

    plot_errorbar(data, save_path="analysis_error_bar.png")

async def main():
    logging.basicConfig(level=logging.INFO)
    #
    # print("=== 1) Correlation Diagram ===")
    # await build_correlation_diagram()

    # print("\n")
    # print("=== 2) Evaluations Histogram ===")
    # await all_evaluations_diagram()

    # print("\n")
    # print("=== 3) Correlation Table ===")
    # save_correlation_table_matplotlib()
    # save_correlation_table_in_chunks()
    
    print("\n")
    demo_plot()

    # scores = [7, 6, 8, 7, 8, 9, 6, 8, 8, 9, 7, 6, 8, 7, 7, 8, 9, 8, 7, 7, 7, 6, 7, 7, 9, 8, 6, 8, 7, 8, 8, 7, 7, 6, 6, 8, 8, 7, 8, 7]
    # min_val = float(min(scores))
    # mean_val = float(statistics.mean(scores))
    # max_val = float(max(scores))
    # print(f"min_val={min_val}, mean_val={mean_val}, max_val={max_val}")

if __name__ == "__main__":
    asyncio.run(main())
