# Development Guidelines for mlx-RAG

**Date:** Wednesday, November 5, 2025

This document outlines the development practices, artifact management, and release procedures for the `mlx-RAG` monorepo, with a strong emphasis on maintaining a local-first, MLX-purist approach.

## 1. Branch Strategy

To ensure organized and isolated development, the following branch strategy will be maintained:

*   **`main`**: This branch represents the stable, production-ready version of the project. All releases will be tagged from `main`.
*   **`development`**: Feature branches will be merged into `development` for integration testing. This branch serves as the aggregate of all ongoing features before they are deemed stable enough for `main`.
*   **Feature Branches**: All new features, bug fixes, or experimental work should be developed on dedicated feature branches, branched off `development`. Branch names should be descriptive (e.g., `feat/audio-stack`, `fix/vdb-query`). Once complete and reviewed, feature branches will be merged into `development`.

## 2. Local Artifacts and Uncommitted Items

All development, including large models, generated data, and experimental output, should primarily remain local until explicitly ready for broader sharing or publication. Critical items to remain local include:

*   **`KBLLR_face_MCKP/`**: This directory contains specific native client code/assets that are not part of the core RAG engine for distribution at this stage.
*   **`coremltools/`**: Vendored or external projects not part of the core `mlx-RAG` source.
*   **`flux/`, `glitchVHS-main/`, `lora/`, `LoRATraining/`, `musicgen/`, `segment_anything/`, `speechcommands/`, `StableDiffusion/`, `Tools/`, `ui/`, `DT-Intent-Sample-main/`, `Data/`**: These directories are either external projects, experimental, or contain large datasets/outputs that are intended for local development and are excluded from version control.
*   **Model Weights and Indexes**: The contents of `models/mlx-models/`, `models/embeddings/`, and `models/indexes/` (e.g., `*.npz` files, downloaded LLM checkpoints) are considered local artifacts. While the directories themselves might be tracked for structure, their large binary contents are ignored.
*   **Generated Logs and Outputs**: Directories like `var/logs/`, `var/outputs/`, `iterm2-logs/`, and `nanobanana-output/` are explicitly ignored (`*.log`, `*.npz` for generated vector DBs).
*   **Virtual Environments and IDE-specific files**: These are strictly local to the developer's environment.

## 3. Staging and Promotion Criteria

Local changes will be promoted to staging (e.g., merging from `development` to `main` for a release candidate) based on the following criteria:

*   **Feature Completeness**: The feature or bug fix must be fully implemented and meet all defined requirements.
*   **Code Review**: All changes must successfully pass a peer code review process.
*   **Automated Tests**: Unit and integration tests must pass with 100% coverage for new logic, and existing tests must remain stable.
*   **Performance Benchmarking**: For MLX-specific components, performance benchmarks (e.g., inference speed, memory usage on Apple Silicon) should be run and meet established targets.
*   **Documentation**: Relevant documentation (API docs, usage guides, `README.md` updates) must be complete and up-to-date.
*   **No Pending Local Artifacts**: Ensure that no unintended local artifacts or large files are inadvertently included in the promotion. Review `.gitignore` effectiveness.

## 4. Release Preparation Checklist (Pre-Publish)

Before any public release or publication, the following checklist must be completed:

*   [ ] **Final Code Review**: A thorough review of all code, ensuring no sensitive information, debugging code, or temporary hacks are present.
*   [ ] **Dependency Audit**: Verify all `pyproject.toml` dependencies are correct, pinned appropriately, and do not contain unnecessary packages. Run `uv sync` to confirm a clean build.
*   [ ] **License Verification**: Ensure all code adheres to the project's `LICENSE` and that any third-party components have compatible licenses.
*   [ ] **Documentation Finalization**: All user-facing documentation (`README.md`, `docs/`) is accurate, comprehensive, and clear.
*   [ ] **Demo/Example Usability**: Confirm that `demo.py` or equivalent examples work flawlessly and are easy to set up and run.
*   [ ] **API Stability**: Ensure public APIs (e.g., `MLXModelEngine` interfaces) are stable and well-defined.
*   [ ] **Asset Stripping**: Confirm that all large, local-only model weights and generated data are correctly excluded from the final packaged release.
*   [ ] **Security Audit**: Basic security checks for common vulnerabilities, especially concerning local file access or external interactions.
*   [ ] **Version Bump**: Update the project version in `pyproject.toml`.
*   [ ] **Tag Release**: Create a Git tag for the release version on the `main` branch.

## 5. Ignored Files and Directories Catalog

The following files and directories are explicitly ignored by Git, ensuring they remain local development artifacts or are managed separately:

```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.pytest_cache/
.mypy_cache/

# Virtual environment
.venv/
env/
env.bak/
venv/

# IDEs and editors
.vscode/
.DS_Store
*.sublime-workspace
*.sublime-project

# Logs and outputs
var/logs/
var/outputs/
iterm2-logs/
nanobanana-output/
*.log

# MLX specific generated files
*.npz

# Models and embeddings (ignore content, but keep directories if needed for structure)
# The directories themselves might be tracked, but the large binary files within them are often ignored.
models/mlx-models/
models/embeddings/
models/indexes/

# Specific directories to keep local (as per user instruction and inferred from directory listing)
KBLLR_face_MCKP/
coremltools/
flux/
glitchVHS-main/
lora/
LoRATraining/
musicgen/
segment_anything/
speechcommands/
StableDiffusion/
Tools/
ui/
DT-Intent-Sample-main/
AILib/
Data/

# Other temporary files
*~
*.bak
*.swp
*.swo
```
