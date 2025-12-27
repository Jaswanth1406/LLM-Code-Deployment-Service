# 🚀 LLM Code Deployment Service

An automated service that receives task requests, uses LLM-powered code generation to build web applications, deploys them to GitHub Pages, and notifies evaluation APIs — all in a single workflow.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100-teal.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Deployment](#deployment)
  - [Local Development](#local-development)
  - [Docker](#docker)
  - [Hugging Face Spaces](#hugging-face-spaces)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Security](#security)
- [License](#license)

## Overview

This project implements a student-side service for the **LLM Code Deployment** assignment. The service:

1. **Receives** task requests via a REST API
2. **Verifies** the shared secret for authentication
3. **Generates** web applications using OpenAI's GPT-4o-mini (or falls back to a template)
4. **Deploys** the generated code to GitHub Pages
5. **Notifies** the instructor's evaluation API with deployment details

The system supports multiple rounds of development, allowing iterative improvements based on evaluation feedback.

## Features

- ✅ **Dual Framework Support** — Both Flask and FastAPI implementations
- ✅ **LLM-Powered Generation** — Uses OpenAI GPT-4o-mini for intelligent code generation
- ✅ **Fallback Generator** — Template-based generation when LLM is unavailable
- ✅ **GitHub Integration** — Automatic repo creation, commits, and Pages deployment
- ✅ **Secret Verification** — Secure authentication via shared secrets
- ✅ **Async Processing** — Background task handling with result polling
- ✅ **Retry Logic** — Exponential backoff for evaluation API notifications
- ✅ **Web UI** — Built-in dashboard for testing deployments
- ✅ **Docker Ready** — Containerized deployment support
- ✅ **Multi-Round Support** — Handles iterative development cycles

## Architecture

```
┌─────────────────┐     POST /api-endpoint      ┌──────────────────┐
│  Instructor's   │ ─────────────────────────▶  │   Flask/FastAPI  │
│  Task Request   │                             │     Server       │
└─────────────────┘                             └────────┬─────────┘
                                                         │
                    ┌────────────────────────────────────┼────────────────────────────────────┐
                    │                                    ▼                                    │
                    │  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐     │
                    │  │   Secret     │───▶│   LLM Generator  │───▶│  GitHub Helper    │     │
                    │  │  Validator   │    │  (OpenAI API)    │    │  (Create/Push)    │     │
                    │  └──────────────┘    └──────────────────┘    └─────────┬─────────┘     │
                    │                                                         │               │
                    │                                                         ▼               │
                    │                                              ┌───────────────────┐     │
                    │                                              │   Enable Pages    │     │
                    │                                              └─────────┬─────────┘     │
                    └────────────────────────────────────────────────────────┼───────────────┘
                                                                             │
                                                                             ▼
┌─────────────────┐     POST (repo details)              ┌──────────────────────────────┐
│  Evaluation     │ ◀────────────────────────────────────│        Notifier              │
│     API         │                                      │  (Exponential Retry)         │
└─────────────────┘                                      └──────────────────────────────┘
```

## Tech Stack

| Component                       | Technology         | Purpose                          |
| ------------------------------- | ------------------ | -------------------------------- |
| **Backend (Primary)**     | Flask 2.3          | REST API server                  |
| **Backend (Alternative)** | FastAPI 0.100      | Async REST API with OpenAPI docs |
| **LLM Integration**       | OpenAI GPT-4o-mini | Intelligent code generation      |
| **Version Control**       | Git + GitHub API   | Repository management            |
| **HTTP Client**           | Requests 2.31      | API calls and notifications      |
| **ASGI Server**           | Uvicorn 0.23       | Production server for FastAPI    |
| **Testing**               | Pytest 7.4         | Unit and E2E testing             |
| **Configuration**         | python-dotenv      | Environment management           |
| **Containerization**      | Docker             | Deployment packaging             |

## Project Structure

```
TDS-PROJECT-1-main/
├── app.py                  # Entrypoint for Hugging Face Spaces
├── Dockerfile              # Docker container configuration
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── src/                    # Core application code
│   ├── __init__.py
│   ├── server.py           # Flask application & main logic
│   ├── fastapi_app.py      # FastAPI alternative implementation
│   ├── generator.py        # App generation orchestrator
│   ├── llm_generator.py    # OpenAI integration
│   ├── github_helper.py    # GitHub API & Git operations
│   └── notifier.py         # Evaluation API notification
│
├── static/                 # Web UI assets
│   ├── index.html          # Dashboard interface
│   ├── app.js              # Frontend JavaScript
│   └── styles.css          # Styling
│
├── scripts/
│   └── set-env.ps1         # PowerShell environment setup
│
└── tests/                  # Test suite
    ├── test_server.py      # Server unit tests
    ├── test_generator.py   # Generator tests
    ├── test_e2e_mocked.py  # End-to-end tests (Round 1)
    └── test_e2e_round2_mocked.py  # E2E tests (Round 2)
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Git installed and configured
- GitHub account with Personal Access Token
- (Optional) OpenAI API key for LLM generation

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/TDS-PROJECT-1.git
   cd TDS-PROJECT-1
   ```
2. **Create and activate virtual environment**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Or on Linux/macOS:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

| Variable                            | Required    | Description                                                 |
| ----------------------------------- | ----------- | ----------------------------------------------------------- |
| `secret`                          | ✅ Yes      | Shared secret for request authentication                    |
| `GITHUB_TOKEN`                    | ✅ Yes      | GitHub PAT with `repo` and `pages` scopes               |
| `OPENAI_API_KEY`                  | ❌ Optional | OpenAI API key for LLM generation                           |
| `GITHUB_OWNER`                    | ❌ Optional | GitHub org/user for repo creation (defaults to token owner) |
| `PORT`                            | ❌ Optional | Server port (default: 7860)                                 |
| `REQUIRE_GITHUB_TOKEN_ON_STARTUP` | ❌ Optional | Fail fast if token invalid (`true`/`false`)             |

### Setting Up Environment

**Option 1: PowerShell script**

```powershell
. .\scripts\set-env.ps1   # Loads from .env file
```

**Option 2: Manual export**

```powershell
$env:secret = 'your-shared-secret'
$env:GITHUB_TOKEN = 'ghp_xxxxxxxxxxxx'
$env:OPENAI_API_KEY = 'sk-xxxxxxxxxxxx'  # Optional
```

**Option 3: Create `.env` file**

```env
secret=your-shared-secret
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

## Usage

### Starting the Server

**Flask (default)**

```bash
python -m src.server
```

**FastAPI with Uvicorn**

```bash
uvicorn src.fastapi_app:app --host 0.0.0.0 --port 7860
```

### Web Interface

Open `http://localhost:7860` in your browser to access the deployment dashboard.

### Example API Request

```bash
curl http://localhost:7860/api-endpoint \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "your-secret",
    "task": "calculator-app",
    "round": 1,
    "nonce": "abc123",
    "brief": "Create a calculator with add, subtract, multiply, divide functions",
    "checks": ["typeof add === '\''function'\''"],
    "evaluation_url": "http://localhost:9000/eval",
    "attachments": []
  }'
```

## API Reference

### `POST /api-endpoint`

Submit a deployment task.

**Request Body:**

```json
{
  "email": "student@example.com",
  "secret": "shared-secret",
  "task": "unique-task-id",
  "round": 1,
  "nonce": "unique-nonce",
  "brief": "Application requirements description",
  "checks": ["JavaScript expressions to validate"],
  "evaluation_url": "https://eval.example.com/notify",
  "attachments": [
    {"name": "file.csv", "url": "data:text/csv;base64,..."}
  ],
  "wait_for_result": false
}
```

**Response (async):**

```json
{"status": "accepted"}
```

**Response (sync with `wait_for_result: true`):**

```json
{
  "email": "student@example.com",
  "task": "unique-task-id",
  "round": 1,
  "nonce": "unique-nonce",
  "repo_url": "https://github.com/user/repo",
  "commit_sha": "abc123...",
  "pages_url": "https://user.github.io/repo/"
}
```

### `GET /health`

Check server health and GitHub token validity.

### `GET /result?email=...&task=...&nonce=...`

Poll for deployment results (async mode).

## Deployment

### Local Development

```bash
# Set environment variables
$env:secret = 'test-secret'
$env:GITHUB_TOKEN = 'ghp_...'

# Run Flask server
python -m src.server
```

### Docker

**Build the image:**

```bash
docker build -t llm-code-deployment:latest .
```

**Run the container:**

```bash
docker run --rm -p 7860:7860 \
  -e GITHUB_TOKEN="ghp_xxxx" \
  -e secret="your-secret" \
  -e OPENAI_API_KEY="sk-xxxx" \
  llm-code-deployment:latest
```

### Hugging Face Spaces

This project is ready for deployment on Hugging Face Spaces:

1. **Create a new Space**

   - Go to [huggingface.co/new-space](https://huggingface.co/new-space)
   - Choose **Docker** as the SDK (recommended) or **Gradio/Other** for Python
2. **Upload or connect repository**

   - Connect your GitHub repo or upload files directly
   - Ensure `app.py`, `requirements.txt`, and `Dockerfile` are at the root
3. **Configure Secrets** (in Space Settings → Repository secrets)

   - `GITHUB_TOKEN` — Your GitHub Personal Access Token
   - `secret` — Your shared authentication secret
   - `OPENAI_API_KEY` — (Optional) OpenAI API key
4. **Deploy**

   - The Space will automatically build and run
   - Access your API at `https://your-username-space-name.hf.space/api-endpoint`

**Docker vs Python Space:**

- **Docker Space** (recommended): Uses the included `Dockerfile`, runs FastAPI with Uvicorn
- **Python Space**: Runs `app.py` directly with Flask

## How It Works

### Round 1: Initial Build

1. **Request Reception** — API receives JSON with task brief and attachments
2. **Authentication** — Validates the shared secret
3. **Code Generation** — Uses OpenAI GPT-4o-mini to generate:
   - `index.html` — Main application
   - `README.md` — Documentation
   - `LICENSE` — MIT license
   - Asset files from attachments
4. **Repository Creation** — Creates public GitHub repo via API
5. **Git Operations** — Initializes, commits, and pushes code
6. **Pages Deployment** — Enables GitHub Pages on main branch
7. **Notification** — POSTs results to evaluation URL with retry logic

### Round 2: Revision

1. **Clone Existing Repo** — Fetches the previously deployed code
2. **Apply Updates** — LLM generates modifications based on new brief
3. **Push Changes** — Commits and pushes updates
4. **Re-notify** — Sends updated deployment details to evaluation API

### Fallback Behavior

If `OPENAI_API_KEY` is not set or the LLM call fails:

- A simple template-based generator creates a basic HTML page
- Attachments are saved to an `assets/` directory
- The brief is displayed on the page

## Testing

Run the test suite:

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_server.py

# With coverage
pytest tests/ --cov=src
```

## Security

⚠️ **Important Security Practices:**

- **Never commit secrets** — Keep tokens out of version control
- **Use environment variables** — Store sensitive data securely
- **Token-authenticated pushes** — Tokens are stripped from remote URLs after push
- **Secret validation** — All requests must include valid shared secret
- **No secrets in generated code** — The generator avoids writing secrets to repos

**Recommended GitHub Token Scopes:**

- `repo` — Full repository access
- `workflow` — For GitHub Actions (if needed)
- `pages` — GitHub Pages management

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```
