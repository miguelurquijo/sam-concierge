from typing import List, Dict, Any, Optional

def format_price(price: int) -> str:
    """Format a price with periods as thousand separators and currency symbol.
    
    Args:
        price: Price value in Colombian pesos
        
    Returns:
        Formatted price string
    """
    return f"${price:,}".replace(',', '.')

def format_amenities(amenities: List[str], max_display: int = 3) -> str:
    """Format amenities for display.
    
    Args:
        amenities: List of amenity strings
        max_display: Maximum number of amenities to show
        
    Returns:
        Formatted amenities string
    """
    if not amenities:
        return ""
    
    # Use appropriate icons for common amenities
    amenity_icons = {
        "piscina": "🏊",
        "gimnasio": "🏋️",
        "gym": "🏋️",
        "parqueadero": "🚗",
        "parking": "🚗",
        "terraza": "🌇",
        "balcón": "🏙️",
        "balcon": "🏙️",
        "jardín": "🌳",
        "jardin": "🌳",
        "seguridad": "🔒",
        "vigilancia": "👮",
        "ascensor": "🛗",
        "bbq": "🍖",
        "playground": "🎯"
    }
    
    formatted_amenities = []
    for amenity in amenities[:max_display]:
        # Look for a matching icon, defaulting to bullet point
        icon = "•"
        for key, value in amenity_icons.items():
            if key.lower() in amenity.lower():
                icon = value
                break
        
        formatted_amenities.append(f"{icon} {amenity}")
    
    # Indicate if there are more amenities
    if len(amenities) > max_display:
        formatted_amenities.append(f"...y {len(amenities) - max_display} más")
    
    return ", ".join(formatted_amenities)

def format_property_card(property_data: Dict[str, Any]) -> str:
    """Format a single property into a comprehensive WhatsApp-friendly message.
    
    Args:
        property_data: Dictionary containing property information
        
    Returns:
        Formatted string for WhatsApp
    """
    try:
        # Format the price
        price_formatted = format_price(property_data['price'])
        
        # Build the property card with full details
        card = f"*{property_data['title']}*\n"
        card += f"💰 {price_formatted}\n"
        card += f"🛏️ {property_data['bedrooms']} habitaciones | 🚿 {property_data['bathrooms']} baños\n"
        card += f"📏 {property_data['area']} m² | 📍 {property_data['neighborhood']}\n"
        
        # Add amenities if available
        if 'amenities' in property_data and property_data['amenities']:
            card += f"\n✨ *Características:* {format_amenities(property_data['amenities'])}\n"
        
        # Add description
        card += f"\n{property_data['description']}\n\n"
        
        # Add call to action and link
        card += f"Ver detalles: {property_data['url']}\n"
        card += "\n¿Te gustaría agendar una visita o saber más sobre esta propiedad?"
        
        return card
    except KeyError as e:
        return f"Error: Falta información de la propiedad: {str(e)}"

def format_property_brief(property_data: Dict[str, Any], index: int = None) -> str:
    """Format a single property into a brief summary.
    
    Args:
        property_data: Dictionary containing property information
        index: Optional index number for the property
        
    Returns:
        Formatted string for a brief property listing
    """
    try:
        # Format the price
        price_formatted = format_price(property_data['price'])
        
        # Start with index if provided
        if index is not None:
            brief = f"*{index}. {property_data['title']}*\n"
        else:
            brief = f"*{property_data['title']}*\n"
        
        # Add key details
        brief += f"💰 {price_formatted} | 🛏️ {property_data['bedrooms']} hab | 📏 {property_data['area']} m²\n"
        
        # Add neighborhood and a few words from description
        description_preview = property_data['description'].split()[:6]
        brief += f"📍 {property_data['neighborhood']} | {' '.join(description_preview)}...\n"
        
        # Add link
        brief += f"🔗 {property_data['url']}\n"
        
        return brief
    except KeyError as e:
        return f"Error: Falta información de la propiedad: {str(e)}"

def format_property_list(properties: List[Dict[str, Any]], max_properties: int = 3) -> str:
    """Format a list of properties for WhatsApp display.
    
    Args:
        properties: List of property dictionaries
        max_properties: Maximum number of properties to include
        
    Returns:
        Formatted string for WhatsApp with multiple properties
    """
    if not properties:
        return "No encontré propiedades que coincidan con tus criterios. ¿Podrías darme más detalles sobre lo que buscas?"
    
    # Get the total count before limiting
    total_count = len(properties)
    
    # Limit the number of properties
    properties = properties[:max_properties]
    
    # Start with an intro
    if total_count == 1:
        message = "Encontré esta propiedad que podría interesarte:\n\n"
    else:
        message = f"Encontré {total_count} propiedades que podrían interesarte:\n\n"
    
    # Add each property
    for i, prop in enumerate(properties, 1):
        message += format_property_brief(prop, i)
        message += "\n"
    
    # Add a note if there are more properties
    if total_count > max_properties:
        message += f"Y {total_count - max_properties} propiedades más que coinciden con tus criterios.\n\n"
    
    # Add a call to action
    message += "¿Cuál de estas propiedades te gustaría conocer mejor? También puedes decirme si buscas algo diferente."
    
    return message

