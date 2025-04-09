import math
import random

import numpy as np

import matplotlib.pyplot as plt
from typing import List, Tuple
from statistics import mean

from scipy.stats import spearmanr, pearsonr

from backend.db.db import get_database

async def get_pairs_no_averaging() -> List[Tuple[float, float]]:
    """
    Collects pairs of (human_score, llm_score) WITHOUT averaging, assuming:
        - `human_answer_evaluation` and `automatic_answer_evaluation` have ONE record
    for each test_answer_result_id.
        - So if there are 20 answers, there are 20 documents in each collection,
    each with the same test_answer_result_id field -> 20 pairs.

    Return: [(human_score, llm_score), ...].
    """
    db = get_database()
    human_coll = db["human_answer_evaluation"]
    auto_coll  = db["automatic_answer_evaluation"]

    human_docs = await human_coll.find({}).to_list(None)
    auto_docs  = await auto_coll.find({}).to_list(None)

    human_map = {}
    for doc in human_docs:
        rid = doc["test_answer_result_id"]
        score = doc["overall_score"]
        human_map[rid] = score

    auto_map = {}
    for doc in auto_docs:
        rid = doc["test_answer_result_id"]
        score = doc["overall_score"]
        auto_map[rid] = score

    pairs = []
    for rid, h_score in human_map.items():
        if rid in auto_map:
            a_score = auto_map[rid]
            pairs.append((h_score, a_score))

    return pairs


async def build_correlation_diagram():
    """
   Correlation chart:
    - X-axis: LLM score
    - Y-axis: Human score
    - One dot (purple) for each document from test_answer_results that has an average human score and an llm score.
    """
    pairs = await get_pairs_no_averaging()
    if not pairs:
        print("No (human, llm) pairs found.")
        return

    human_scores = [p[0] for p in pairs]
    llm_scores = [p[1] for p in pairs]

    jittered_x = []
    jittered_y = []
    for x, y in zip(llm_scores, human_scores):
        jx = x + random.uniform(-0.05, 0.05)
        jy = y + random.uniform(-0.05, 0.05)
        jittered_x.append(jx)
        jittered_y.append(jy)

    rho_spearman, _ = spearmanr(human_scores, llm_scores)
    rho_pearson, _ = pearsonr(human_scores, llm_scores)
    qwk = quadratic_weighted_kappa(human_scores, llm_scores, min_rating=1, max_rating=10)
    rmse_value = rmse(human_scores, llm_scores)

    print(f"Spearman correlation = {rho_spearman:.3f}")
    print(f"Pearson correlation  = {rho_pearson:.3f}")
    print(f"Quadratic Weighted Kappa = {qwk:.3f}")
    print(f"RMSE (root mean sq. error) = {rmse_value:.3f}")

    plt.figure(figsize=(6, 6))
    plt.scatter(jittered_x, jittered_y, color='purple', alpha=0.7)
    plt.xlabel("LLM evaluation")
    plt.ylabel("Human evaluation")
    plt.title("Answer Correlation Diagram: LLM vs Human ")
    plt.grid(True)
    plt.xlim(1, 11)
    plt.ylim(1, 11)
    plt.xticks(range(1, 11))
    plt.yticks(range(1, 11))
    plt.show()

async def get_pairs_1to1() -> List[Tuple[float, float]]:
    """
    Assume that the collections human_answer_evaluation and automatic_answer_evaluation have exactly
     one score for each answer (test_answer_result_id).
    Return a list of (human_score, llm_score) in any order.
    """
    db = get_database()
    human_coll = db["human_answer_evaluation"]
    auto_coll = db["automatic_answer_evaluation"]

    human_docs = await human_coll.find({}).to_list(None)
    auto_docs = await auto_coll.find({}).to_list(None)

    human_map = {}
    for doc in human_docs:
        rid = doc["test_answer_result_id"]
        h_score = doc["overall_score"]
        human_map[rid] = h_score

    llm_map = {}
    for doc in auto_docs:
        rid = doc["test_answer_result_id"]
        a_score = doc["overall_score"]
        llm_map[rid] = a_score

    pairs = []
    for rid, h_score in human_map.items():
        if rid in llm_map:
            a_score = llm_map[rid]
            pairs.append((h_score, a_score))

    return pairs


