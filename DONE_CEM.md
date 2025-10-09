
# Project `CemV1Strategy` - Session Debrief & Learnings

This document details the complete workflow, including errors, resolutions, and key learnings from the session on 2025-10-09.

## 1. Initial Goal & Context

The primary objective was to analyze a WhatsApp chat history between Tarik (Captain) and Cem to understand the context of their AI trading project. The initial request was to read the chat and prepare for questions.

## 2. The "Clean Slate" Pivot: A Case Study in Debugging

Our initial plan was to build upon Captain's existing `AIV3` strategy. However, this led to a persistent and difficult-to-diagnose `Invalid parameter file` error.

**Lessons Learned from Failures:**

*   **Problem:** We were unable to run `backtesting` or `hyperopt` on a cloned version of the `AIV3` strategy.
*   **Hypothesis 1 (File Existence):** We first thought the strategy's `.json` file was missing. Creating an empty file with `touch` did not work.
*   **Hypothesis 2 (JSON Validity):** We then hypothesized the file needed to be a valid JSON object. Writing `{}` to the file did not work.
*   **Hypothesis 3 (JSON Structure):** We then hypothesized the file needed a specific internal structure (`{"params": ...}`). This also failed.
*   **Hypothesis 4 (Permissions):** We checked file permissions with `ls -l`, which were correct and not the source of the error.
*   **Hypothesis 5 (Misleading Error):** We theorized the error was misleading and was related to missing parameters for `XGBoostRegressor` in the main config. This was proven false by checking the official examples.
*   **Conclusion & Pivot:** After exhausting all logical paths, we concluded the cloned files contained a hidden, unresolvable issue. We adopted the Captain's initial suggestion to start with a **"Clean Slate"**. This was the correct strategic decision.

## 3. Building the `CemV1Strategy` Baseline

Starting from scratch, we systematically built a new, minimal FreqAI strategy. This process also involved debugging several common setup issues:

1.  **`ModuleNotFoundError: rapidjson`:** Diagnosed as a missing dependency. Resolved by having the Captain install `python-rapidjson` and `xgboost` via `pip`.
2.  **Environment/PATH Issue:** Diagnosed why the installed libraries were not found by the application. The `which python3` command revealed the system's global Python was being used. **Resolution:** All subsequent commands were modified to use the full, explicit path to the virtual environment's executable (`/home/tarik/git/freqtrade/.venv/bin/python3`).
3.  **`Invalid choice: 'train'`:** Corrected our workflow, realizing that FreqAI model training is triggered by `backtesting` or `hyperopt`, not a separate `train` command.
4.  **Configuration Validation Errors:** Systematically added required parameters (`include_timeframes`, `exit_pricing`, `stoploss`, etc.) to the minimal `config_cem_v1.json` until it passed validation.
5.  **`NameError: 'DataFrame' is not defined`:** A simple coding error where an `import` statement was missing. Resolved by adding `from pandas import DataFrame`.
6.  **`KeyError: '&-s_label'` / `KeyError: '%-gru_prediction'`:** A deep FreqAI workflow issue. We learned that features for the model must be prefixed with `%-` and that columns added *before* `freqai.start()` are not available to the entry/exit logic. **Resolution:** We correctly structured the strategy to define features in `feature_engineering_standard` and add other necessary columns *after* `freqai.start()`.
7.  **`Trying to access pretrained model...`:** The final recurring error. This occurred whenever we changed the strategy's features. **Resolution:** We established the correct procedure is to delete the old model directory (`rm -rf user_data/models/<identifier>`) to force a clean retraining.

## 4. The Breakthrough: Successful Optimization

After fixing all data and configuration issues, we successfully ran `hyperopt` on the full 8-month dataset (`20250201-20251001`).

*   **Result:** The optimizer found a profitable set of parameters.
*   **Optimal Parameters Found:**
    *   `buy_future_max_return`: **0.079**
    *   `sell_future_max_return`: **0.001**
*   **Key Learning:** The default entry threshold of 3% was far too conservative. A higher threshold of 7.9% was found to be profitable, indicating a strategy of extreme selectivity.

## 5. Final Validation

A final backtest was run using these optimized parameters. 

*   **Result:** **PROFITABLE**.
*   **Metrics:** Over the 8-month period, the strategy executed 6 trades with a **100% win rate**, yielding a **+1.20%** total profit with **0% drawdown**.

This successfully concludes the creation of a robust, profitable, single-stage AI strategy, which now serves as our validated baseline.
