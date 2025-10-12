# Project TODO

This file tracks upcoming tasks, long-term goals, and strategic ideas for the Freqtrade AI project. Each item includes context and reasoning to provide a comprehensive knowledge base.

---

## 🎯 Active Discussion (This Session)

- **[ ] Integrate Freqtrade with MCP Orchestrator**

---

# Project TODO

This file tracks upcoming tasks, long-term goals, and strategic ideas for the Freqtrade AI project. Each item includes context and reasoning to provide a comprehensive knowledge base.

---

## 🎯 Active Mission

- **[ ] `GeminiV6` - Decoupled Trend-Following**
    - **[WHY]:** The `GeminiV5` experiment proved that a "coupled" architecture (training the AI on pre-filtered signals) is flawed and leads to a no-trade bias. This is our attempt to fix that core problem.
    - **[WHAT]:** Refactor the strategy to decouple the AI's prediction from the strategy's entry filters.
    - **[HOW]:** The AI's job will be simplified to predict "will the price rise in the next N candles?" on all data. The strategy's job will be to use its trend indicators as a filter, only acting on the AI's signal when the trend conditions are met.

- **[ ] Enhance `CemV1Strategy` - Our Current Best Model**
    - **[WHY]:** We achieved a significant milestone with `CemV1Strategy`, creating a profitable baseline. Before exploring entirely new strategies, we should maximize the potential of our best-performing asset.
    - **[WHAT]:** Systematically improve the existing `CemV1Strategy`.
    - **[HOW]:**
        - **[ ] Idea 1: Implement the Full Two-Stage Architecture.** Our current `CemV1` is only the first stage (the GRU model, simulated by a standard FreqAI model). The next logical step is to implement the second `XGBoost` "confirmer" model to create the full, dual-confidence system described in the `CemAI.txt` design document. This is the core of Cem's original vision.
        - **[ ] Idea 2: Perform Exhaustive Hyperparameter Optimization.** Our initial `hyperopt` run was short but successful. A much longer run (e.g., 1000-5000 epochs) could uncover significantly more profitable parameter combinations for entry, exit, and stop-loss, further improving the baseline.

---

## 🏛️ Project Architecture

- **[BLUEPRINT]: The AI Firm Vision**
    - Our visions have completely converged into a single, powerful blueprint for an AI-run firm.
    - The **"CEO Agent"** is the master agent that consumes a rich "virtual dashboard" to make high-level strategic decisions.
    - The **MCP Dashboard** is the central nervous system, fed by specialist agents reporting on sentiment, ETF inflows, political news, and market data.
    - The **"Narrative Analyst" Agent** is the team of these specialist agents, feeding the dashboard.
    - The **"Trader Agents"** and **"Developer Agents"** are the "Hunters" and "Strategy Forges" that the CEO commands to execute its vision.

- **[CONCEPT]: Dynamic Agent Spawning**
    - The CEO Agent should have the ability to dynamically spawn temporary, mission-specific "task force" agents, in addition to commanding its permanent "departments." This allows for a more flexible and efficient allocation of resources for short-term R&D tasks, like the "Strategy Development Factory" scenario.

- **[ ] Integrate Freqtrade with MCP Orchestrator**
    - **[WHY]:** Our ultimate vision is a multi-agent AI trading firm. We have the trading engine (`CemV1Strategy`) and a prototype for the communication backbone (the MCP server). This task is the critical bridge to connect them.
    - **[WHAT]:** Create a standalone "Trader AI Agent" script.
    - **[HOW]:** This agent's script would be a Python file that runs in its own terminal. It would periodically query the MCP server for directives (e.g., `{'directive': 'START_TRADE_BOT', 'strategy': 'CemV1Strategy'}`). Upon receiving a directive, it would construct and execute the appropriate `freqtrade` shell command. It would also need the ability to find and terminate existing `freqtrade` processes to stop the bot when directed.

