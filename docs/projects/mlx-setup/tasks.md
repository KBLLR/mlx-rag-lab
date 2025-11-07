# Task Ledger for MLX Setup

Track all work for the `MLX Setup` project here. Keep the table **sorted by priority** (top = highest).

## Backlog
| ID    | Title                                            | Description                                                   | Priority | Owner | Notes                                                  |
|-------|--------------------------------------------------|---------------------------------------------------------------|----------|-------|--------------------------------------------------------|
| MLX-001 | Verify MLX Core Installation                     | Confirm successful installation of `mlx` and basic functionality. | High     |       | Run simple array operations and `eval()` tests.        |
| MLX-002 | Document Lazy Computation Behavior               | Create a clear explanation and code example demonstrating MLX's lazy computation. | High     |       | Show how `eval()` triggers execution.                  |
| MLX-003 | Document Unified Memory Architecture             | Explain and demonstrate how MLX utilizes unified memory on Apple Silicon. | High     |       | Highlight seamless CPU/GPU operation.                  |
| MLX-004 | Research and Document Quantization Best Practices | Investigate and summarize MLX quantization techniques for model optimization. | Medium   |       | Include 4-bit, 8-bit, and DWQ if applicable.           |
| MLX-005 | Explore Batch Size Optimization                  | Document how adjusting batch sizes impacts memory usage and performance during MLX operations. | Medium   |       | Provide examples for fine-tuning or inference.         |
| MLX-006 | Investigate Gradient Checkpointing               | Explain and document the use of gradient checkpointing for memory reduction in MLX training. | Medium   |       | Note the trade-off with computation speed.             |
| MLX-007 | Document Memory Wiring (macOS 15.0+)             | Research and explain the memory wiring feature for large models on macOS 15.0+. | Low      |       | Note OS version requirement.                           |
| MLX-008 | Create MLX Environment Health Check Script       | Develop a Python script to automatically verify MLX installation and key optimizations. | Low      |       | Output system info, MLX version, and basic test results. |

## In Progress
| ID | Title | Started (YYYY-MM-DD) | Owner | Notes |
|----|-------|----------------------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|--------------|----------|-------|

## Done
| ID    | Title                                            | Completed (YYYY-MM-DD) | Outcome                                                |
|-------|--------------------------------------------------|------------------------|--------------------------------------------------------|
| MLX-000 | Review mlx-RAG pyproject.toml for MLX version and dependencies | 2025-11-07             | Confirmed mlx~=0.29.3 is used and dependencies are appropriate. |