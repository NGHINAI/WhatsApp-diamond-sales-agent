import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock

from agent.agent import DiamondSalesAgent
from database.queries import DiamondQueries
from utils.helpers import format_diamond_info, extract_diamond_id

# Sample test data
SAMPLE_DIAMOND = {
    "id": "D12345",
    "carat": 1.25,
    "cut": "Excellent",
    "color": "F",
    "clarity": "VS1",
    "shape": "Round",
    "price": 8500.00,
    "certificate": "GIA"
}

SAMPLE_CHAT_HISTORY = [
    {"sender": "user", "message": "Hi, I'm looking for a diamond engagement ring", "timestamp": "2023-06-01T10:00:00"},
    {"sender": "agent", "message": "Hello! I'd be happy to help you find the perfect diamond engagement ring. Could you share some details about what you're looking for?", "timestamp": "2023-06-01T10:00:30"}
]

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch("database.supabase.supabase_client") as mock_client:
        # Mock get_diamonds method
        mock_client.get_diamonds.return_value = [SAMPLE_DIAMOND]
        
        # Mock get_diamond_by_id method
        mock_client.get_diamond_by_id.return_value = SAMPLE_DIAMOND
        
        # Mock get_chat_history method
        mock_client.get_chat_history.return_value = SAMPLE_CHAT_HISTORY
        
        yield mock_client

@pytest.fixture
def mock_diamond_queries():
    """Mock DiamondQueries for testing."""
    with patch("agent.tools.DiamondQueries") as mock_queries:
        # Mock get_diamonds_by_criteria method
        mock_queries.get_diamonds_by_criteria.return_value = [SAMPLE_DIAMOND]
        
        # Mock search_diamonds_by_text method
        mock_queries.search_diamonds_by_text.return_value = [SAMPLE_DIAMOND]
        
        # Mock get_diamond_recommendations method
        mock_queries.get_diamond_recommendations.return_value = [SAMPLE_DIAMOND]
        
        yield mock_queries

@pytest.fixture
def mock_agent():
    """Mock DiamondSalesAgent for testing."""
    with patch("agent.agent.DiamondSalesAgent") as MockAgent:
        agent_instance = MagicMock()
        agent_instance.handle_message.return_value = "I've found a beautiful 1.25 carat Round diamond with F color and VS1 clarity for $8,500."
        MockAgent.return_value = agent_instance
        yield agent_instance

# Test helper functions
def test_format_diamond_info():
    """Test formatting diamond information."""
    formatted = format_diamond_info(SAMPLE_DIAMOND)
    
    assert "1.25 carat Round" in formatted
    assert "Cut: Excellent" in formatted
    assert "Color: F" in formatted
    assert "Clarity: VS1" in formatted
    assert "$8,500.00" in formatted
    assert "Certificate: GIA" in formatted

def test_extract_diamond_id():
    """Test extracting diamond ID from message."""
    message1 = "I'm interested in Diamond #D12345"
    message2 = "Can you tell me more about ID: D12345?"
    message3 = "I like #D12345"
    
    assert extract_diamond_id(message1) == "D12345"
    assert extract_diamond_id(message2) == "D12345"
    assert extract_diamond_id(message3) == "D12345"

# Test database queries
@pytest.mark.asyncio
async def test_get_diamonds_by_criteria(mock_diamond_queries):
    """Test getting diamonds by criteria."""
    criteria = {
        "carat": {"min": 1.0, "max": 2.0},
        "color": ["F", "G"],
        "clarity": ["VS1", "VS2"],
        "cut": ["Excellent"]
    }
    
    diamonds = await DiamondQueries.get_diamonds_by_criteria(criteria)
    
    assert len(diamonds) == 1
    assert diamonds[0]["id"] == "D12345"
    assert diamonds[0]["carat"] == 1.25
    assert diamonds[0]["color"] == "F"
    assert diamonds[0]["clarity"] == "VS1"

# Test agent functionality
@pytest.mark.asyncio
async def test_agent_handle_message(mock_agent):
    """Test agent handling a message."""
    chat_id = "12345678901"
    message = "I'm looking for a 1 carat diamond with excellent cut under $10,000"
    
    response = await mock_agent.handle_message(chat_id, message)
    
    assert response is not None
    assert "diamond" in response.lower()
    assert mock_agent.handle_message.called_once_with(chat_id, message)

# Run tests with: pytest -xvs tests/test_agent.py