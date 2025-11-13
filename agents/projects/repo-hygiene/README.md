# Repo Hygiene Project Template

This project template outlines best practices and essential components for maintaining a clean, secure, and collaborative public repository. It serves as a checklist and guide for ensuring a project is always ready for public consumption, adhering to industry standards for open-source projects.

## Key Requirements for Public Repositories

*   **License:** Clearly defined and included (e.g., MIT License).
*   **README:** Comprehensive and standard `README.md` providing project overview, setup, usage, and contribution guidelines.
*   **CONTRIBUTING:** Detailed `CONTRIBUTING.md` with guidelines for developers to contribute effectively.
*   **CODEOWNERS:** Auto-generated or manually maintained `CODEOWNERS` file to specify individuals or teams responsible for parts of the codebase.
*   **SECURITY:** A `SECURITY.md` policy outlining how to report vulnerabilities and the project's security practices.
*   **CHANGELOG:** A `CHANGELOG.md` to keep a chronological log of all notable changes to the project.
*   **GITIGNORE:** A standard and comprehensive `.gitignore` file to exclude unnecessary files, build artifacts, and sensitive information.
*   **CI/CD:** Basic Continuous Integration/Continuous Deployment setup (e.g., GitHub Actions, GitLab CI) for automated testing and deployment.
*   **DOCS:** A well-structured `docs/` directory for project documentation, including API references, tutorials, and architectural overviews.
*   **LICENSING:** Clear and consistent licensing information across all relevant files.
*   **CODESTYLE:** Enforced code style guidelines (e.g., via linters like Black, Prettier, ESLint) to maintain code readability and consistency.
*   **TESTING:** Robust unit tests and integration tests to ensure code quality and functionality.
*   **SECRETS:** Strict exclusion of all secrets, API keys, and sensitive credentials from the repository.
*   **DATA:** Exclusion of large datasets, temporary data, or sensitive data from the repository.
*   **LOCALDEV:** Clear instructions and scripts for setting up a local development environment.

## Project Structure

Refer to `SITEMAP.md` for a human-friendly overview of the repository structure.

## Development Guidelines

Refer to `DEVELOPMENT_GUIDELINES.md` for comprehensive guidelines on development practices, artifact management, and release procedures.

## Audit Log

Refer to `AUDIT-log.md` for a checklist and criteria for assessing the project's "good state."

## Tasks

Refer to `tasks.md` for a ledger tracking all project tasks and their status.