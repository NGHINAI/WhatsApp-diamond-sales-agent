import asyncio
import asyncpg
from supabase import create_client, Client
from typing import Dict, List, Any, Optional
from config.config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    DIAMOND_INVENTORY_TABLE,
    CHAT_HISTORY_TABLE
)

class SupabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.pg_conn = None
    
    async def connect_postgres(self):
        """Connect directly to PostgreSQL for more complex queries."""
        if not self.pg_conn:
            # Extract connection details from Supabase URL
            # This is a simplified example - in production, you'd use proper connection params
            conn_str = f"postgresql://postgres:{SUPABASE_SERVICE_ROLE_KEY}@db.{SUPABASE_URL.split('//')[1]}/postgres"
            self.pg_conn = await asyncpg.connect(conn_str)
        return self.pg_conn
    
    async def close_postgres(self):
        """Close PostgreSQL connection."""
        if self.pg_conn:
            await self.pg_conn.close()
            self.pg_conn = None
    
    # Diamond inventory methods
    async def get_diamonds(self, filters: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get diamonds from inventory with optional filters."""
        query = self.supabase.table(DIAMOND_INVENTORY_TABLE).select("*")
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    # Handle range filters
                    if 'min' in value:
                        query = query.gte(key, value['min'])
                    if 'max' in value:
                        query = query.lte(key, value['max'])
                else:
                    query = query.eq(key, value)
        
        response = query.limit(limit).execute()
        return response.data
    
    async def get_diamond_by_id(self, diamond_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific diamond by ID."""
        response = self.supabase.table(DIAMOND_INVENTORY_TABLE).select("*").eq("id", diamond_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    async def search_diamonds(self, query: str) -> List[Dict[str, Any]]:
        """Search diamonds using full-text search."""
        conn = await self.connect_postgres()
        try:
            # This assumes you have a proper full-text search setup in your database
            # Adjust the query based on your actual schema
            sql = f"""
            SELECT * FROM {DIAMOND_INVENTORY_TABLE}
            WHERE to_tsvector('english', description || ' ' || COALESCE(attributes::text, ''))
            @@ plainto_tsquery('english', $1)
            LIMIT 10
            """
            rows = await conn.fetch(sql, query)
            return [dict(row) for row in rows]
        finally:
            await self.close_postgres()
    
    # Chat history methods
    async def save_message(self, chat_id: str, sender: str, message: str, timestamp=None) -> Dict[str, Any]:
        """Save a message to chat history."""
        data = {
            "chat_id": chat_id,
            "sender": sender,
            "message": message,
            "timestamp": timestamp or "now()"
        }
        response = self.supabase.table(CHAT_HISTORY_TABLE).insert(data).execute()
        return response.data[0] if response.data else None
    
    async def get_chat_history(self, chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chat history for a specific chat."""
        response = self.supabase.table(CHAT_HISTORY_TABLE)\
            .select("*")\
            .eq("chat_id", chat_id)\
            .order("timestamp", desc=False)\
            .limit(limit)\
            .execute()
        return response.data

# Singleton instance
supabase_client = SupabaseClient()