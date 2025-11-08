# Contributing to mlx-RAG

We welcome contributions to the `mlx-RAG` project! By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md) (to be created).

## How to Contribute

1.  **Fork the repository:** Start by forking the `mlx-RAG` repository to your GitHub account.
2.  **Clone your fork:**
    ```bash
    git clone https://github.com/your-username/mlx-RAG.git
    cd mlx-RAG
    ```
3.  **Set up your development environment:** Follow the instructions in the main [README.md](README.md) for setting up `uv` and installing dependencies.
4.  **Create a new branch:** Choose a descriptive name for your branch (e.g., `feature/add-new-model`, `bugfix/fix-ingestion-error`).
    ```bash
    git checkout -b feature/your-feature-name
    ```
5.  **Make your changes:** Implement your feature or bug fix. Ensure your code adheres to the project's [Code Style](#code-style) and includes relevant unit tests.
6.  **Run tests:** Before submitting, make sure all existing tests pass and your new tests cover your changes.
    ```bash
    uv run pytest
    ```
7.  **Commit your changes:** Write clear and concise commit messages.
    ```bash
    git commit -m "feat: Add new feature for X"
    ```
8.  **Push to your fork:**
    ```bash
    git push origin feature/your-feature-name
    ```
9.  **Create a Pull Request (PR):** Go to the original `mlx-RAG` repository on GitHub and open a new Pull Request from your forked branch. Provide a detailed description of your changes.

## Code Style

We use `ruff` for linting and `black` for code formatting. Please ensure your code is formatted and linted before submitting a PR:

```bash
uv run ruff check .
uv run black .
```

## Testing

All new features and bug fixes should be accompanied by appropriate unit tests. Tests are located in the `tests/` directory.

## Reporting Bugs

If you find a bug, please open an issue on GitHub with a clear description, steps to reproduce, and expected behavior.

## Feature Requests

Feel free to open an issue on GitHub to suggest new features or improvements.

## License

By contributing to `mlx-RAG`, you agree that your contributions will be licensed under the [MIT License](LICENSE).
