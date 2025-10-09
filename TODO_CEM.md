
# Project `CemV1Strategy` - TODO List

This file outlines the future development roadmap and strategic goals for the project.

## 1. Implement Cem's Full Vision (Two-Stage Model)

*   **Priority:** 1 (User-selected)
*   **Description:** Evolve the current single-stage model into the two-stage architecture from Cem's specification. 
*   **Tasks:**
    *   Develop and train a primary GRU model.
    *   Implement a `DataProvider` to load the predictions from the GRU model as a new feature (e.g., `%-gru_prediction`).
    *   Test and validate the dual-confidence check logic.

## 2. Increase Trade Frequency (Feature Expansion)

*   **Priority:** 2
*   **Description:** Add more diverse and advanced features to the model to provide it with more opportunities to find high-confidence trades.
*   **Ideas:**
    *   Integrate Order Book features (e.g., bid/ask volume, spread analysis).
    *   Explore different indicator families beyond standard momentum (e.g., volatility indicators like ATR, statistical indicators).
    *   Implement sentiment analysis by integrating a news feed API as a feature.

## 3. Advanced Hyperparameter Optimization

*   **Priority:** 3
*   **Description:** Go beyond optimizing only the entry/exit thresholds. A more comprehensive hyperopt can yield significant improvements.
*   **Tasks:**
    *   Add `stoploss` to the hyperopt space to find a dynamic, optimal stoploss value.
    *   Add key indicator parameters (e.g., RSI period) to the hyperopt space.

## 4. Scale to More Pairs & Different Markets

*   **Priority:** 4
*   **Description:** Test the robustness and scalability of the strategy.
*   **Tasks:**
    *   Expand the `pair_whitelist` to include more volatile or alternative assets.
    *   Re-run hyperopt on a broader portfolio of pairs.
    *   Investigate adapting the strategy for different market types (e.g., Futures, if applicable).

## 5. Deploy to Live Dry-Run

*   **Priority:** 5 (Deferred by user)
*   **Description:** Deploy the current profitable strategy to a live server in dry-run mode.
*   **Goal:** To monitor its performance on new, unseen, real-time market data and validate its real-world viability.

## 6. Build Orchestrator Integration

*   **Priority:** 6
*   **Description:** Begin scaffolding the `Tmux-Orchestrator` framework to manage the `CemV1Strategy` bot as a 'worker' agent.
*   **Goal:** To achieve the final vision of an AI-managed trading firm where a 'CEO' agent can start, stop, and monitor this strategy bot.