def format_no_results_message(filters: Dict[str, Any] = None) -> str:
    """Format a message for when no properties match the search criteria.
    
    Args:
        filters: Dictionary of filters that were applied (if available)
        
    Returns:
        Formatted response suggesting alternatives
    """
    message = "No encontré propiedades que coincidan exactamente con tus criterios. "
    
    if filters and filters.get('max_price'):
        message += "Podría ser que el rango de precio sea muy específico. "
    
    if filters and filters.get('neighborhoods'):
        message += f"No tenemos muchas propiedades disponibles en {', '.join(filters['neighborhoods'])} actualmente. "
    
    message += "\n\n¿Podrías ajustar alguno de estos criterios o contarme más sobre lo que buscas?"
    
    return message

def format_filter_summary(filters: Dict[str, Any]) -> str:
    """Format a summary of the filters extracted from user query.
    
    Args:
        filters: Dictionary of extracted filters
        
    Returns:
        Human-readable summary of the search filters
    """
    if not filters:
        return "Estoy buscando propiedades según tus preferencias."
    
    summary = "Estoy buscando propiedades con las siguientes características:\n"
    
    if 'property_type' in filters:
        summary += f"• Tipo: {filters['property_type'].capitalize()}\n"
    
    if 'neighborhoods' in filters:
        neighborhoods = [n.capitalize() for n in filters['neighborhoods']]
        summary += f"• Ubicación: {', '.join(neighborhoods)}\n"
    
    if 'min_price' in filters and 'max_price' in filters:
        min_price = format_price(filters['min_price'])
        max_price = format_price(filters['max_price'])
        summary += f"• Precio: Entre {min_price} y {max_price}\n"
    elif 'max_price' in filters:
        max_price = format_price(filters['max_price'])
        summary += f"• Precio máximo: {max_price}\n"
    
    if 'min_bedrooms' in filters:
        summary += f"• Habitaciones: {filters['min_bedrooms']}+\n"
    
    if 'min_bathrooms' in filters:
        summary += f"• Baños: {filters['min_bathrooms']}+\n"
    
    if 'min_area' in filters:
        summary += f"• Área mínima: {filters['min_area']} m²\n"
    
    if 'amenities' in filters:
        amenities = [a.capitalize() for a in filters['amenities']]
        summary += f"• Características: {', '.join(amenities)}\n"
    
    return summary

def format_viewing_request(property_id: str, contact_info: Optional[str] = None) -> str:
    """Format a message for scheduling a property viewing.
    
    Args:
        property_id: ID of the property to view
        contact_info: Optional contact information from the user
        
    Returns:
        Formatted viewing request message
    """
    message = f"¡Perfecto! Para agendar una visita a la propiedad (ID: {property_id}), "
    
    if contact_info:
        message += f"utilizaré tu información de contacto ({contact_info}). "
    else:
        message += "necesitaré algunos datos adicionales. "
    
    message += "\n\nUn asesor de LaHaus se pondrá en contacto contigo en las próximas 24 horas para coordinar la visita. "
    message += "También puedes contactarnos directamente al +57 300 123 4567 si prefieres una respuesta más rápida."
    
    return message

def format_whatsapp_message(message: str) -> str:
    """Format any message for WhatsApp display, handling length limitations.
    
    Args:
        message: The message to format
        
    Returns:
        A WhatsApp-friendly formatted message
    """
    # WhatsApp has a character limit, so we'll truncate if necessary
    MAX_LENGTH = 4096
    
    if len(message) > MAX_LENGTH:
        # Truncate and add an indicator
        return message[:MAX_LENGTH-100] + "\n\n... [Mensaje truncado debido a limitaciones de longitud]"
    
    return message

def format_welcome_message() -> str:
    """Format a welcome message for new users.
    
    Returns:
        Formatted welcome message
    """
    message = "¡Hola! Soy Karol, tu asistente virtual de LaHaus 🏡\n\n"
    message += "Puedo ayudarte a encontrar la propiedad perfecta según tus necesidades. "
    message += "Cuéntame qué tipo de inmueble estás buscando:\n\n"
    message += "• ¿En qué zona o barrio te gustaría vivir?\n"
    message += "• ¿Cuál es tu presupuesto?\n"
    message += "• ¿Cuántas habitaciones y baños necesitas?\n"
    message += "• ¿Buscas alguna característica especial? (gimnasio, piscina, etc.)\n\n"
    message += "Por ejemplo, puedes decirme: \"Busco un apartamento en Chapinero con 2 habitaciones y un presupuesto de 450 millones de pesos\""
    
    return message