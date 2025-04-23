from typing import Dict, List, Any, Optional, Tuple
import json
from database.supabase import supabase_client
from config.config import DIAMOND_INVENTORY_TABLE, CHAT_HISTORY_TABLE

class DiamondQueries:
    """SQL queries for diamond inventory."""
    
    @staticmethod
    async def get_diamonds_by_criteria(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get diamonds matching specific criteria.
        
        Args:
            criteria: Dictionary of filter criteria like:
                {
                    "carat": {"min": 1.0, "max": 2.0},
                    "color": ["D", "E", "F"],
                    "clarity": ["VVS1", "VVS2"],
                    "cut": ["Excellent"],
                    "price": {"min": 5000, "max": 15000}
                }
        
        Returns:
            List of matching diamonds
        """
        # Connect to PostgreSQL for more complex query
        conn = await supabase_client.connect_postgres()
        try:
            # Build dynamic query based on criteria
            conditions = []
            params = {}
            param_idx = 1
            
            for key, value in criteria.items():
                if isinstance(value, dict):
                    # Handle range filters
                    if 'min' in value:
                        conditions.append(f"{key} >= ${param_idx}")
                        params[str(param_idx)] = value['min']
                        param_idx += 1
                    if 'max' in value:
                        conditions.append(f"{key} <= ${param_idx}")
                        params[str(param_idx)] = value['max']
                        param_idx += 1
                elif isinstance(value, list):
                    # Handle list of values (IN operator)
                    placeholders = [f"${param_idx + i}" for i in range(len(value))]
                    conditions.append(f"{key} IN ({', '.join(placeholders)})")
                    for i, val in enumerate(value):
                        params[str(param_idx + i)] = val
                    param_idx += len(value)
                else:
                    # Handle exact match
                    conditions.append(f"{key} = ${param_idx}")
                    params[str(param_idx)] = value
                    param_idx += 1
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            query = f"""
            SELECT * FROM {DIAMOND_INVENTORY_TABLE}
            WHERE {where_clause}
            ORDER BY price ASC
            LIMIT 10
            """
            
            # Execute query with parameters
            rows = await conn.fetch(query, *[params[str(i)] for i in range(1, param_idx)])
            return [dict(row) for row in rows]
        finally:
            await supabase_client.close_postgres()
    
    @staticmethod
    async def search_diamonds_by_text(search_text: str) -> List[Dict[str, Any]]:
        """Search diamonds using full-text search.
        
        Args:
            search_text: Text to search for in diamond descriptions and attributes
            
        Returns:
            List of matching diamonds
        """
        return await supabase_client.search_diamonds(search_text)
    
    @staticmethod
    async def get_diamond_recommendations(budget: float, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get diamond recommendations based on budget and preferences.
        
        Args:
            budget: Maximum price
            preferences: Dictionary of preferences like cut, color, etc.
            
        Returns:
            List of recommended diamonds
        """
        conn = await supabase_client.connect_postgres()
        try:
            # Build a scoring query that ranks diamonds based on preferences
            score_components = []
            conditions = [f"price <= ${1}"]
            params = [budget]
            param_idx = 2
            
            for key, value in preferences.items():
                if key in ['cut', 'color', 'clarity']:
                    if isinstance(value, list):
                        placeholders = [f"${param_idx + i}" for i in range(len(value))]
                        conditions.append(f"{key} IN ({', '.join(placeholders)})")
                        for i, val in enumerate(value):
                            params.append(val)
                        param_idx += len(value)
                        # Add to score - preferred attributes get higher score
                        score_components.append(f"CASE WHEN {key} IN ({', '.join(placeholders)}) THEN 10 ELSE 0 END")
                    else:
                        conditions.append(f"{key} = ${param_idx}")
                        params.append(value)
                        param_idx += 1
                        # Add to score - preferred attributes get higher score
                        score_components.append(f"CASE WHEN {key} = ${param_idx-1} THEN 10 ELSE 0 END")
            
            # Add carat preference to score if provided
            if 'carat' in preferences:
                target_carat = preferences['carat']
                params.append(target_carat)
                # Score based on how close to target carat
                score_components.append(f"(10 - ABS(carat - ${param_idx}))")
                param_idx += 1
            
            # Combine all score components
            score_expr = " + ".join(score_components) if score_components else "0"
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
            SELECT *, ({score_expr}) AS match_score 
            FROM {DIAMOND_INVENTORY_TABLE}
            WHERE {where_clause}
            ORDER BY match_score DESC, price ASC
            LIMIT 5
            """
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
        finally:
            await supabase_client.close_postgres()


class ChatHistoryQueries:
    """SQL queries for chat history."""
    
    @staticmethod
    async def save_conversation(chat_id: str, user_message: str, agent_response: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Save both user message and agent response to chat history.
        
        Args:
            chat_id: Unique identifier for the chat (typically phone number)
            user_message: Message from the user
            agent_response: Response from the agent
            
        Returns:
            Tuple of (user_message_record, agent_response_record)
        """
        # Save user message
        user_record = await supabase_client.save_message(
            chat_id=chat_id,
            sender="user",
            message=user_message
        )
        
        # Save agent response
        agent_record = await supabase_client.save_message(
            chat_id=chat_id,
            sender="agent",
            message=agent_response
        )
        
        return user_record, agent_record
    
    @staticmethod
    async def get_recent_conversation(chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for a chat.
        
        Args:
            chat_id: Unique identifier for the chat
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message records in chronological order
        """
        return await supabase_client.get_chat_history(chat_id, limit)
    
    @staticmethod
    async def get_conversation_summary(chat_id: str) -> str:
        """Generate a summary of the conversation.
        
        Args:
            chat_id: Unique identifier for the chat
            
        Returns:
            Summary text of the conversation
        """
        conn = await supabase_client.connect_postgres()
        try:
            query = f"""
            WITH user_interests AS (
                SELECT 
                    DISTINCT jsonb_array_elements_text(
                        jsonb_path_query_array(to_jsonb(message), '$."diamond_attributes"[*]')
                    ) as interest
                FROM {CHAT_HISTORY_TABLE}
                WHERE chat_id = $1 AND sender = 'user'
            )
            SELECT string_agg(interest, ', ') as interests FROM user_interests
            """
            
            result = await conn.fetchval(query, chat_id)
            if result:
                return f"User has expressed interest in diamonds with: {result}"
            return "No specific interests detected yet."
        except Exception as e:
            import logging
            logging.error(f"Error generating conversation summary: {e}", exc_info=True)
            return "Unable to generate conversation summary."
        finally:
            await supabase_client.close_postgres()