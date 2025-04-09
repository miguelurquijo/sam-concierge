from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import re
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger

from .templates import format_property_list
from .config import DEFAULT_SEARCH_LIMIT

class PropertySearchInput(BaseModel):
    """Input for the property search tool."""
    query: str = Field(
        description="A natural language description of what the user is looking for in a property"
    )
    max_results: Optional[int] = Field(
        default=5,
        description="Maximum number of results to return"
    )

class PropertySearchOutput(BaseModel):
    """Output for the property search tool."""
    formatted_results: str = Field(
        description="Formatted string with property results"
    )
    properties: List[Dict[str, Any]] = Field(
        description="List of property dictionaries"
    )
    total_matches: int = Field(
        description="Total number of matching properties"
    )

def extract_filters(query: str) -> Dict[str, Any]:
    """Extract explicit filter criteria from a natural language query.
    
    This function extracts various property attributes like:
    - price range (min/max)
    - number of bedrooms/bathrooms
    - neighborhoods/locations
    - property type (apartment, house)
    - amenities
    
    Args:
        query: Natural language query from user
        
    Returns:
        Dictionary of extracted filters
    """
    filters = {}
    
    # Normalize query - lowercase and remove accents for simpler regex matching
    normalized_query = query.lower()
    
    # Extract price information
    price_match = re.search(r'(\d+[\d.,]*)\s*(?:millones|millon|m)(?:\s*de pesos)?', normalized_query)
    if price_match:
        price_str = price_match.group(1).replace('.', '').replace(',', '')
        # Convert to full number (e.g., 500 million = 500,000,000)
        filters['max_price'] = int(float(price_str) * 1_000_000)
    
    price_range_match = re.search(r'entre\s*(\d+[\d.,]*)\s*y\s*(\d+[\d.,]*)\s*(?:millones|millon|m)', normalized_query)
    if price_range_match:
        min_price_str = price_range_match.group(1).replace('.', '').replace(',', '')
        max_price_str = price_range_match.group(2).replace('.', '').replace(',', '')
        filters['min_price'] = int(float(min_price_str) * 1_000_000)
        filters['max_price'] = int(float(max_price_str) * 1_000_000)
    
    # Extract bedrooms
    bedrooms_match = re.search(r'(\d+)\s*(?:habitaciones|hab|habitación|cuartos|recámaras)', normalized_query)
    if bedrooms_match:
        filters['min_bedrooms'] = int(bedrooms_match.group(1))
    
    # Extract bathrooms
    bathrooms_match = re.search(r'(\d+)\s*(?:baños|baño)', normalized_query)
    if bathrooms_match:
        filters['min_bathrooms'] = int(bathrooms_match.group(1))
    
    # Extract area (m²)
    area_match = re.search(r'(\d+)\s*(?:m2|metros cuadrados|metros|m²)', normalized_query)
    if area_match:
        filters['min_area'] = int(area_match.group(1))
    
    # Extract property type
    if re.search(r'\b(?:apartamento|apto|apartamentos)\b', normalized_query):
        filters['property_type'] = 'apartamento'
    elif re.search(r'\b(?:casa|casas)\b', normalized_query):
        filters['property_type'] = 'casa'
    
    # Extract common neighborhoods in Bogotá and Medellín
    neighborhoods = [
        'chapinero', 'usaquen', 'chico', 'cedritos', 'salitre', 
        'poblado', 'laureles', 'envigado', 'sabaneta', 'belen',
        'estadio', 'itagui', 'caldas', 'estrella', 'robledo',
        'santa barbara', 'rosales', 'teusaquillo', 'suba', 'bosa',
        'kennedy', 'candelaria', 'fontibon'
    ]
    
    found_neighborhoods = []
    for neighborhood in neighborhoods:
        if neighborhood in normalized_query:
            found_neighborhoods.append(neighborhood)
    
    if found_neighborhoods:
        filters['neighborhoods'] = found_neighborhoods
    
    # Extract amenities
    amenities = [
        'piscina', 'gimnasio', 'gym', 'parqueadero', 'parking', 
        'terraza', 'balcón', 'balcon', 'jardín', 'jardin', 
        'seguridad', 'vigilancia', 'ascensor', 'bbq', 'playground'
    ]
    
    found_amenities = []
    for amenity in amenities:
        if amenity in normalized_query:
            found_amenities.append(amenity)
    
    if found_amenities:
        filters['amenities'] = found_amenities
    
    logger.info(f"Extracted filters: {filters}")
    return filters