- **[ ] Define Advanced Agent Behaviors & Operational Logic**
    - **[WHY]:** To translate our high-level agent roles (Trader, Auditor, etc.) into concrete, implementable logic, capturing the detailed operational procedures from our previous research.
    - **[WHAT]:** Document the specific, rule-based behaviors for each agent in our AI Firm.
    - **[HOW]:** This involves specifying the exact logic for each agent:
        - **Trader Agent:** Must be programmed to report P&L hourly via the MCP. It must also have a function to automatically halt trading and alert the CEO if a configurable drawdown limit is breached (e.g., -2% over 3 hours).
        - **Auditor Agent:** Must be programmed to automatically fetch new models from the "Quant Group" and run them through a gauntlet of backtests against pre-defined risk metrics (e.g., Sharpe Ratio > 1.5, Max Drawdown < 20%), flagging under-performers.
        - **CEO Agent:** Must have the capability to issue parallelized tasks to multiple agents simultaneously (e.g., instructing 5 "Quant" agents to each train a different model on a different coin).

- **[ ] Define Core Orchestration Technology**
    - **[WHY]:** To turn our abstract architectural blueprint into a concrete technical plan.
    - **[WHAT]:** Formally adopt `tmux` as the core framework for managing our multi-agent system and the `spec.md`/`prompt.md` file structure for issuing directives to the CEO agent.
    - **[HOW]:** The "Integrate Freqtrade with MCP Orchestrator" task will be implemented using `tmux` to create and manage the different agent windows (CEO, Trader, etc.). The CEO agent will be programmed to read a `prompt.md` file to begin its work.

---

## 🧠 Future Strategy R&D

- **[ ] Mean Reversion Strategy**
    - **[WHY]:** This is a classic, proven trading archetype that is the opposite of trend-following. It operates on the assumption that prices will revert to a historical average.
    - **[WHAT]:** Design and build a new FreqAI strategy based on mean-reversion principles.
    - **[HOW]:** An agent could start by using features like RSI, Stochastic RSI, or the distance of the price from a long-term moving average. The AI's goal would be to predict when the price is "over-extended" and likely to snap back.
        - **[NOTE]:** A potential implementation could be a "HFT-Lite" version focused on very short timeframes (seconds).

- **[ ] Trend-Continuation Classifier**
    - **[WHY]:** A variation of trend-following. Instead of just identifying a trend, this would use AI to determine the probability of an *existing* trend continuing.
    - **[WHAT]:** Build a strategy that first confirms a strong trend is in place using traditional indicators (like ADX), and *then* uses an AI model to decide if it's a good time to enter in the direction of that trend.

- **[ ] Explore Options Trading Strategies**
    - **[WHY]:** To expand our firm's capabilities beyond spot/futures and into the derivatives market, which offers unique opportunities for alpha generation.
    - **[WHAT]:** Research and develop agents capable of trading options.
    - **[HOW]:** The first candidate for implementation would be a **"Vol-Skew Harvest"** strategy. This involves using delta-hedged straddle/strangle combinations to profit from mispricings in the options volatility skew.

---

## 🔬 Advanced AI Concepts & Improvements

- **[ ] Implement Feature Importance & Selection**
    - **[WHY]:** Our `GeminiV3` and `GeminiV4` experiments failed, likely because we fed the model too many irrelevant features ("feature noise"), which confused it. A smaller set of high-impact features is often more effective.
    - **[WHAT]:** Implement a systematic process to identify the most impactful features and remove the noise.
    - **[HOW]:** An agent should use the FreqAI Jupyter notebook (`freqtrade/freqai/freqai-notebook.ipynb`). By loading our trained `CemV1Strategy` model, we can use libraries like `shap` to analyze and rank all features by their contribution to the model's predictions. We can then remove the least important features and retrain the model to see if its performance improves.

- **[ ] Multi-Target Prediction**
    - **[WHY]:** Currently, our model only predicts an entry signal. A more advanced model could add more value.
    - **[WHAT]:** Train the AI to predict multiple outputs simultaneously, such as both the buy signal and the optimal stop-loss value for that specific trade.

- **[ ] Dynamic Classification Target**
    - **[WHY]:** A fixed profit target (e.g., 2%) may be too easy in a volatile market and too hard in a stable one.
    - **[WHAT]:** Make the classification target adaptive to market volatility.
    - **[HOW]:** Instead of `future_return > 0.02`, the target could be `future_return > (ATR * 0.5)`, where ATR (Average True Range) is a measure of volatility.

