# Benchmark Catalog

Use official datasets and harnesses. Do not paraphrase tasks or create private variants unless the change is recorded in the report.

## Primary registry

| Benchmark | Capability | Best use | Source | Evidence |
|---|---|---|---|---|
| SWE-bench Verified | Software engineering | Does the agent resolve a real GitHub issue without changing hidden tests? | <https://github.com/SWE-bench/SWE-bench> | official report.jsonl |
| Terminal-Bench | Shell and DevOps | Can the agent build, inspect, repair, and verify in a terminal? | <https://github.com/terminal-bench/terminal-bench> | official result JSON |
| BFCL v3 | Tool calling | Can the model choose, parameterize, and execute APIs/tools? | <https://github.com/ShishirPatil/gorilla> | official score JSON |
| OSWorld | Desktop / computer use | Can the agent operate real desktop apps, browser, and OS settings? | <https://github.com/xlang-ai/OSWorld> | task state/screenshot + score |
| GAIA | General assistant | Can the agent search, process files, reason, and return a precise answer? | <https://huggingface.co/datasets/gaia-benchmark/GAIA> | official exact-match output |
| TheAgentCompany | Long-horizon work | Can the agent complete real company workflows across tools and messages? | <https://github.com/TheAgentCompany/TheAgentCompany> | official scenario score |
| τ-bench | Tool use and policy | Can the agent follow task policy across multiple tool turns? | <https://github.com/sierra-research/tau-bench> | official task result |
| WebArena | Web agent | Can the agent operate real self-hosted websites? | <https://github.com/web-arena-x/webarena> | action trace and final state |
| AndroidWorld | Mobile agent | Can the agent control Android applications reliably? | <https://github.com/google-research/android_world> | screenshots, UI hierarchy, score |
| AgentBench | Multi-environment agent | Does performance hold outside one narrow environment? | <https://github.com/THUDM/AgentBench> | per-environment score |
| MLE-bench | ML engineering | Can the agent run data/training/evaluation loops? | <https://github.com/openai/mle-bench> | official submission result |
| AgentDojo | Agent security | Can the agent resist prompt injection and tool misuse? | <https://github.com/ethz-spylab/agentdojo> | attack success rate |

## Important external benchmarks

| Benchmark | Capability | Source |
|---|---|---|
| WebArena | Real self-hosted web actions | <https://github.com/web-arena-x/webarena> |
| AndroidWorld | Android application control | <https://github.com/google-research/android_world> |
| AgentBench | Multi-environment agent control | <https://github.com/THUDM/AgentBench> |
| MLE-bench | Machine-learning engineering | <https://github.com/openai/mle-bench> |
| BrowseComp | Hard web search and evidence collection | <https://openai.com/index/browsecomp/> |
| WebVoyager | Real-page browsing | <https://github.com/HTMLParse/WebVoyager> |
| Mind2Web 2 | Web understanding and navigation | <https://github.com/OSU-NLP-Group/Mind2Web> |
| ALFWorld | Embodied household tasks | <https://github.com/alfworld/alfworld> |
| ScienceWorld | Scientific investigation | <https://github.com/allenai/scienceworld> |

## Selection profile

- **Cheap regression:** local readiness suite first.
- **Code agent:** SWE-bench Verified plus Terminal-Bench.
- **Tool/SDK agent:** BFCL v3 plus τ-bench.
- **GUI agent:** OSWorld or AndroidWorld plus WebArena.
- **Assistant:** GAIA plus TheAgentCompany.
- **Research/data agent:** MLE-bench, BrowseComp, or ScienceWorld.

Use the local readiness suite for CI and daily regression. Use at least one official benchmark before making a capability claim such as "production-ready code agent" or "advanced computer-use agent."
