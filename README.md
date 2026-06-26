AI Content Moderation System
This repository contains an automated content moderation system for a community forum (noverflow.io.vn). The system uses a Retrieval-Augmented Generation (RAG) architecture to evaluate user posts against official community guidelines before approving, denying, or flagging them.
The project is split into two components:
Ingestion Script (ingest.py): A Python script that parses community guidelines from a Word document, generates vector embeddings locally using Ollama, and uploads them to a Pinecone vector index.
n8n Workflow (Moderator.json): An automated backend workflow that catches incoming forum posts via webhooks, uses a LangChain AI Agent to cross-reference the text with the Pinecone vector index, and updates the forum API accordingly.
🛠 Architecture & Workflow
Trigger: A new forum post triggers the n8n Webhook node.
Retrieval: The LangChain Agent invokes its Guideline tool to fetch strict moderation guidelines from the Pinecone Vector Store.
Evaluation: A local LLM (Llama 3.2:1b running via Ollama) processes the post strictly against the fetched context and outputs a JSON decision ("approve" or "deny").
Routing: A Switch node routes the decision:
Approve: Issues a PATCH request to approve the post.
Deny: Issues a DELETE request to remove the post.
Fallback/Uncertain: Flags the post for human moderation via a fallback route.
🚀 Component Setup
1. Vector Database Ingestion (Python)
The script reads moderation policies from a local .docx file and seeds your vector index.
Prerequisites
Python 3.8+
Ollama installed locally with the nomic-embed-text model pulled:

Bash
ollama pull nomic-embed-text
Installation & Execution
Install dependencies:

Bash
pip install ollama python-docx pinecone
Place your policy handbook in the root directory and name it Context.docx.

Run the ingestion script to chunk, embed, and upsert data to Pinecone:

Bash
python ingest.py
2. Automation Workflow (n8n)
The JSON file defines the server-side automation logic.

Prerequisites
An n8n instance (self-hosted or cloud).

Local Ollama instance accessible by n8n with llama3.2:1b pulled:

Bash
ollama pull llama3.2:1b
A Pinecone account and API key.

Import Instructions
Open your n8n workspace.

Create a new workflow.

Click the menu in the top right corner and select Import from File.

Select the Moderator.json file.

Update credentials for the Ollama and Pinecone nodes to match your local/cloud setups.

Toggle the workflow to Active.

🔑 Configuration & API Spec
API Authorization
The workflow expects to interact with the forum backend using an authorized service token. If updating secrets, ensure the HTTP Request headers contain the correct key:

Header: Authorization

Value: Token MySuperSecretAutomatedModeratorToken12345; userId=1

Expected Webhook Payload
The n8n entry point listens for a POST request matching the following structure:

JSON
{
  "body": {
    "post": {
      "id": "12345",
      "content": "The text content of the forum post to evaluate."
    }
  }
}
🛡 Security Note
[!WARNING]
Hardcoded credentials and API keys (such as the Pinecone API Key and Authorization tokens) are currently embedded in these files for demonstration purposes. Always replace these with n8n Environment Variables or secure credential stores before deploying to production.
