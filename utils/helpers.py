import json
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

def format_diamond_info(diamond: Dict[str, Any]) -> str:
    """Format diamond information for customer-friendly display.
    
    Args:
        diamond: Dictionary containing diamond attributes
        
    Returns:
        Formatted string with diamond information
    """
    # Ensure all expected fields exist
    fields = {
        "id": diamond.get("id", "Unknown ID"),
        "carat": diamond.get("carat", 0),
        "cut": diamond.get("cut", "Unknown"),
        "color": diamond.get("color", "Unknown"),
        "clarity": diamond.get("clarity", "Unknown"),
        "shape": diamond.get("shape", "Round"),
        "price": diamond.get("price", 0),
        "certificate": diamond.get("certificate", "None"),
    }
    
    # Format the price with commas
    price_formatted = f"${fields['price']:,.2f}" if fields['price'] else "Price not available"
    
    # Create the formatted string
    formatted = f"Diamond #{fields['id']}:\n"
    formatted += f"• {fields['carat']} carat {fields['shape']}\n"
    formatted += f"• Cut: {fields['cut']}\n"
    formatted += f"• Color: {fields['color']}\n"
    formatted += f"• Clarity: {fields['clarity']}\n"
    formatted += f"• Price: {price_formatted}\n"
    
    if fields['certificate'] and fields['certificate'] != "None":
        formatted += f"• Certificate: {fields['certificate']}\n"
    
    return formatted

def format_diamond_list(diamonds: List[Dict[str, Any]]) -> str:
    """Format a list of diamonds for customer-friendly display.
    
    Args:
        diamonds: List of dictionaries containing diamond attributes
        
    Returns:
        Formatted string with list of diamonds
    """
    if not diamonds:
        return "No diamonds found matching your criteria."
    
    formatted = f"Found {len(diamonds)} diamonds matching your criteria:\n\n"
    
    for i, diamond in enumerate(diamonds, 1):
        # Format price with commas
        price = diamond.get("price", 0)
        price_formatted = f"${price:,.2f}" if price else "Price not available"
        
        # Create a short summary for each diamond
        formatted += f"{i}. {diamond.get('carat', 0)} carat {diamond.get('shape', 'Round')}, "
        formatted += f"{diamond.get('color', 'Unknown')} color, {diamond.get('clarity', 'Unknown')} clarity, "
        formatted += f"{price_formatted} (ID: {diamond.get('id', 'Unknown')})\n"
    
    formatted += "\nWould you like more details about any of these diamonds?"
    
    return formatted

def extract_diamond_id(message: str) -> Optional[str]:
    """Extract a diamond ID from a customer message.
    
    Args:
        message: Customer message text
        
    Returns:
        Diamond ID if found, None otherwise
    """
    # Look for patterns like "Diamond #12345" or "ID: 12345" or just "#12345"
    patterns = [
        r"Diamond #(\w+)",
        r"ID: (\w+)",
        r"#(\w+)",
        r"diamond (\w+)",
        r"number (\w+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def parse_budget_range(message: str) -> Optional[Dict[str, float]]:
    """Parse a budget range from a customer message.
    
    Args:
        message: Customer message text
        
    Returns:
        Dictionary with min and max budget if found, None otherwise
    """
    # Look for patterns like "$5,000 to $10,000" or "between $5k and $10k"
    range_patterns = [
        r"\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:to|-|and)\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
        r"between\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:to|-|and)\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)"
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            min_budget = float(match.group(1).replace(',', ''))
            max_budget = float(match.group(2).replace(',', ''))
            return {"min": min_budget, "max": max_budget}
    
    # Look for patterns like "under $5,000" or "less than $5k"
    under_patterns = [
        r"(?:under|less than|below|not more than)\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
        r"(?:max|maximum|up to)\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)"
    ]
    
    for pattern in under_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            max_budget = float(match.group(1).replace(',', ''))
            return {"min": 0, "max": max_budget}
    
    # Look for patterns like "at least $5,000" or "minimum $5k"
    over_patterns = [
        r"(?:at least|minimum|more than|over|above)\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)"
    ]
    
    for pattern in over_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            min_budget = float(match.group(1).replace(',', ''))
            return {"min": min_budget, "max": 1000000}  # Set a high upper bound
    
    # Look for a single price point
    single_pattern = r"\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)"
    match = re.search(single_pattern, message)
    if match:
        budget = float(match.group(1).replace(',', ''))
        # Create a range around the single value
        return {"min": budget * 0.8, "max": budget * 1.2}
    
    return None

def generate_chat_id(phone_number: str) -> str:
    """Generate a unique chat ID from a phone number.
    
    Args:
        phone_number: Customer's phone number
        
    Returns:
        Unique chat ID
    """
    # Remove any non-digit characters
    clean_number = re.sub(r'\D', '', phone_number)
    
    # Ensure it has a standard format
    if not clean_number.startswith("1") and len(clean_number) == 10:
        clean_number = "1" + clean_number
    
    return clean_number

def format_timestamp(timestamp: Optional[str] = None) -> str:
    """Format a timestamp for database storage.
    
    Args:
        timestamp: Optional timestamp string
        
    Returns:
        Formatted timestamp string
    """
    if timestamp:
        return timestamp
    
    # Generate current timestamp in ISO format
    return datetime.now().isoformat()