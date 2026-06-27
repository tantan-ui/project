# AI Content Moderation System

This repository contains an automated content moderation system for a community forum (noverflow.io.vn). The system uses a Retrieval-Augmented Generation (RAG) architecture to evaluate user posts against official community guidelines before approving, denying, or flagging them.

## Overview

The project is split into two components:

- **Ingestion Script (`ingest.py`)**: A Python CLI script that parses community guidelines from a Word document, generates vector embeddings locally using Ollama, and uploads them to a Pinecone vector index.
- **n8n Workflow (`Moderator.json`)**: An automated backend workflow that catches incoming forum posts via webhooks, uses a LangChain AI agent to cross-reference the text with the Pinecone vector index, and updates the forum API accordingly.

## Architecture & Workflow

1. **Trigger**: A new forum post triggers the n8n webhook node.
2. **Retrieval**: The LangChain agent invokes its guideline tool to fetch strict moderation guidelines from the Pinecone vector store.
3. **Evaluation**: A local LLM (`Llama 3.2:1b` running via Ollama) processes the post strictly against the fetched context and outputs a JSON decision (`"approve"` or `"deny"`).
4. **Routing**: A switch node routes the decision:
   - **Approve**: Issues a PATCH request to approve the post.
   - **Deny**: Issues a DELETE request to remove the post.
   - **Fallback/Uncertain**: Flags the post for human moderation.

---

## Component Setup

### 1. Vector Database Ingestion (Python CLI)

The ingestion engine reads moderation policies from a local `.docx` file and seeds your vector index. It has been built as a CLI tool allowing dynamic variable adjustment.

#### Prerequisites

- Python 3.12+
- `uv` (An ultra-fast Python package installer and resolver)
- Ollama installed locally with the `nomic-embed-text` model pulled:

```bash
ollama pull nomic-embed-text
```

### Environment Setup & Installation

Navigate to the project root directory and initialize an isolated environment with `uv`.

```powershell
cd D:\project\project

# Create a virtual environment
uv venv

# Activate the environment on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies cleanly without global namespace collision
uv pip install ollama python-docx pinecone
```

#### Making it a Global Command (Windows)

To run the ingestion script from any folder without typing the full project path:

1. Create a folder to store global CLI binaries, for example: `C:\tools`.
2. In that directory, create a file named `ingest.bat`.
3. Open `ingest.bat` in Notepad and paste the following contents:

   ```cmd
   uv run --project "YOUR_PROJECT_DIRECTORY" python "YOUR_PROJECT_DIRECTORY ingest.py" %*
   ```

4. Add your scripts folder (`C:\tools`) to the Windows `Path` environment variable.
5. Restart PowerShell to apply the updated PATH.

### Execution Guide & Arguments

Place your policy handbook in the project folder. To ingest with default configuration:

```powershell
ingest Context.docx
```

To override the target index or chunk size:

```powershell
# Override index target and increase chunk size
ingest Context.docx --chunk-size 1000 --index production-context
```

To view the built-in help for all available arguments:

```powershell
ingest --help
```

#### CLI Arguments Reference

Argument | Long Flag | Default | Description
--- | --- | --- | ---
`file` | Positional | Required | Path to the target `.docx` file for parsing.
`-i` | `--index` | `context` | Target namespace/index within Pinecone.
`-c` | `--chunk-size` | `500` | Local character length allocation per split.
`-m` | `--model` | `nomic-embed-text` | Local Ollama embedding model.
`-k` | `--key` | Hardcoded Default | Target authorization Pinecone API secret string.








## 2. Automation Workflow (n8n)

The `Moderator.json` workflow defines the server-side automation logic for forum moderation.

### Prerequisites

- An `n8n` instance (self-hosted or cloud)
- A local Ollama instance accessible by `n8n`
- `llama3.2:1b` pulled locally in Ollama

```bash
ollama pull llama3.2:1b
```

- A Pinecone account and API key

### Ollama / n8n Connectivity

Depending on how `n8n` is deployed, the Ollama base URL must be configured differently.

#### Scenario A: Native n8n + Native Ollama
If `n8n` is installed locally (npm or desktop app) and Ollama is running on your host machine:

- Ollama Base URL in `n8n`: `http://localhost:11434`

#### Scenario B: n8n in Docker + Ollama running natively
When `n8n` runs inside Docker, `localhost` refers to the container itself. To reach the host machine from the container, use the Docker gateway host:

- Ollama Base URL in `n8n` (Windows/macOS): `http://host.docker.internal:11434`
- Ollama Base URL in `n8n` (Linux): `http://172.17.0.1:11434`

#### Scenario C: Both n8n and Ollama in Docker
If both services run inside the same Docker network (for example via `docker-compose`), use the service DNS name:

- Ollama Base URL in `n8n`: `http://ollama:11434`

#### Connection troubleshooting

If `n8n` still reports a connection timeout, Ollama may need to accept external requests.

- Windows:
  1. Close Ollama in the system tray.
  2. Open PowerShell and run:

    ```powershell
    setx OLLAMA_HOST "0.0.0.0"
    ```

  3. Restart Ollama.

- Linux / Docker:
  - Set `OLLAMA_HOST=0.0.0.0` in your service or container environment.

### Import Instructions

1. Open your `n8n` workspace.
2. Create a new workflow.
3. Click the menu in the top-right corner and select **Import from File**.
4. Select the `Moderator.json` file.
5. Update the Ollama and Pinecone credentials to match your environment.
6. Toggle the workflow to **Active**.

### Configuration & API Specification

The workflow expects to interact with the forum backend using an authorized service token.

- Header: `Authorization`
- Value: `Token <API_KEY>; userId= <user_id>`

### Expected Webhook Payload

The `n8n` webhook endpoint accepts a POST request with the following JSON structure:

```json
{
  "body": {
    "post": {
      "id": "12345",
      "content": "The text content of the forum post to evaluate."
    }
  }
}
```

### Security Note

> **Warning:** Hardcoded credentials and API keys (such as the Pinecone API key and authorization tokens) are currently embedded in these files for demonstration purposes. Replace them with `n8n` environment variables or secure credential stores before deploying to production.