- **[ ] Market Regime Filter**
    - **[WHY]:** Most strategies only work well in specific market conditions (e.g., trending or ranging).
    - **[WHAT]:** Build a secondary AI model whose only job is to identify the current market regime. The main strategy would then only be allowed to trade if the regime filter gives it a green light.

- **[ ] Anomaly Detection Entries**
    - **[WHY]:** Large, profitable price movements are often preceded by unusual, anomalous market activity.
    - **[WHAT]:** Use an anomaly detection model (e.g., Isolation Forest) as a feature to identify these unusual conditions, which could serve as a powerful entry signal.

---

## 🚀 Next Level Plan: The "Asymmetric Opportunities" Portfolio

- **[PHILOSOPHY]:** This is a contingency plan for if our current evolutionary approach does not yield high-multiple returns. It marks a shift from seeking a single, consistent edge to building a portfolio of specialized "Hunter" agents, each designed to exploit rare, high-impact, asymmetric market events. The goal is not to trade often, but to trade with maximum impact and leverage when a prime opportunity is identified.

- **[ ] The "Black Swan" Hunter (Crash & Spike Arbitrage)**
    - **[GOAL]:** To profit from extreme market volatility events (flash crashes, parabolic spikes).
    - **[WHY]:** A single, correctly predicted 30-50% market move, when properly leveraged, can generate returns that would otherwise take years to accumulate. This is the highest risk/reward agent.
    - **[HOW]:** This agent would monitor derivatives data, order book depth, cross-exchange liquidity gaps, and extreme volatility indicators. It would be trained to recognize the statistical signatures that precede a liquidity crisis or cascading liquidation event and execute a significant leveraged position.
        - **[NOTE]:** This can be enhanced with an "Event-Driven" approach, using a macro-economic calendar to anticipate volatility around specific known events (e.g., FED announcements, token unlocks).

- **[ ] The "Breakout" Hunter (Multi-Year Level Exploitation)**
    - **[GOAL]:** To profit from the momentum ignition when a major asset breaks a multi-year support or resistance level.
    - **[WHY]:** The breakout of a long-term, widely-watched consolidation pattern is one of the most reliable and powerful signals in technical analysis, as it forces a large number of market participants to act.
    - **[HOW]:** This agent would analyze price data on `daily` or `weekly` timeframes to identify these long-term levels. When a decisive breakout occurs, it would execute a leveraged trade to capture the initial explosive momentum.

- **[ ] The "Arbitrageur" (The Income Generator)**
    - **[GOAL]:** To generate a steady, low-risk stream of income to fund the more speculative "Hunter" agents and grow the base capital.
    - **[WHY]:** High-risk strategies require a stable capital base to draw from. This agent provides it by exploiting market inefficiencies rather than predicting market direction.
    - **[HOW]:** This agent would constantly monitor **funding rates** on perpetual futures and **basis spreads** across multiple exchanges. When a significant, sustained arbitrage opportunity appears, it would take opposing positions on the two exchanges to capture the spread as near risk-free profit.

- **[ ] The "Decay Hunter" Agent (ETF Rebalancing)**
    - **[GOAL]:** To profit from the inherent value decay of leveraged ETFs during periods of high volatility and low directional trend.
    - **[WHY]:** This provides a source of alpha that is uncorrelated to market direction, allowing the firm to profit from sideways, choppy markets where other strategies fail.
    - **[HOW]:** This agent would be activated by the "Market Regime Filter." It would identify suitable leveraged ETFs, verify their shortability on our target exchange, and execute short positions, holding them for a multi-day period to capture the effect of volatility decay.
        - **[NOTE]:** A more advanced version could incorporate an AI-driven "factor-tilt" (e.g., shifting from low-volatility to momentum based on market conditions).

- **[ ] The "Stat-Arb" Hunter (Statistical Arbitrage)**
    - **[GOAL]:** To profit from temporary statistical deviations in a basket of cointegrated assets (e.g., crypto stocks, related tokens, ETFs).
    - **[WHY]:** A market-neutral strategy that profits from relative value rather than market direction. It is often highly compatible with leverage.
    - **[HOW]:** The agent would find a basket of assets that historically move together. When one asset in the basket deviates significantly from the others, the agent would short the outperformer and long the underperformer(s), betting on the statistical relationship (the "spread") to revert to its mean.

