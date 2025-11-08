# Security Policy for mlx-RAG

We take the security of `mlx-RAG` seriously. This document outlines our security policy and procedures for reporting vulnerabilities.

## Supported Versions

We currently support the latest stable release of `mlx-RAG`. Security updates will be provided for this version.

## Reporting a Vulnerability

If you discover a security vulnerability within `mlx-RAG`, please report it to us as soon as possible. We appreciate your efforts to responsibly disclose your findings.

**Please DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, please send an email to [security@example.com](mailto:security@example.com) (replace with actual security contact).

In your report, please include:

*   A clear and concise description of the vulnerability.
*   Steps to reproduce the vulnerability.
*   The potential impact of the vulnerability.
*   Any proof-of-concept code or screenshots that can help us understand the issue.

## Our Commitment

We are committed to:

*   Acknowledging your report within 2 business days.
*   Providing a timeline for addressing the vulnerability.
*   Keeping you informed of our progress.
*   Publicly acknowledging your contribution (if you agree) once the vulnerability is resolved.

## General Security Best Practices

*   **Keep dependencies updated:** Regularly update project dependencies to mitigate known vulnerabilities.
*   **Avoid hardcoding secrets:** Never hardcode API keys, passwords, or other sensitive information directly in the codebase. Use environment variables or secure configuration management.
*   **Input validation:** Always validate and sanitize user inputs to prevent injection attacks.
*   **Least privilege:** Ensure that components and services operate with the minimum necessary permissions.

Thank you for helping to keep `mlx-RAG` secure!
