from typing import List, Dict, Any, Optional
import re
from datetime import datetime

# ===== Formatting Utilities =====

def format_price(price: int) -> str:
    """Format a price with periods as thousand separators and currency symbol.
    
    Args:
        price: Price value in Colombian pesos
        
    Returns:
        Formatted price string
    """
    return f"${price:,}".replace(',', '.')

def format_amenities(amenities: List[str], max_display: int = 3, style: str = "list") -> str:
    """Format amenities for display with icons.
    
    Args:
        amenities: List of amenity strings
        max_display: Maximum number of amenities to show
        style: Display style ('list', 'inline', 'bullets')
        
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
        "playground": "🎯",
        "patio": "🏡",
        "cocina": "🍳",
        "lavanderia": "🧺",
        "amoblado": "🪑",
        "internet": "📶",
        "aire": "❄️",
        "calefaccion": "🔥",
        "mascotas": "🐾",
        "sala": "🛋️",
        "comedor": "🍽️"
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
        if style == "list" or style == "bullets":
            formatted_amenities.append(f"...y {len(amenities) - max_display} más")
        else:
            formatted_amenities.append(f"(+{len(amenities) - max_display} más)")
    
    if style == "list":
        return "\n".join(formatted_amenities)
    elif style == "bullets":
        return "• " + "\n• ".join([a.strip("• ") for a in formatted_amenities])
    else:  # inline
        return ", ".join(formatted_amenities)

def format_date(date_str: str, include_time: bool = False) -> str:
    """Format a date string into a user-friendly format.
    
    Args:
        date_str: Date string (ISO format)
        include_time: Whether to include time in the output
        
    Returns:
        Formatted date string
    """
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio", 
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        
        if include_time:
            return f"{date_obj.day} de {months[date_obj.month-1]} de {date_obj.year}, {date_obj.hour}:{date_obj.minute:02d}"
        else:
            return f"{date_obj.day} de {months[date_obj.month-1]} de {date_obj.year}"
    except (ValueError, TypeError):
        # Return original if invalid date
        return date_str

def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the text
        add_ellipsis: Whether to add an ellipsis at the end
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Try to truncate at a word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Only truncate at word if it's not too short
        truncated = truncated[:last_space]
    
    if add_ellipsis:
        truncated += "..."
        
    return truncated

def add_line_breaks(text: str, max_line_length: int = 40) -> str:
    """Add line breaks to text to improve readability on mobile.
    
    Args:
        text: Text to format
        max_line_length: Maximum length of each line
        
    Returns:
        Text with added line breaks
    """
    if not text or len(text) <= max_line_length:
        return text
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        
        if current_length + word_length + len(current_line) > max_line_length:
            # Start a new line
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            # Add to current line
            current_line.append(word)
            current_length += word_length
    
    # Add the last line
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)

def format_location(neighborhood: str, city: Optional[str] = None) -> str:
    """Format location information.
    
    Args:
        neighborhood: Neighborhood name
        city: Optional city name
        
    Returns:
        Formatted location string
    """
    if city and neighborhood:
        return f"📍 {neighborhood}, {city}"
    elif neighborhood:
        return f"📍 {neighborhood}"
    elif city:
        return f"📍 {city}"
    else:
        return ""

# ===== Property Templates =====

def format_property_card(property_data: Dict[str, Any], detailed: bool = False) -> str:
    """Format a single property into a comprehensive WhatsApp-friendly message.
    
    Args:
        property_data: Dictionary containing property information
        detailed: Whether to show full details
        
    Returns:
        Formatted string for WhatsApp
    """
    try:
        # Format the price
        price_formatted = format_price(property_data['price'])
        
        # Build the property card header with ID (helps for reference in conversation)
        property_id = property_data.get('id', 'N/A')
        card = f"*{property_data['title']}* (Ref: {property_id})\n"
        
        # Basic details (always included)
        card += f"💰 {price_formatted}\n"
        card += f"🛏️ {property_data['bedrooms']} habitaciones | 🚿 {property_data['bathrooms']} baños\n"
        
        # Area and location on same line
        location = format_location(property_data.get('neighborhood', ''))
        card += f"📏 {property_data['area']} m² | {location}\n"
        
        # Amenities (highlighted differently based on detail level)
        if 'amenities' in property_data and property_data['amenities']:
            if detailed:
                card += f"\n✨ *Características:*\n{format_amenities(property_data['amenities'], max_display=6, style='bullets')}\n"
            else:
                card += f"\n✨ *Características:* {format_amenities(property_data['amenities'], style='inline')}\n"
        
        # Description (truncated or full based on detail level)
        if detailed:
            # Full description with line breaks for readability
            description = add_line_breaks(property_data['description'])
            card += f"\n📝 *Descripción:*\n{description}\n"
        else:
            # Truncated description
            description = truncate_text(property_data['description'], max_length=150)
            card += f"\n{description}\n"
        
        # Additional details for detailed view
        if detailed and 'construction_year' in property_data:
            card += f"\n🏗️ *Año de construcción:* {property_data['construction_year']}\n"
        
        if detailed and 'stratum' in property_data:  # Colombian specific - "estrato"
            card += f"⭐ *Estrato:* {property_data['stratum']}\n"
            
        # Add call to action and link
        card += f"\n🔗 *Ver detalles completos:* {property_data['url']}\n"
        
        # Call to action based on detail level
        if detailed:
            card += "\n¿Te gustaría agendar una visita a esta propiedad? Puedo coordinar con un asesor para que te contacte."
        else:
            card += "\n¿Te gustaría más información sobre esta propiedad?"
        
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
        
        # Add key details on first line
        brief += f"💰 {price_formatted} | 🛏️ {property_data['bedrooms']} hab | 📏 {property_data['area']} m²\n"
        
        # Add neighborhood and a few words from description on second line
        neighborhood = property_data.get('neighborhood', 'Ubicación no especificada')
        description_preview = truncate_text(property_data['description'], max_length=70)
        brief += f"📍 {neighborhood} | {description_preview}\n"
        
        # Add amenities highlights if available (max 3, inline format)
        if 'amenities' in property_data and property_data['amenities']:
            brief += f"✨ {format_amenities(property_data['amenities'], max_display=3, style='inline')}\n"
        
        # Add link
        brief += f"🔗 {property_data['url']}\n"
        
        return brief
    except KeyError as e:
        return f"Error: Falta información de la propiedad: {str(e)}"

def format_property_comparison(properties: List[Dict[str, Any]], max_properties: int = 3) -> str:
    """Format properties side by side for comparison.
    
    Args:
        properties: List of property dictionaries
        max_properties: Maximum number of properties to include
        
    Returns:
        Formatted comparison text
    """
    if not properties or len(properties) < 2:
        return "Se necesitan al menos 2 propiedades para hacer una comparación."
    
    # Limit number of properties
    properties = properties[:max_properties]
    
    # Create header
    comparison = "*COMPARACIÓN DE PROPIEDADES*\n\n"
    
    # Headers for each property
    for i, prop in enumerate(properties, 1):
        comparison += f"*Propiedad {i}:* {prop['title']}\n"
    
    comparison += "\n"
    
    # Price comparison
    comparison += "*💰 Precio:*\n"
    for prop in properties:
        comparison += f"- {format_price(prop['price'])}\n"
    
    comparison += "\n"
    
    # Room comparison
    comparison += "*🛏️ Habitaciones:*\n"
    for prop in properties:
        comparison += f"- {prop['bedrooms']} hab\n"
    
    comparison += "\n"
    
    # Bathroom comparison
    comparison += "*🚿 Baños:*\n"
    for prop in properties:
        comparison += f"- {prop['bathrooms']} baños\n"
    
    comparison += "\n"
    
    # Area comparison
    comparison += "*📏 Área:*\n"
    for prop in properties:
        comparison += f"- {prop['area']} m²\n"
    
    comparison += "\n"
    
    # Location
    comparison += "*📍 Ubicación:*\n"
    for prop in properties:
        comparison += f"- {prop.get('neighborhood', 'No especificada')}\n"
    
    comparison += "\n"
    
    # Links
    comparison += "*🔗 Enlaces:*\n"
    for i, prop in enumerate(properties, 1):
        comparison += f"- Propiedad {i}: {prop['url']}\n"
    
    # Call to action
    comparison += "\n¿Cuál de estas propiedades te parece más interesante?"
    
    return comparison

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
        message = "✨ *He encontrado esta propiedad que podría interesarte:*\n\n"
    else:
        message = f"✨ *He encontrado {total_count} propiedades que podrían interesarte:*\n\n"
    
    # Add each property
    for i, prop in enumerate(properties, 1):
        message += format_property_brief(prop, i)
        message += "\n"
    
    # Add a note if there are more properties
    if total_count > max_properties:
        message += f"Y {total_count - max_properties} propiedades más que coinciden con tus criterios.\n\n"
    
    # Add a call to action
    message += "¿Cuál de estas propiedades te gustaría conocer mejor? Puedes pedirme más detalles de la que te interese o decirme si quieres ver otras opciones."
    
    return message

def format_property_gallery(properties: List[Dict[str, Any]], max_properties: int = 5) -> str:
    """Format a gallery-style list of properties with minimal details.
    
    Args:
        properties: List of property dictionaries
        max_properties: Maximum number of properties to include
        
    Returns:
        Formatted string for WhatsApp with a gallery of properties
    """
    if not properties:
        return "No encontré propiedades que coincidan con tus criterios. ¿Podrías darme más detalles sobre lo que buscas?"
    
    # Get the total count before limiting
    total_count = len(properties)
    
    # Limit the number of properties
    properties = properties[:max_properties]
    
    # Start with an intro
    gallery = f"*GALERÍA DE PROPIEDADES ({total_count} resultados)*\n\n"
    
    # Format each property with minimal details
    for i, prop in enumerate(properties, 1):
        price = format_price(prop['price'])
        title = prop.get('title', f"Propiedad {i}")
        area = prop.get('area', 'N/A')
        bedrooms = prop.get('bedrooms', 'N/A')
        neighborhood = prop.get('neighborhood', 'Ubicación no especificada')
        
        gallery += f"*{i}. {title}*\n"
        gallery += f"💰 {price} | 🛏️ {bedrooms} hab | 📏 {area} m² | 📍 {neighborhood}\n"
        gallery += f"🔗 {prop['url']}\n\n"
    
    # Add a note if there are more properties
    if total_count > max_properties:
        gallery += f"...y {total_count - max_properties} propiedades más disponibles.\n\n"
    
    # Add call to action
    gallery += "Puedes decirme el número de la propiedad para ver más detalles, o indicarme si quieres refinar la búsqueda."
    
    return gallery

# ===== Response Templates =====

def format_no_results_message(filters: Dict[str, Any] = None) -> str:
    """Format a message for when no properties match the search criteria.
    
    Args:
        filters: Dictionary of filters that were applied (if available)
        
    Returns:
        Formatted response suggesting alternatives
    """
    message = "🔍 No encontré propiedades que coincidan exactamente con tus criterios. "
    
    if filters:
        if filters.get('max_price'):
            message += f"El presupuesto máximo de {format_price(filters['max_price'])} podría ser restrictivo. "
        
        if filters.get('neighborhoods'):
            locations = ', '.join(n.capitalize() for n in filters['neighborhoods'])
            message += f"No tenemos muchas propiedades disponibles en {locations} actualmente. "
        
        if filters.get('min_bedrooms') and filters.get('min_bedrooms') > 2:
            message += f"Propiedades con {filters['min_bedrooms']} o más habitaciones son menos comunes. "
            
        if filters.get('amenities') and len(filters.get('amenities', [])) > 2:
            message += "Buscar múltiples características específicas reduce las opciones disponibles. "
    
    message += "\n\n¿Te gustaría ajustar alguno de estos criterios? Puedo sugerirte opciones similares si me indicas qué aspectos son más importantes para ti."
    
    return message

def format_filter_summary(filters: Dict[str, Any]) -> str:
    """Format a summary of the filters extracted from user query.
    
    Args:
        filters: Dictionary of extracted filters
        
    Returns:
        Human-readable summary of the search filters
    """
    if not filters:
        return "Estoy buscando propiedades según tus preferencias generales."
    
    summary = "🔍 *Estoy buscando propiedades con las siguientes características:*\n\n"
    
    if 'property_type' in filters:
        summary += f"• *Tipo:* {filters['property_type'].capitalize()}\n"
    
    if 'neighborhoods' in filters:
        neighborhoods = [n.capitalize() for n in filters['neighborhoods']]
        summary += f"• *Ubicación:* {', '.join(neighborhoods)}\n"
    
    if 'min_price' in filters and 'max_price' in filters:
        min_price = format_price(filters['min_price'])
        max_price = format_price(filters['max_price'])
        summary += f"• *Precio:* Entre {min_price} y {max_price}\n"
    elif 'max_price' in filters:
        max_price = format_price(filters['max_price'])
        summary += f"• *Precio máximo:* {max_price}\n"
    elif 'min_price' in filters:
        min_price = format_price(filters['min_price'])
        summary += f"• *Precio mínimo:* {min_price}\n"
    
    if 'min_bedrooms' in filters:
        summary += f"• *Habitaciones:* {filters['min_bedrooms']}+\n"
    
    if 'min_bathrooms' in filters:
        summary += f"• *Baños:* {filters['min_bathrooms']}+\n"
    
    if 'min_area' in filters:
        summary += f"• *Área mínima:* {filters['min_area']} m²\n"
    
    if 'amenities' in filters:
        amenities = [a.capitalize() for a in filters['amenities']]
        summary += f"• *Características:* {', '.join(amenities)}\n"
    
    summary += "\n¿Estos criterios son correctos o te gustaría ajustar alguno?"
    
    return summary

def format_viewing_request(property_id: str, property_title: str = "", contact_info: Optional[str] = None) -> str:
    """Format a message for scheduling a property viewing.
    
    Args:
        property_id: ID of the property to view
        property_title: Title of the property
        contact_info: Optional contact information from the user
        
    Returns:
        Formatted viewing request message
    """
    property_desc = f"{property_title} (Ref: {property_id})" if property_title else f"propiedad (Ref: {property_id})"
    
    message = f"¡Perfecto! 📅 Para agendar una visita a la {property_desc}, "
    
    if contact_info:
        message += f"utilizaré tu información de contacto ({contact_info}). "
    else:
        message += "necesitaré algunos datos adicionales. ¿Podrías proporcionarme un número de teléfono donde nuestro asesor pueda contactarte? "
    
    message += "\n\nUn asesor de LaHaus se pondrá en contacto contigo en las próximas 24 horas para coordinar la visita. "
    message += "También puedes contactarnos directamente al *+57 300 123 4567* si prefieres una respuesta más rápida."
    
    message += "\n\n¿Hay algún horario específico que te convenga para la visita?"
    
    return message

def format_contact_agent_request(property_id: str = None, question: str = None) -> str:
    """Format a message for connecting with a human agent.
    
    Args:
        property_id: Optional ID of the property of interest
        question: Optional specific question for the agent
        
    Returns:
        Formatted agent connection message
    """
    message = "👋 Entiendo que deseas hablar con uno de nuestros asesores especializados. "
    
    if property_id:
        message += f"Voy a solicitar que un asesor con conocimiento específico sobre la propiedad (Ref: {property_id}) se ponga en contacto contigo. "
    else:
        message += "Voy a solicitar que uno de nuestros asesores se ponga en contacto contigo lo antes posible. "
    
    if question:
        message += f"\n\nLe informaré que tienes la siguiente consulta: \"{question}\""
    
    message += "\n\n¿Podrías proporcionarme un número de teléfono donde te puedan contactar? Nuestro equipo se comunicará contigo en las próximas 24 horas laborables."
    
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
        # Try to truncate at a paragraph break to keep the message coherent
        truncated = message[:MAX_LENGTH-150]
        last_break = max(truncated.rfind('\n\n'), truncated.rfind('\n'), truncated.rfind('. '))
        
        if last_break > MAX_LENGTH * 0.7:  # Only truncate at break if it's not too short
            truncated = truncated[:last_break]
        
        truncated += "\n\n... [Mensaje truncado debido a limitaciones de longitud. Solicita más detalles si es necesario]"
        return truncated
    
    return message

def format_welcome_message() -> str:
    """Format a welcome message for new users.
    
    Returns:
        Formatted welcome message
    """
    message = "👋 *¡Hola! Soy Karol, tu asistente virtual de LaHaus* 🏡\n\n"
    message += "Estoy aquí para ayudarte a encontrar la propiedad perfecta según tus necesidades. "
    message += "Para ofrecerte las mejores opciones, me sería de gran ayuda que me cuentes:\n\n"
    message += "• ¿En qué zona o barrio te gustaría vivir?\n"
    message += "• ¿Cuál es tu presupuesto aproximado?\n"
    message += "• ¿Cuántas habitaciones y baños necesitas?\n"
    message += "• ¿Buscas alguna característica especial como gimnasio, piscina, parqueadero, etc?\n\n"
    message += "Por ejemplo, puedes decirme: \"*Busco un apartamento en Chapinero con 2 habitaciones y un presupuesto de 450 millones de pesos*\""
    
    return message

def format_search_instructions() -> str:
    """Format instructions on how to search for properties.
    
    Returns:
        Formatted instructions
    """
    message = "🔍 *Cómo buscar propiedades con LaHaus*\n\n"
    message += "Para ayudarte a encontrar la propiedad ideal, puedes indicarme lo siguiente:\n\n"
    message += "• *Tipo de propiedad:* Apartamento, casa, aparta-estudio, etc.\n"
    message += "• *Ubicación:* Barrio, zona o ciudad de interés\n"
    message += "• *Presupuesto:* Rango o presupuesto máximo\n"
    message += "• *Tamaño:* Número de habitaciones y baños\n"
    message += "• *Características especiales:* Piscina, gimnasio, parqueadero, etc.\n\n"
    message += "Ejemplo: \"Busco un apartamento de 2 habitaciones en Chapinero entre 400 y 500 millones, con parqueadero\"\n\n"
    message += "También puedes refinar tu búsqueda en cualquier momento o pedirme más información sobre una propiedad específica."
    
    return message

def format_follow_up_questions(properties: List[Dict[str, Any]] = None) -> List[str]:
    """Generate follow-up questions based on shown properties.
    
    Args:
        properties: List of properties shown to the user
        
    Returns:
        List of follow-up questions
    """
    generic_questions = [
        "¿Te gustaría ver propiedades en alguna otra zona?",
        "¿Prefieres ver opciones con un presupuesto diferente?",
        "¿Hay alguna característica específica que estés buscando?",
        "¿Prefieres apartamentos o casas?",
        "¿Te interesa alguna de estas propiedades?"
    ]
    
    if not properties or len(properties) == 0:
        return generic_questions
    
    specific_questions = []
    
    # Price range adjustment
    prices = [p['price'] for p in properties]
    avg_price = sum(prices) / len(prices)
    specific_questions.append(f"¿Te gustaría ver opciones {'más económicas' if avg_price > 500000000 else 'con más características'} que estas?")
    
    # Location preference
    locations = set(p.get('neighborhood', '') for p in properties if p.get('neighborhood'))
    if locations:
        locations_str = ", ".join(list(locations)[:2])
        specific_questions.append(f"Además de {locations_str}, ¿hay otras zonas que te interesen?")
    
    # Property type preference
    property_types = set(p.get('title', '').split()[0].lower() for p in properties)
    if 'apartamento' in property_types and 'casa' not in property_types:
        specific_questions.append("¿Te interesaría ver también opciones de casas?")
    elif 'casa' in property_types and 'apartamento' not in property_types:
        specific_questions.append("¿Te interesaría ver también opciones de apartamentos?")
    
    # Add generic questions to fill out the list
    combined = specific_questions + [q for q in generic_questions if q not in specific_questions]
    return combined[:5]  # Return up to 5 questions