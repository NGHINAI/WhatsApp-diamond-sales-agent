from typing import Dict, Any, List, Optional
from langchain.tools import Tool
from pydantic import BaseModel, Field
import json
import re
from database.queries import DiamondQueries

# Tool input/output schemas
class SearchDiamondsInput(BaseModel):
    """Input for searching diamonds."""
    carat: Optional[Dict[str, float]] = Field(None, description="Carat range, e.g. {\"min\": 1.0, \"max\": 2.0}")
    color: Optional[List[str]] = Field(None, description="List of colors, e.g. [\"D\", \"E\", \"F\"]")
    clarity: Optional[List[str]] = Field(None, description="List of clarities, e.g. [\"VVS1\", \"VVS2\"]")
    cut: Optional[List[str]] = Field(None, description="List of cuts, e.g. [\"Excellent\"]")
    price: Optional[Dict[str, float]] = Field(None, description="Price range, e.g. {\"min\": 5000, \"max\": 15000}")
    shape: Optional[List[str]] = Field(None, description="List of shapes, e.g. [\"Round\", \"Princess\"]")

class GetDiamondDetailsInput(BaseModel):
    """Input for getting diamond details."""
    diamond_id: str = Field(..., description="ID of the diamond to get details for")

class RecommendDiamondsInput(BaseModel):
    """Input for recommending diamonds."""
    budget: float = Field(..., description="Maximum budget for the diamond")
    preferences: Dict[str, Any] = Field(..., description="Customer preferences for diamond attributes")

class ExtractPreferencesInput(BaseModel):
    """Input for extracting customer preferences from message."""
    message: str = Field(..., description="Customer message to extract preferences from")

# Tool implementations
async def search_diamonds(criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search for diamonds matching specific criteria."""
    return await DiamondQueries.get_diamonds_by_criteria(criteria)

async def get_diamond_details(diamond_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific diamond."""
    from database.supabase import supabase_client
    return await supabase_client.get_diamond_by_id(diamond_id)

async def recommend_diamonds(budget: float, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Recommend diamonds based on budget and preferences."""
    return await DiamondQueries.get_diamond_recommendations(budget, preferences)

async def extract_preferences(message: str) -> Dict[str, Any]:
    """Extract diamond preferences from a customer message."""
    # This is a simplified implementation - in a real system, you'd use a more
    # sophisticated NLP approach or a dedicated LLM call
    preferences = {}
    
    # Extract carat preferences
    carat_pattern = r'(\d+(?:\.\d+)?)[\s-]*carat'
    carat_matches = re.findall(carat_pattern, message, re.IGNORECASE)
    if carat_matches:
        preferences['carat'] = float(carat_matches[0])
    
    # Extract price/budget preferences
    price_pattern = r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)|\$(\d+)'
    price_matches = re.findall(price_pattern, message)
    if price_matches:
        # Take the first match and remove commas
        price_str = ''.join(price_matches[0]).replace(',', '')
        preferences['budget'] = float(price_str)
    
    # Extract color preferences
    colors = ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
    color_matches = [c for c in colors if f" {c} " in f" {message} " or f" color {c}" in f" {message} "]
    if color_matches:
        preferences['color'] = color_matches
    
    # Extract clarity preferences
    clarities = ['IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2']
    clarity_matches = [c for c in clarities if c in message.upper()]
    if clarity_matches:
        preferences['clarity'] = clarity_matches
    
    # Extract cut preferences
    cuts = ['Excellent', 'Very Good', 'Good', 'Fair', 'Poor']
    cut_matches = [c for c in cuts if c.lower() in message.lower()]
    if cut_matches:
        preferences['cut'] = cut_matches
    
    # Extract shape preferences
    shapes = ['Round', 'Princess', 'Cushion', 'Emerald', 'Oval', 'Radiant', 'Pear', 'Marquise', 'Heart']
    shape_matches = [s for s in shapes if s.lower() in message.lower()]
    if shape_matches:
        preferences['shape'] = shape_matches
    
    return preferences

# Create the tools
def get_agent_tools() -> List[Tool]:
    """Get the tools for the diamond sales agent."""
    tools = [
        Tool(
            name="search_diamonds",
            description="Search for diamonds matching specific criteria",
            func=search_diamonds,
            args_schema=SearchDiamondsInput
        ),
        Tool(
            name="get_diamond_details",
            description="Get detailed information about a specific diamond",
            func=get_diamond_details,
            args_schema=GetDiamondDetailsInput
        ),
        Tool(
            name="recommend_diamonds",
            description="Recommend diamonds based on budget and preferences",
            func=recommend_diamonds,
            args_schema=RecommendDiamondsInput
        ),
        Tool(
            name="extract_preferences",
            description="Extract diamond preferences from a customer message",
            func=extract_preferences,
            args_schema=ExtractPreferencesInput
        )
    ]
    
    return tools