def apply_filters(properties: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply extracted filters to the property list.
    
    Args:
        properties: List of property dictionaries
        filters: Dictionary of filters to apply
        
    Returns:
        Filtered list of properties
    """
    filtered_properties = properties.copy()
    
    # Apply price filters
    if 'min_price' in filters:
        filtered_properties = [p for p in filtered_properties if p['price'] >= filters['min_price']]
    if 'max_price' in filters:
        filtered_properties = [p for p in filtered_properties if p['price'] <= filters['max_price']]
    
    # Apply bedroom filters
    if 'min_bedrooms' in filters:
        filtered_properties = [p for p in filtered_properties if p['bedrooms'] >= filters['min_bedrooms']]
    
    # Apply bathroom filters
    if 'min_bathrooms' in filters:
        filtered_properties = [p for p in filtered_properties if p['bathrooms'] >= filters['min_bathrooms']]
    
    # Apply area filters
    if 'min_area' in filters:
        filtered_properties = [p for p in filtered_properties if p['area'] >= filters['min_area']]
    
    # Apply neighborhood filters
    if 'neighborhoods' in filters:
        # Case-insensitive check for any of the specified neighborhoods
        neighborhood_properties = []
        for p in filtered_properties:
            for neighborhood in filters['neighborhoods']:
                if neighborhood.lower() in p['neighborhood'].lower():
                    neighborhood_properties.append(p)
                    break
        filtered_properties = neighborhood_properties
    
    # Apply property type filter
    if 'property_type' in filters:
        property_type = filters['property_type']
        filtered_properties = [p for p in filtered_properties if property_type.lower() in p['title'].lower()]
    
    # Apply amenities filter if present in property data
    if 'amenities' in filters:
        amenity_properties = []
        for p in filtered_properties:
            if 'amenities' in p:
                # Check if any requested amenity is in the property's amenities
                if any(amenity in [a.lower() for a in p['amenities']] for amenity in filters['amenities']):
                    amenity_properties.append(p)
        
        # Only filter if we found properties with matching amenities
        if amenity_properties:
            filtered_properties = amenity_properties
    
    logger.info(f"Filtering reduced properties from {len(properties)} to {len(filtered_properties)}")
    return filtered_properties

def rank_properties(properties: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Rank properties based on relevance to query.
    
    In a real implementation, this would use embeddings for semantic similarity.
    For now, we'll use a simple keyword matching approach.
    
    Args:
        properties: List of property dictionaries
        query: User's search query
        
    Returns:
        Ranked list of properties
    """
    # If we have fewer than 2 properties, no need to rank
    if len(properties) < 2:
        return properties
    
    # Simple ranking using keyword occurrence
    query_words = set(query.lower().split())
    
    # Calculate a relevance score for each property
    for prop in properties:
        # Combine all textual fields for matching
        property_text = f"{prop['title']} {prop['neighborhood']} {prop['description']}".lower()
        
        # Count matching words
        matching_words = sum(1 for word in query_words if word in property_text)
        
        # Calculate a basic score
        prop['_score'] = matching_words / len(query_words) if query_words else 0
        
        # Boost scores for exact neighborhood matches
        for word in query_words:
            if word in prop['neighborhood'].lower():
                prop['_score'] += 0.5
        
        # Boost scores for properties with more amenities
        if 'amenities' in prop:
            prop['_score'] += min(len(prop['amenities']) * 0.1, 0.5)  # Cap the boost
    
    # Sort by score (descending)
    ranked_properties = sorted(properties, key=lambda p: p.get('_score', 0), reverse=True)
    
    return ranked_properties

def create_property_search_tool():
    """Create a LangChain tool for searching properties with filter extraction and ranking."""
    
    @tool
    def search_properties(query: str, max_results: int = 5) -> str:
        """Search for properties that match the given criteria.
        
        Args:
            query: A natural language description of what the user is looking for in a property,
                   such as 'apartments in Chapinero with 2 bedrooms under 500 million pesos'
            max_results: Maximum number of results to return
            
        Returns:
            A string with information about matching properties
        """
        try:
            # 1. Load property data
            sample_data_path = os.path.join('data', 'sample_properties.json')
            
            if os.path.exists(sample_data_path):
                with open(sample_data_path, 'r', encoding='utf-8') as f:
                    properties = json.load(f)
            else:
                # Fallback to minimal sample data
                properties = [
                    {
                        "id": "prop1",
                        "title": "Apartamento en Chapinero",
                        "price": 450000000,
                        "bedrooms": 2,
                        "bathrooms": 2,
                        "area": 75,
                        "neighborhood": "Chapinero",
                        "description": "Hermoso apartamento en Chapinero con vista a la ciudad",
                        "url": "https://lahaus.com/properties/prop1",
                        "amenities": ["Gimnasio", "Piscina", "Seguridad 24h"]
                    },
                    {
                        "id": "prop2",
                        "title": "Casa en Usaquén",
                        "price": 950000000,
                        "bedrooms": 3,
                        "bathrooms": 3,
                        "area": 150,
                        "neighborhood": "Usaquén",
                        "description": "Amplia casa con jardín en zona exclusiva de Usaquén",
                        "url": "https://lahaus.com/properties/prop2",
                        "amenities": ["Jardín", "Parqueadero", "Seguridad 24h"]
                    }
                ]
            
            # 2. Extract filters from the query
            filters = extract_filters(query)
            
            # 3. Apply filters to narrow down properties
            filtered_properties = apply_filters(properties, filters)
            
            # 4. Rank the results by relevance
            ranked_properties = rank_properties(filtered_properties, query)
            
            # 5. Limit the number of results
            results = ranked_properties[:min(max_results, len(ranked_properties))]
            
            # 6. Format the results using the template
            formatted_response = format_property_list(results, max_results)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error in property search: {str(e)}")
            return "Lo siento, hubo un problema al buscar propiedades. Por favor intenta de nuevo."
    
    return search_properties

# Function to get property by ID (useful for follow-up questions)
def get_property_by_id(property_id: str) -> Dict[str, Any]:
    """Retrieve a property by its ID.
    
    Args:
        property_id: The ID of the property to retrieve
        
    Returns:
        Property dictionary if found, otherwise None
    """
    try:
        sample_data_path = os.path.join('data', 'sample_properties.json')
        
        if os.path.exists(sample_data_path):
            with open(sample_data_path, 'r', encoding='utf-8') as f:
                properties = json.load(f)
                
                for prop in properties:
                    if prop['id'] == property_id:
                        return prop
        
        return None
    
    except Exception as e:
        logger.error(f"Error retrieving property by ID: {str(e)}")
        return None