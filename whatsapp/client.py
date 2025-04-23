import requests
import json
from typing import Dict, Any, List, Optional, Callable
import asyncio
import google.generativeai as genai
from config.config import WHATSAPP_API_BASE_URL, GEMINI_API_KEY
from database.queries import ChatHistoryQueries

class GeminiHandler:
    """Handler for Gemini AI responses."""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def __call__(self, chat_id: str, message: str) -> str:
        """Generate AI response using Gemini.

        Args:
            chat_id: Chat ID
            message: User message

        Returns:
            Generated response
        """
        try:
            response = await self.model.generate_content_async(message)
            return response.text
        except Exception as e:
            import logging
            logging.error(f"Error generating Gemini response: {e}", exc_info=True)
            return "Sorry, I'm having trouble generating a response right now."


class WhatsAppClient:
    """Client for interacting with WhatsApp MCP server."""
    
    def __init__(self, api_base_url: str = WHATSAPP_API_BASE_URL):
        """Initialize WhatsApp client.
        
        Args:
            api_base_url: Base URL for WhatsApp MCP server API
        """
        self.api_base_url = api_base_url
        self.message_handlers: List[Callable] = []
        self.register_message_handler(GeminiHandler())
    
    def register_message_handler(self, handler: Callable):
        """Register a function to handle incoming messages.
        
        Args:
            handler: Async function that takes (chat_id, message) and returns response
        """
        self.message_handlers.append(handler)
    
    async def send_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Send a message to a WhatsApp chat.
        
        Args:
            chat_id: Chat ID (phone number with country code)
            message: Text message to send
            
        Returns:
            Response from WhatsApp API
        """
        endpoint = f"{self.api_base_url}/send_message"
        payload = {
            "chat_id": chat_id,
            "message": message
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(endpoint, json=payload)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            import logging
            logging.error(f"Error sending WhatsApp message: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def listen_for_messages(self, polling_interval: int = 5):
        """Listen for incoming WhatsApp messages.
        
        Args:
            polling_interval: Seconds between polling for new messages
        """
        print(f"Starting WhatsApp message listener with {len(self.message_handlers)} handlers")
        last_message_id = None
        
        while True:
            try:
                # Poll for new messages
                endpoint = f"{self.api_base_url}/list_messages"
                params = {}
                if last_message_id:
                    params["after_id"] = last_message_id
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.get(endpoint, params=params)
                )
                response.raise_for_status()
                messages = response.json().get("messages", [])
                
                if messages:
                    # Update last message ID
                    last_message_id = messages[-1].get("id")
                    
                    # Process each message
                    for message in messages:
                        chat_id = message.get("chat_id")
                        sender = message.get("sender")
                        content = message.get("content")
                        
                        # Skip messages from the agent itself
                        if sender == "self":
                            continue
                        
                        # Process message with all registered handlers
                        for handler in self.message_handlers:
                            try:
                                response = await handler(chat_id, content)
                                if response:
                                    # Send response back to WhatsApp
                                    await self.send_message(chat_id, response)
                                    
                                    # Save conversation to database
                                    await ChatHistoryQueries.save_conversation(
                                        chat_id=chat_id,
                                        user_message=content,
                                        agent_response=response
                                    )
                            except Exception as e:
                                import logging
                                logging.error(f"Error in message handler: {e}", exc_info=True)
            
            except Exception as e:
                import logging
                logging.error(f"Error polling for WhatsApp messages: {e}", exc_info=True)
            
            # Wait before polling again
            await asyncio.sleep(polling_interval)
    
    async def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific chat.
        
        Args:
            chat_id: Chat ID to get info for
            
        Returns:
            Chat information or None if not found
        """
        endpoint = f"{self.api_base_url}/get_chat"
        params = {"chat_id": chat_id}
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(endpoint, params=params)
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            import logging
            logging.error(f"Error getting chat info: {e}", exc_info=True)
            return None

# Singleton instance
whatsapp_client = WhatsAppClient()