async def all_evaluations_diagram():
    """
    Bar chart:
    - X axis: answer number (1..N)
    - Y axis: score value (1..10)
    - Green bars: human
    - Red bars: llm

    At the end, print mean, min, max for human and for llm.
    """
    pairs = await get_pairs_1to1()
    if not pairs:
        print("No data (pairs) found.")
        return

    human_scores = [p[0] for p in pairs]
    llm_scores = [p[1] for p in pairs]


    N = len(pairs)
    x_indices = np.arange(1, N + 1)

    h_mean = mean(human_scores)
    h_min, h_max = min(human_scores), max(human_scores)

    l_mean = mean(llm_scores)
    l_min, l_max = min(llm_scores), max(llm_scores)

    print(f"=== Human scores ({N}) ===")
    print(f"Mean={h_mean:.2f}, Min={h_min}, Max={h_max}")
    print(f"=== LLM scores ({N}) ===")
    print(f"Mean={l_mean:.2f}, Min={l_min}, Max={l_max}")

    width = 0.4

    plt.figure(figsize=(10, 5))
    plt.bar(x_indices - width/2, human_scores, width=width,
            color='green', alpha=0.7, label='Human')
    plt.bar(x_indices + width/2, llm_scores,   width=width,
            color='red',   alpha=0.7, label='LLM')

    plt.xlabel("Answer Index")
    plt.ylabel("Evaluation score")
    plt.title("Evaluations Diagram")
    plt.xticks(x_indices, x_indices)
    plt.ylim(0, 11)
    plt.yticks(range(1, 11))
    plt.legend()
    plt.grid(axis='y', alpha=0.75)

    plt.show()


