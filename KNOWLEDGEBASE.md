# FreqAI Model Management Knowledge Base

This document outlines the best practices and procedures for managing FreqAI models within the freqtrade project. Adhering to this workflow ensures that experiments are reproducible, old models can be revisited, and the `user_data/models/` directory remains organized.

## 1. How to Recover/Reverse-Engineer a Model's Configuration

If you have a model directory but have lost the original configuration file, you can recover the exact parameters used for its training.

### Primary Method: `run_params.json`

FreqAI automatically saves the core training parameters inside the model's directory.

- **Location:** `user_data/models/<your-identifier>/run_params.json`
- **Content:** This JSON file contains the `freqai` configuration block and other key parameters like `timeframe` and `stake_amount`.
- **Usage:** To restore the configuration, simply copy the contents of this file (specifically the `freqai` object) into a new `config.json` file.

**Example `run_params.json`:**
```json
{
    "freqai": {
        "enabled": true,
        "freqaimodel": "LightGBMClassifier",
        "identifier": "gemini-v5-trend",
        "train_period_days": 30,
        "backtest_period_days": 7,
        // ... and so on
    },
    "timeframe": "5m",
    "stake_amount": 200
}
```

### Secondary Method: Git History

If `run_params.json` is missing, you can use Git to find the commit where the model `identifier` was used.

- **Command:** Use `git log` with the `-S` flag (pickaxe) to search for commits that introduced or removed a specific string.
- **Example:**
  ```bash
  # Search for the exact identifier string in the history of all config files
  git log --all -p -S'gemini-v5-trend' -- *config*.json
  ```
- **Usage:** This command will show you the exact commits and diffs where the identifier was added or changed, allowing you to check out that commit and retrieve the full configuration file.

## 2. How to Test Old Models

Re-evaluating old models against new market data is a valuable strategy.

- **Flag:** `--freqai-backtest-live-models`
- **Purpose:** This flag tells `freqtrade backtesting` to use existing, pre-trained models instead of training new ones.

### Workflow for Testing Old Models

1.  **Identify Model:** Choose a model to test from `user_data/models/`.
2.  **Recover Config:** Retrieve its original configuration from its `run_params.json` file as described in section 1.
3.  **Set Identifier:** Ensure the `identifier` in your current config matches the model you want to test.
4.  **Run Backtest:** Execute the backtesting command with the `--freqai-backtest-live-models` flag and a new `--timerange`.

## 3. How to Clean the `user_data/models/` Folder

To prevent clutter, periodically clean up "orphan" models that are no longer linked to an active configuration file.

### Safe Cleanup Procedure

1.  **List Active Identifiers:** Programmatically parse all `config_*.json` files and create a list of all `identifier` values currently in use.
2.  **List Model Directories:** Get a list of all subdirectories within `user_data/models/`.
3.  **Identify Orphans:** Find the directories from step 2 that are not in the list from step 1. These are orphans.
4.  **Archive First:** Instead of immediate deletion (`rm -rf`), archive the orphan directories into a single compressed file (e.g., `archived_models_YYYY-MM-DD.tar.gz`).
5.  **Move Archive:** Move the archive to a separate backup location.
6.  **Delete Later:** You can permanently delete the archive after a safe period (e.g., a few weeks).

## 4. Best Practice Workflow for Model Creation

A disciplined workflow is essential for long-term success and organization.

**The "One Experiment, One Config, Commit First" Principle:**

1.  **One Experiment, One Config:** For each new experimental model, create a **new, descriptively named config file**.
    - *Bad:* Editing `config.json` over and over.
    - *Good:* `config_v8_volatility_feature.json`
2.  **Matching Identifier:** Inside the new config file, set the `identifier` to a name that matches the experiment.
    - *Identifier:* `"v8_volatility_feature"`
3.  **Commit First:** **Before** starting the training, commit the new config file and any related strategy code changes to Git.
    - *Commit Message:* `feat(freqai): Add volatility index as new feature for model v8`
4.  **Train:** Now, run your backtest or live training.

This process creates a permanent, self-documenting link between your Git history, your configuration file, and the resulting model folder on your disk. It makes model recovery, testing, and cleanup trivial.
