# Installation Guide for WhatsApp Diamond Sales AI Agent

This guide will walk you through the complete setup process for the WhatsApp Diamond Sales AI Agent, including database configuration, WhatsApp integration, and agent deployment.

## Prerequisites

- Python 3.8 or higher
- Go (for WhatsApp MCP server)
- PostgreSQL database (connected to Supabase)
- Supabase account
- OpenAI API key

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd whatsapp_agent
```

## Step 2: Set Up the Environment

Run the setup script to create a virtual environment and install dependencies:

```bash
python setup.py
```

Alternatively, you can set up manually:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux
source .venv/bin/activate
# On Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Copy the example environment file and edit it with your credentials:

```bash
cp .env.example .env
```

Edit the `.env` file with your actual credentials:

```
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
```

## Step 4: Set Up WhatsApp MCP Server

1. Clone the WhatsApp MCP repository:

```bash
git clone https://github.com/lharries/whatsapp-mcp.git
cd whatsapp-mcp
```

2. Set up the WhatsApp bridge:

```bash
cd whatsapp-bridge
go run main.go
```

3. Scan the QR code with your WhatsApp mobile app to authenticate.

4. Configure the MCP server for your AI assistant by creating a configuration file:

For Claude Desktop:
```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/path/to/whatsapp-mcp/whatsapp-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

Save this as `claude_desktop_config.json` in your Claude Desktop configuration directory.

For Cursor:
```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/path/to/whatsapp-mcp/whatsapp-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

Save this as `mcp.json` in your Cursor configuration directory.

## Step 5: Set Up Database Tables

Ensure your Supabase database has the following tables:

### Diamond Inventory Table

Create a table named `diamond_inventory` with the following structure:

```sql
CREATE TABLE public.diamond_inventory (
    id TEXT PRIMARY KEY,
    carat NUMERIC NOT NULL,
    cut TEXT NOT NULL,
    color TEXT NOT NULL,
    clarity TEXT NOT NULL,
    shape TEXT NOT NULL,
    price NUMERIC NOT NULL,
    certificate TEXT,
    description TEXT,
    attributes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Chat History Table

Create a table named `chat_history` with the following structure:

```sql
CREATE TABLE public.chat_history (
    id SERIAL PRIMARY KEY,
    chat_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB
);

-- Add index for faster queries
CREATE INDEX chat_history_chat_id_idx ON public.chat_history (chat_id);
```

## Step 6: Run the Application

Start the WhatsApp Diamond Sales AI Agent:

```bash
python main.py
```

The agent will now listen for incoming WhatsApp messages and respond to diamond sales inquiries.

## Testing

Run the tests to verify that everything is working correctly:

```bash
pytest tests/
```

## Troubleshooting

### WhatsApp Connection Issues

- Ensure the WhatsApp bridge is running and authenticated
- Check that the WhatsApp MCP server is properly configured
- Verify that the WhatsApp API base URL in `config.py` matches your setup

### Database Connection Issues

- Verify your Supabase credentials in the `.env` file
- Ensure the database tables are created with the correct structure
- Check that your Supabase service role key has the necessary permissions

### Agent Response Issues

- Verify your OpenAI API key is valid and has sufficient credits
- Check the agent logs for any errors in processing messages
- Ensure the system prompt in `agent/prompts.py` is appropriate for your use case