def quadratic_weighted_kappa(y_true, y_pred, min_rating=None, max_rating=None):
    """
    Calculates Quadratic Weighted Kappa (QWK) for two lists of ratings.

    Parameters:
    ----------
    y_true : list or array of int
    The "true" ratings (e.g. human ratings).
    y_pred : list or array of int
    The "predicted" ratings (e.g. LLM ratings).
    min_rating : int (optional)
    The minimum rating value. If None, take the min of y_true, y_pred.
    max_rating : int (optional)
    The maximum rating value. If None, take the max of y_true, y_pred.

    Returns:
    -----------
    float
    QWK value (from -∞ to 1, where 1 = perfect match).
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    if min_rating is None:
        min_rating = min(y_true.min(), y_pred.min())
    if max_rating is None:
        max_rating = max(y_true.max(), y_pred.max())

    num_ratings = int(max_rating - min_rating + 1)

    y_true_shifted = y_true - min_rating
    y_pred_shifted = y_pred - min_rating

    O = np.zeros((num_ratings, num_ratings), dtype=float)
    for t, p in zip(y_true_shifted, y_pred_shifted):
        O[t, p] += 1

    W = np.zeros((num_ratings, num_ratings), dtype=float)
    for i in range(num_ratings):
        for j in range(num_ratings):
            W[i, j] = float((i - j) ** 2) / (num_ratings - 1) ** 2

    hist_true = np.sum(O, axis=1)
    hist_pred = np.sum(O, axis=0)

    N = O.sum()
    E = np.outer(hist_true, hist_pred) / N

    numerator = (W * O).sum()
    denominator = (W * E).sum()

    if denominator == 0:
        return 1.0

    kappa = 1.0 - numerator / denominator
    return kappa

def rmse(y_true, y_pred):
    """
    Returns the RMSE (root mean square error) between two lists of numbers.
    """
    if len(y_true) == 0:
        return 0.0

    mse = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / len(y_true)
    return math.sqrt(mse)

def save_correlation_table_matplotlib():
    data = [
        [0.866, 0.632, 0.775, 0.671, 1.360, 0.866, 0.707, 0.775, 0.742],
        [0.625, 0.794, 0.502, 0.667, 0.584, 0.636, 0.585, 0.571, 0.549], # Snake
        [0.705, 0.810, 0.509, 0.699, 0.780, 0.580, 0.582, 0.665, 0.560],
        [0.705, 0.814, 0.508, 0.700, 0.760, 0.671, 0.592, 0.646, 0.555]
        # [0.806, 0.742, 0.894, 0.837, 0.742, 0.806, 0.775, 0.775, 0.742],
        # [0.611, 0.734, 0.588, 0.708, 0.729, 0.581, 0.585, 0.684, 0.577], # Scenario
        # [0.653, 0.745, 0.531, 0.738, 0.800, 0.618, 0.587, 0.634, 0.607],
        # [0.636, 0.758, 0.619, 0.773, 0.792, 0.631, 0.625, 0.699, 0.587]
        # [0.775, 0.806, 0.922, 0.671, 0.922, 0.548, 0.775, 0.775, 0.806],
        # [0.673, 0.629, 0.536, 0.766, 0.482, 0.712, 0.610, 0.706, 0.594], # Analysis
        # [0.857, 0.695, 0.735, 0.867, 0.606, 0.706, 0.658, 0.727, 0.629],
        # [0.837, 0.711, 0.698, 0.856, 0.591, 0.740, 0.648, 0.746, 0.621]
    ]
    row_labels = ["RMSE", "QWK", "Spearman", "Pearson"]

    col_labels = [
        "gpt-4o\nCoT", "gpt-4o\nPC", "gpt-4o\nReAct",
        "o3-mini\nCoT", "o3-mini\nPC", "o3-mini\nReAct",
        "claude-3-7-sonnet\nCoT", "claude-3-7-sonnet\nPC", "claude-3-7-sonnet\nReAct"
    ]

    fig, ax = plt.subplots(figsize=(5, 2))
    ax.set_axis_off()

    table = ax.table(
        cellText=data,
        rowLabels=row_labels,
        colLabels=col_labels,
        loc="center"
    )

    table.set_fontsize(10)
    table.scale(1.2, 1.6)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("black")
        cell.set_linewidth(1.0)

    plt.savefig("snake_corr_table.png", dpi=300, bbox_inches="tight")


def save_correlation_table_in_chunks():
    full_data = [
        [0.775, 0.806, 0.922, 0.671, 0.922, 0.548, 0.775, 0.775, 0.806],
        [0.673, 0.629, 0.536, 0.766, 0.482, 0.712, 0.610, 0.706, 0.594], # Analysis
        [0.857, 0.695, 0.735, 0.867, 0.606, 0.706, 0.658, 0.727, 0.629],
        [0.837, 0.711, 0.698, 0.856, 0.591, 0.740, 0.648, 0.746, 0.621]
    ]
    row_labels = ["RMSE", "QWK", "Spearman", "Pearson"]
    col_labels = [
        "CoT", "PC", "ReAct",
        "CoT", "PC", "ReAct",
        "CoT", "PC", "ReAct"
    ]

    chunk_size = 3

    def chunk_list(lst, size):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]

    col_chunks = list(chunk_list(col_labels, chunk_size))

    for chunk_index, cols_in_chunk in enumerate(col_chunks, start=1):
        start_col = (chunk_index - 1) * chunk_size
        end_col = start_col + chunk_size

        data_sub = []
        for row in full_data:
            data_sub.append(row[start_col:end_col])

        fig, ax = plt.subplots(figsize=(6, 2))
        ax.set_axis_off()

        table = ax.table(
            cellText=data_sub,
            rowLabels=row_labels,
            colLabels=cols_in_chunk,
            loc="center"
        )

        table.set_fontsize(10)
        table.scale(1.2, 1.6)
        for (r, c), cell in table.get_celld().items():
            cell.set_edgecolor("black")
            cell.set_linewidth(1.0)

        plt.savefig(
            f"analysis_corr_table_part{chunk_index}.png",
            dpi=300,
            bbox_inches="tight"
        )
        plt.close(fig)


def plot_min_mean_max_columns(data, save_path="my_rating_diagram.png"):
    model_order = ["gpt-4o", "o3-mini", "claude-3-7-sonnet"]
    technique_order = ["CoT", "PC", "ReAct"]

    all_groups = []
    for m in model_order:
        for t in technique_order:
            all_groups.append((m, t))

    model_colors = {
        "gpt-4o": "yellow",
        "o3-mini": "green",
        "claude-3-7-sonnet": "blue"
    }

    data_map = {}
    for item in data:
        m = item["model"]
        t = item["technique"]
        key = (m, t)
        data_map[key] = (
            item["min_val"],
            item["mean_val"],
            item["max_val"]
        )

    x_indices = np.arange(len(all_groups))

    fig, ax = plt.subplots(figsize=(10, 5))

    line_min = ax.plot([], [], color="red", label="Min rating")[0]
    line_max = ax.plot([], [], color="orange", label="Max rating")[0]
    line_mean = ax.plot([], [], color="purple", label="Mean rating")[0]

    ax.set_xlim(-1, len(all_groups) + 1)

    bar_width = 0.6

    half_w = 0.3

    for i, (m, t) in enumerate(all_groups):

        left = i - bar_width / 2
        bottom = 1
        height = 9

        color_model = model_colors.get(m, "gray")

        ax.bar(x=i, height=height, bottom=bottom,
               width=bar_width, color=color_model, alpha=0.6)

        top_y = bottom + height
        ax.text(i, top_y + 0.3, t, ha='center', va='bottom', fontsize=9)

        if (m, t) in data_map:
            val_min, val_mean, val_max = data_map[(m, t)]
        else:
            val_min, val_mean, val_max = (None, None, None)

        if val_min is None:
            continue

        ax.hlines(val_min, i - half_w, i + half_w, color="red", linewidth=2)
        ax.hlines(val_mean, i - half_w, i + half_w, color="purple", linewidth=2)
        ax.hlines(val_max, i - half_w, i + half_w, color="orange", linewidth=2)

    ax.set_xticks(x_indices)
    x_labels = [m for (m, t) in all_groups]
    ax.set_xticklabels(x_labels, rotation=0)
    ax.set_ylim(0, 11)
    ax.set_yticks(range(1, 11))
    ax.set_ylabel("LLM and Human evaluations")
    ax.set_title("Ratio of all results")

    ax.legend(handles=[line_min, line_max, line_mean], loc="upper right")

    ax.grid(axis='y', alpha=0.4)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved chart to {save_path}")
    plt.close(fig)

def plot_errorbar(data, save_path="errorbar_plot.png"):
    model_order = ["gpt-4o", "o3-mini", "claude-3-7"]
    technique_order = ["CoT", "PC", "ReAct"]
    all_groups = [(m, t) for m in model_order for t in technique_order]

    data_map = {}
    for item in data:
        key = (item["model"], item["technique"])
        data_map[key] = (item["min_val"], item["mean_val"], item["max_val"])

    x = np.arange(len(all_groups))
    means = []
    lower_err = []
    upper_err = []

    for group in all_groups:
        if group in data_map:
            mn, mean, mx = data_map[group]
        else:
            mn, mean, mx = (np.nan, np.nan, np.nan)
        means.append(mean)
        lower_err.append(mean - mn)
        upper_err.append(mx - mean)

    error = [lower_err, upper_err]

    plt.figure(figsize=(8, 5))
    plt.errorbar(x, means, yerr=error, fmt='o', color="black", ecolor="gray",
                    elinewidth=2, capsize=5, capthick=2)

    xtick_labels = [f"{m}\n{t}" for m, t in all_groups]
    plt.xticks(x, xtick_labels)

    plt.ylabel("LLM and Human evaluations")
    plt.grid(True, which="both", ls="--", alpha=0.7)
    plt.ylim(0, 11)
    plt.yticks(range(1, 11))
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()
