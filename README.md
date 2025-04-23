# WhatsApp Diamond Sales AI Agent

WhatsApp Diamond Sales AI Agent is an intelligent assistant designed to streamline diamond sales conversations via WhatsApp. It integrates with Supabase for inventory and chat history management, leverages advanced agent frameworks for natural language understanding, and connects to WhatsApp through the whatsapp-mcp server. The agent can answer customer queries, manage inventory lookups, and maintain conversation context, making it ideal for diamond retailers seeking automation and efficiency.

## Setup

### 1. Create and Activate a Virtual Environment (Recommended)

It is strongly recommended to use a Python virtual environment to isolate dependencies and avoid conflicts.

#### On Unix/macOS:

```sh
python3 -m venv venv
source venv/bin/activate
```

#### On Windows (cmd):

```cmd
python -m venv venv
venv\Scripts\activate
```

#### On Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```sh
pip install -r requirements.txt
```

### 3. Configure Supabase credentials

Edit `config/config.py` with your Supabase credentials.

### 4. Set up WhatsApp MCP server

Follow instructions at https://github.com/lharries/whatsapp-mcp

### 5. Run the application

```sh
python main.py
```

## Database Schema

The application requires two tables in your Supabase project **before running the application**:

1. `public.diamond_inventory` – Stores diamond inventory information
2. `public.chat_history` – Stores conversation history

### Required Table Schemas

#### 1. diamond_inventory
A sample schema for the diamond inventory table:

| Column Name   | Type        | Description                  |
|--------------|-------------|------------------------------|
| id           | uuid        | Primary key                  |
| shape        | text        | Diamond shape (e.g., Round)  |
| carat        | numeric     | Carat weight                 |
| color        | text        | Color grade                  |
| clarity      | text        | Clarity grade                |
| price        | numeric     | Price in USD                 |
| available    | boolean     | Availability status          |

#### 2. chat_history
A sample schema for the chat history table:

| Column Name   | Type        | Description                  |
|--------------|-------------|------------------------------|
| id           | uuid        | Primary key                  |
| user_id      | text        | WhatsApp user identifier     |
| message      | text        | Message content              |
| timestamp    | timestamptz | Time of message              |

**Make sure both tables exist in your Supabase project before starting the application.**

## Directory Structure

Below is an overview of the project structure:

```
.
├── agent/           # Core agent logic, prompts, and tools
│   ├── agent.py     # Main agent implementation
│   ├── prompts.py   # System and user prompt templates
│   └── tools.py     # Custom tools for the agent
├── config/          # Configuration files
│   └── config.py    # Supabase and environment configuration
├── database/        # Database interaction modules
│   ├── queries.py   # SQL queries and helpers
│   └── supabase.py  # Supabase client and DB logic
├── whatsapp/        # WhatsApp integration
│   └── client.py    # WhatsApp MCP client interface
├── utils/           # Utility functions
│   └── helpers.py   # Helper utilities
├── tests/           # Unit tests
│   └── test_agent.py# Tests for agent functionality
├── main.py          # Application entry point
├── requirements.txt # Python dependencies
├── setup.py         # Setup script for environment
├── INSTALLATION.md  # Detailed installation guide
├── README.md        # Project overview and instructions
└── .env.example     # Example environment variables
```

## Testing

Run unit tests with: `pytest tests/`