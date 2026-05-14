# MCP Chat

MCP Chat is a command-line interface application built to learn and demonstrate how a Model Context Protocol (MCP) server and client interact. It enables chat capabilities with AI models through the Gemini API, supporting document retrieval, command-based prompts, and extensible tool integrations.

## Prerequisites

- Python 3.10+
- Gemini API Key

## Setup

### Option 1: Setup with uv (Recommended)
`uv` is a fast Python package installer and resolver.

```bash
pip install uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Option 2: Setup with pip

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install google-genai python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

## Configuration

Create or edit the `.env` file in the project directory with your API key:
```env
GEMINI_API_KEY=""  # Enter your Gemini API secret key
```

## Running the Project

```bash
# If using uv:
uv run main.py

# If using standard Python:
python main.py
```

## Usage

- **Basic Interaction**: Type your message and press Enter to chat.
- **Document Retrieval**: Use the `@` symbol followed by a document ID to include its content in your query (e.g., `> Tell me about @deposition.md`). Document IDs will auto-complete.
- **Commands**: Use the `/` prefix to execute commands defined by the MCP server (e.g., `> /format deposition.md`). Commands auto-complete when you press Tab.

## Development

- **Documents**: Edit the `mcp_server.py` file to add new resources to the `docs` dictionary.
- **Linting/Typing**: No strict linting or type checks are currently implemented.