---

## ✨ PHASE 3: The Sentient Trading Floor (Long-Term Vision)

- **[PHILOSOPHY]:** This is the ultimate evolution of our project. It moves beyond a static portfolio of agents into a self-improving, self-auditing ecosystem. The goal is to create a system that not only executes trades but also *autonomously creates, tests, and refines its own strategies* while actively trying to eliminate its own weaknesses. The emergent behavior of this system is the **"Adaptive Alpha Hunter"** - a firm that automatically re-trains and re-allocates capital when its profit curve begins to droop.

- **[ ] The "Strategy Forge" (The R&D Department)**
    - **[CONCEPT]:** An engine that uses **Genetic Algorithms (GAs)** to automatically evolve new, profitable "Hunter" agents.
    - **[WHY]:** A GA can test millions of combinations of indicators and rules, discovering novel strategies a human would never conceive of. It removes us as the bottleneck to innovation.
    - **[HOW]:** Create a "primordial soup" of trading rules (indicators, operators, actions). The Forge will randomly combine them into proto-strategies, backtest them, and have the most profitable ones "breed" to create new generations, while the losers "die." The end result is a highly-evolved, battle-tested new agent to be deployed.

- **[ ] The "Red Team" Agent (The Adversary)**
    - **[CONCEPT]:** A dedicated AI agent whose only job is to **find weaknesses in our own profitable strategies and trade against them.**
    - **[WHY]:** Every market edge decays over time. The Red Team's job is to detect this decay *before* it costs us real money. It is our internal immune system.
    - **[HOW]:** The Red Team agent analyzes the trade history of our profitable Hunters to find predictable patterns in their behavior. If it can successfully profit by counter-trading a Hunter, it proves that Hunter's edge is weakening, and the CEO Agent is alerted to reduce its capital allocation.

- **[ ] The "CRO" Agent (Chief Risk Officer)**
    - **[CONCEPT]:** A specialized agent with **ultimate veto power** over the entire portfolio, focused exclusively on advanced risk management, not profit.
    - **[WHY]:** The use of leverage to achieve high returns requires an unbreakable safety mechanism to prevent catastrophic losses.
    - **[HOW]:** Before any high-leverage trade is executed, the CRO agent runs thousands of **Monte Carlo simulations** to model the potential impact on the entire portfolio. If the simulation shows a non-trivial probability of a catastrophic loss (e.g., >1% chance of a 30% drawdown), the CRO vetoes the trade, protecting the fund from ruin.

- **[ ] The "Causal Inference" Agent (The Skeptic)**
    - **[CONCEPT]:** An agent that acts as a final filter for all trade hypotheses, determining true cause-and-effect.
    - **[WHY]:** Most market signals are correlations, not causal links. Acting on spurious correlations is a primary way funds lose money. This agent protects our capital from narrative-chasing and flawed models.
    - **[HOW]:** When the "Narrative Analyst" proposes a hypothesis (e.g., "Positive news is causing the price to rise"), this agent uses advanced statistical models (e.g., Granger Causality, Bayesian Networks) to challenge it. It asks: "Did the news *truly cause* the rise, or did a third hidden factor cause both?" Only causally-validated hypotheses would be passed to the CEO agent for consideration.

- **[ ] The "Execution Optimizer" Agent (Microstructure Awareness)**
    - **[CONCEPT]:** An agent dedicated to optimal trade execution, minimizing market impact (slippage).
    - **[WHY]:** A profitable strategy can be rendered unprofitable by poor execution. Capturing the theoretical alpha requires executing trades as close to the decision price as possible.
    - **[HOW]:** This agent would take a directive from the CEO (e.g., "Buy 1000 BTC over the next 2 hours"). It would then use execution algorithms like **TWAP (Time-Weighted Average Price)** or **VWAP (Volume-Weighted Average Price)**. It would break the large order into hundreds of smaller, randomized "child" orders and place them strategically over time, constantly monitoring the live order book to hide its intention and minimize slippage.

