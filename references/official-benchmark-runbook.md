# Official Benchmark Runbook

Always create a virtual environment and pin the benchmark repository commit in the report. Commands below are starting points; the benchmark repository is authoritative when its CLI changes.

## SWE-bench Verified

```bash
python3 -m venv .venv-swebench
source .venv-swebench/bin/activate
python -m pip install -U swebench
docker info

python -m swebench.harness.run_evaluation \
  --dataset_name princeton-nlp/SWE-bench_Verified \
  --predictions_path predictions.jsonl \
  --max_workers 4 \
  --run_id xfg-agent-review
```

`predictions.jsonl` normally contains `instance_id`, `model_name_or_path`, and `model_patch`. Keep the generated report and Docker logs. Score is resolved / total after the official harness applies tests.

## Terminal-Bench

```bash
python3 -m venv .venv-terminal
source .venv-terminal/bin/activate
python -m pip install -U terminal-bench
docker info
tb --help
```

Select one published task set, then run the official CLI with the chosen agent adapter. Save the complete result directory, task manifest, and per-task duration. Do not score from a transcript alone.

## BFCL v3

```bash
python3 -m venv .venv-bfcl
source .venv-bfcl/bin/activate
python -m pip install -U bfcl
bfcl generate --help
bfcl evaluate --help
```

Use one fixed model endpoint and category list. Keep generation and evaluation logs separately. Report simple, multiple, parallel, and executable/tool categories; never average incompatible categories into a single "BFCL score."

## OSWorld

```bash
git clone --depth 1 https://github.com/xlang-ai/OSWorld.git
cd OSWorld
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start the environment exactly as its README specifies. Use the official task JSON, controller, and evaluator. Preserve screenshots, VM state, action traces, and the official result file. Run one desktop profile at a time.

## GAIA

```bash
huggingface-cli download gaia-benchmark/GAIA \
  --repo-type dataset \
  --local-dir data/gaia
```

Run the fixed level/split, disable access to benchmark solutions, and score with the official exact-match contract. Keep retrieved URLs, file artifacts, and final answers.

## TheAgentCompany

```bash
git clone --depth 1 https://github.com/TheAgentCompany/TheAgentCompany.git
cd TheAgentCompany
docker compose up -d
```

Use one published scenario profile. Record internal messages, tool calls, artifacts, and partial-credit state. Long-horizon scenarios should report both final success and rubric completion.

## WebArena / AndroidWorld / MLE-bench / AgentBench

Clone the official repository, use its documented setup, and keep the output artifact named by that harness. For AndroidWorld, connect a controlled emulator/device profile and record screen state. For MLE-bench, capture submissions and leaderboard-equivalent metrics.

## Minimum result package

For each external benchmark, archive:

1. benchmark repository commit or dataset revision;
2. runner command;
3. task ID list;
4. official raw result file;
5. per-task score;
6. aggregate score;
7. duration and token/cost data when the harness emits it;
8. any failure classification.
