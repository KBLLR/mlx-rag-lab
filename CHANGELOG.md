# Changelog

All notable changes to the `mlx-RAG` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2025-11-08

### Added

*   Initial project setup for MLX-based Retrieval-Augmented Generation (RAG).
*   Core Python RAG pipeline under `src/`.
*   Basic CLI for interactive RAG.
*   Musicgen integration for text-to-music generation.

### Fixed

*   Resolved `AttributeError` in `EncodecModel` (`decode`, `chunk_length`).
*   Corrected Musicgen audio duration mapping in `MusicgenAdapter`.
*   Fixed `ModuleNotFoundError` and `NameError` in `musicgen_core/utils.py`.

### Changed

*   Updated `LICENSE` to MIT.
*   Enhanced `README.md` with detailed setup, usage, and contribution sections.
*   Modified `.gitignore` to specifically ignore model subdirectories while keeping `mlx-models/README.md` visible.

