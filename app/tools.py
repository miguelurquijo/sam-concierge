from typing import Dict, List, Any
from langchain.tools import BaseTool
from loguru import logger

from .search import create_property_search_tool, get_property_by_id

def create_lahaus_tools() -> List[BaseTool]:
    """Create and return a list of LangChain tools for the LaHaus Concierge agent.
    
    Returns:
        List of LangChain tool objects
    """
    try:
        # Create property search tool
        property_search_tool = create_property_search_tool()
        
        # In the future, additional tools can be added here, such as:
        # - Schedule viewing tool
        # - Get property details tool
        # - Connect with agent tool
        # - Property comparison tool
        # - Location information tool
        
        # Return list of tools
        return [property_search_tool]
    
    except Exception as e:
        logger.error(f"Error creating LaHaus tools: {str(e)}")
        # Return minimal tool set in case of error
        return [create_property_search_tool()]

def get_property_details(property_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific property.
    
    This is a wrapper around get_property_by_id that could be expanded
    to include more specific property information in the future.
    
    Args:
        property_id: The ID of the property to retrieve
        
    Returns:
        Property dictionary if found, otherwise None
    """
    return get_property_by_id(property_id)