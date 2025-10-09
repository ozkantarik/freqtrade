# Project TODO

This file tracks upcoming tasks and ideas for our Freqtrade AI project.

## GeminiV4 Strategy Development

- [x] **Option 1: Volatility Trading:** Build a strategy to trade market volatility itself (e.g., using Bollinger Band Width or ATR). *(Conclusion: Not viable with the tested approach)*
- [ ] **Option 2: Pure Trend Following:** Build a strategy that identifies and follows major trends without predicting specific price targets.
- [ ] **Option 3: Mean Reversion:** Build a strategy that trades on the assumption that prices will revert to their average (e.g., using RSI or distance from a moving average).

## Advanced AI Concepts

- [ ] **Concept 1: Multi-Target Prediction:** Train the AI to predict both the buy signal and the optimal stop-loss value for that specific trade.
- [ ] **Concept 2: Dynamic Classification Target:** Make the classification target adaptive to market volatility (e.g., `future_return > ATR * factor`).
- [ ] **Concept 3: Market Regime Filter:** Build a secondary AI model to identify the market regime (e.g., 'trending', 'ranging') and allow the main strategy to trade only in favorable conditions.
- [ ] **Concept 4: Anomaly Detection Entries:** Use an anomaly detection model to identify unusual market conditions that may precede large price movements.
