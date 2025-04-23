import asyncio
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import components
from whatsapp.client import whatsapp_client
from agent.agent import diamond_agent
from database.supabase import supabase_client

async def main():
    """Main application entry point."""
    try:
        logger.info("Starting WhatsApp Diamond Sales AI Agent")
        
        # Register message handler
        whatsapp_client.register_message_handler(diamond_agent.handle_message)
        
        # Start listening for WhatsApp messages
        logger.info("Listening for WhatsApp messages...")
        await whatsapp_client.listen_for_messages()
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
    finally:
        # Clean up resources
        await supabase_client.close_postgres()
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    # Run the main application
    asyncio.run(main())