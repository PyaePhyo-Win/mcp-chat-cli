# MCP Chat

MCP Chat is a command-line interface application built to learn and demonstrate how a Model Context Protocol (MCP) server and client interact. It enables chat capabilities with AI models through the Gemini API, supporting document retrieval, command-based prompts, and extensible tool integrations.

## Project Structure

```text
.
├── core/                   # Core application logic
│   ├── chat.py             # Base Chat class handling LLM & Tool orchestration
│   ├── cli_chat.py         # specialized CliChat for CLI interactions
│   ├── cli.py              # Main CLI application (UI, prompts, auto-completion)
│   ├── gemini.py           # Gemini LLM service wrapper (Async Streaming)
│   └── tools.py            # MCP Tool management and execution
├── main.py                 # Entry point of the application
├── mcp_client.py           # Model Context Protocol client implementation
├── mcp_server.py           # Model Context Protocol server implementation
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # Project documentation
```

## Component Descriptions

| File/Folder | Description |
| :--- | :--- |
| **`core/`** | Contains the internal modules that drive the chat and interface logic. |
| `core/chat.py` | Manages the conversation state and coordinates between the LLM and various MCP tools. |
| `core/cli_chat.py` | Extends the base Chat to handle CLI-specific features like `@` resource mentions and `/` commands. |
| `core/cli.py` | Built with `prompt-toolkit` and `rich`, this handles the terminal UI, styled inputs, and real-time streaming Markdown rendering. |
| `core/gemini.py` | Interfaces with the Google GenAI SDK to provide asynchronous streaming responses. |
| `core/tools.py` | Bridges the LLM's function calling with the registered MCP server tools. |
| **`main.py`** | The startup script that initializes the MCP clients, sets up the LLM service, and launches the CLI app. |
| **`mcp_client.py`** | A robust client that communicates with MCP servers to fetch resources, prompts, and tools. |
| **`mcp_server.py`** | A sample MCP server providing document resources and prompt templates. |
| **`pyproject.toml`** | Defines Python dependencies like `rich`, `prompt-toolkit`, and `google-genai`. |

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