- **[ ] Online Learning Models (Real-Time Adaptation)**
    - **[CONCEPT]:** An agent or model architecture that can learn and adapt *in real-time* as new market data arrives tick-by-tick.
    - **[WHY]:** Markets are non-stationary; their underlying dynamics are always changing. A model that can adapt in real-time will always have a fresher, more relevant understanding of the market than a stale, offline model.
    - **[HOW]:** This would involve exploring models designed for online learning (e.g., using the **River ML** library). This agent wouldn't replace the offline models entirely but could act as a "fine-tuner," making small adjustments to a main strategy's predictions based on the very latest market action.

- **[ ] The "Portfolio Manager" Agent (The Alpha Accountant)**
    - **[CONCEPT]:** A specialized agent that continuously analyzes the performance of all other trading agents and strategies in the portfolio. It provides the CEO agent with the critical data needed for strategic capital allocation.
    - **[WHY]:** To run our system like a true fund, the CEO needs to make data-driven decisions. Is the "Black Swan" Hunter" actually skillful, or just lucky? Are the "Breakout Hunter" and "CemV1" secretly making the same trades, creating hidden concentration risk? This agent answers those questions.
    - **[HOW]:** This agent would consume the trade logs from all live strategies and calculate advanced portfolio metrics (Sharpe/Sortino Ratios, Alpha/Beta, Drawdown Analysis, Correlation Matrix). The output of this agent *is* the primary data source for the "virtual dashboard" consumed by the CEO Agent via the MCP.

- **[ ] The "DevOps" Team (Self-Healing Codebase)**
    - **[CONCEPT]:** An always-on team of agents dedicated to automating the maintenance of our `freqtrade` fork.
    - **[WHY]:** To ensure our system always has the latest features, bug fixes, and security patches from the upstream `freqtrade` repository without requiring manual intervention.
    - **[HOW]:** This team would consist of:
        - A **"Lookout"** agent that periodically runs `git pull upstream develop`.
        - A **"Quality Control"** agent that runs tests and static analysis on the new code.
        - A **"Corrector"** agent that attempts to automatically fix any merge conflicts or new errors introduced by the update.

---

## 🧹 Knowledge & Maintenance

- **[ ] Review and apply the model management strategies outlined in `KNOWLEDGEBASE.md`**
    - **[WHY]:** To ensure our `user_data/models/` directory remains organized, reproducible, and that we can leverage past experiments effectively.
    - **[WHAT]:** Periodically revisit the `KNOWLEDGEBASE.md` file to execute model cleanup and leverage old models for new tests.

---

## ⚙️ Operational Frameworks

- **[ ] Implement GitFlow Branching Model**
    - **[WHY]:** As our project grows with multiple agents and experiments ("Hunters," "Forges," etc.), our current single `develop` branch will become chaotic and risky. Adopting a professional branching model is necessary to allow for radical experimentation without destabilizing our working, profitable strategies.
    - **[WHAT]:** Transition our Git workflow to the GitFlow model.
    - **[HOW]:** This involves establishing a set of branch conventions:
        - **`main`:** Sacred branch for production-ready code only.
        - **`develop`:** The primary integration branch for completed features.
        - **`feature/<agent-name>`:** All new work (e.g., `feature/black-swan-hunter`) will be done in isolated branches, protecting `develop` and `main` from experimental code until it is tested and approved.
    - **[STATUS]:** Postponed. We will implement this when the project's complexity makes it necessary.

---

## PHASE 4: Future Frontiers (Post-Sentience)

- **[ ] Liquidity Magnet Market-Maker (LMO)**
    - **[CONCEPT]:** A market-making strategy that analyzes order book micro-structure to provide liquidity and capture the bid-ask spread, plus exchange rebates.
    - **[WHY]:** This is a fundamentally different source of alpha that can generate profit even in flat, low-volatility markets. It is a highly specialized, institutional-grade strategy.
    - **[STATUS]:** Postponed. This likely requires a different, lower-latency technology stack than Freqtrade and should only be considered after the core AI Firm is fully operational and profitable.
