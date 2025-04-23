import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Database tables
DIAMOND_INVENTORY_TABLE = "diamond_inventory"
CHAT_HISTORY_TABLE = "chat_history"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# WhatsApp configuration
WHATSAPP_API_BASE_URL = "http://localhost:8080"

# Agent configuration
AGENT_MODEL = "gpt-4o"
SYSTEM_PROMPT_MAX_TOKENS = 4000
MAX_HISTORY_MESSAGES = 10