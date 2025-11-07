# MLX Setup - Gemini AI Assistant Guide

This `GEMINI.md` file serves as a high-level entry point for AI assistant interactions within the `MLX Setup` project. It provides essential context and directs the AI to more detailed documentation.

## Project Overview

This project aims to confirm that your MLX environment is correctly configured and optimized for performance on Apple Silicon. It focuses on verifying core MLX functionalities, understanding lazy computation and unified memory, and applying optimization techniques for efficient model execution.

## Key Documentation Files

For detailed instructions, context, and project-specific documentation, please refer to the following files:

*   [`README.md`](README.md): High-level project overview and setup instructions.
*   [`SITEMAP.md`](SITEMAP.md): A human-friendly overview of the repository structure.
*   [`AUDIT-log.md`](AUDIT-log.md): Checklist and criteria for assessing the project's "good state."
*   [`GEMINI.md`](GEMINI.md): This AI assistant / MCP configuration and context file.
*   [`tasks.md`](tasks.md): A ledger for tracking all project tasks and their status.

## AI Assistant Specific Instructions

*   **Prioritize verification and optimization tasks** related to MLX installation and performance on Apple Silicon.
*   **Refer to official MLX documentation** ([https://ml-explore.github.io/mlx/build/html/index.html](https://ml-explore.github.io/mlx/build/html/index.html)) and `ml-explore/mlx-examples` for best practices.
*   **Focus on system-level checks** and Python environment configurations.
*   **When suggesting optimizations**, consider the impact on memory and computation, and provide clear instructions.

## Dependency Management

Dependencies are primarily managed via `pip` for `mlx` and `mlx-lm`.
*   To install core MLX: `pip install mlx`
*   To install MLX for LLMs: `pip install mlx-lm`

## Building and Running

This project primarily involves running Python scripts to verify MLX functionality and observe its behavior. There are no complex build steps beyond installing the `mlx` package.

*   **Basic MLX Test**: Run a Python script with `import mlx.core as mx` and perform basic array operations.
*   **Optimization Tests**: Implement and run small benchmarks to test the impact of different optimization techniques (e.g., with and without quantization, varying batch sizes).