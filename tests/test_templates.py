import pytest
import datetime
from app.templates import (
    format_price, 
    format_amenities, 
    format_date, 
    truncate_text, 
    add_line_breaks, 
    format_location,
    format_property_card, 
    format_property_brief, 
    format_property_comparison, 
    format_property_list,
    format_property_gallery,
    format_no_results_message,
    format_filter_summary,
    format_viewing_request,
    format_contact_agent_request,
    format_whatsapp_message,
    format_welcome_message,
    format_search_instructions,
    format_follow_up_questions
)

class TestFormattingUtilities:
    def test_format_price(self):
        assert format_price(500000000) == "$500.000.000"
        assert format_price(0) == "$0"
        assert format_price(1000) == "$1.000"
    
    def test_format_amenities(self):
        amenities = ["piscina", "gimnasio", "parqueadero", "terraza", "jardín"]
        
        # Test list style formatting
        list_format = format_amenities(amenities, max_display=3, style="list")
        assert "🏊 piscina" in list_format
        assert "🏋️ gimnasio" in list_format
        assert "🚗 parqueadero" in list_format
        assert "...y 2 más" in list_format
        
        # Test inline style formatting
        inline_format = format_amenities(amenities, max_display=3, style="inline")
        assert "🏊 piscina, 🏋️ gimnasio, 🚗 parqueadero" in inline_format
        assert "(+2 más)" in inline_format
        
        # Test bullets style formatting
        bullets_format = format_amenities(amenities, max_display=3, style="bullets")
        assert "piscina" in bullets_format
        assert "gimnasio" in bullets_format
        assert "parqueadero" in bullets_format
        assert "...y 2 más" in bullets_format
        
        # Test empty amenities
        assert format_amenities([]) == ""
    
    def test_format_date(self):
        # Test with valid ISO date
        assert format_date("2023-10-15") == "15 de octubre de 2023"
        
        # Test with time included
        assert "15 de octubre de 2023, 14:30" in format_date("2023-10-15T14:30:00", include_time=True)
        
        # Test with invalid date
        assert format_date("invalid-date") == "invalid-date"
    
    def test_truncate_text(self):
        text = "This is a long text that should be truncated at some point to make it shorter."
        
        # Test with default parameters
        truncated = truncate_text(text, max_length=20)
        assert len(truncated) <= 23  # 20 + "..."
        assert truncated.endswith("...")
        
        # Test without ellipsis
        truncated = truncate_text(text, max_length=20, add_ellipsis=False)
        assert len(truncated) <= 20
        assert not truncated.endswith("...")
        
        # Test with text shorter than max length
        short_text = "Short text"
        assert truncate_text(short_text, max_length=20) == short_text
        
        # Test empty text
        assert truncate_text("") == ""
    
    def test_add_line_breaks(self):
        text = "This is a long text that should have line breaks added to improve readability on mobile devices."
        
        # Test with default line length
        formatted = add_line_breaks(text)
        assert "\n" in formatted
        
        # Make sure no line is longer than max_line_length
        for line in formatted.split("\n"):
            assert len(line) <= 40
        
        # Test with custom line length
        formatted = add_line_breaks(text, max_line_length=20)
        for line in formatted.split("\n"):
            assert len(line) <= 20
        
        # Test with short text
        short_text = "Short text"
        assert add_line_breaks(short_text) == short_text
    
    def test_format_location(self):
        # Test with both neighborhood and city
        assert format_location("Chapinero", "Bogotá") == "📍 Chapinero, Bogotá"
        
        # Test with only neighborhood
        assert format_location("Chapinero") == "📍 Chapinero"
        
        # Test with only city
        assert format_location("", "Bogotá") == "📍 Bogotá"
        
        # Test with neither
        assert format_location("", "") == ""


class TestPropertyTemplates:
    # Create a sample property for testing
    @pytest.fixture
    def sample_property(self):
        return {
            "id": "12345",
            "title": "Apartamento en Chapinero",
            "price": 450000000,
            "bedrooms": 2,
            "bathrooms": 2,
            "area": 85,
            "neighborhood": "Chapinero",
            "description": "Hermoso apartamento con excelente ubicación, luminoso y con acabados de primera.",
            "amenities": ["Parqueadero", "Gimnasio", "Seguridad 24/7", "Terraza"],
            "url": "https://lahaus.com/property/12345",
            "construction_year": 2018,
            "stratum": 4
        }
    
    @pytest.fixture
    def sample_properties(self):
        return [
            {
                "id": "12345",
                "title": "Apartamento en Chapinero",
                "price": 450000000,
                "bedrooms": 2,
                "bathrooms": 2,
                "area": 85,
                "neighborhood": "Chapinero",
                "description": "Hermoso apartamento con excelente ubicación, luminoso y con acabados de primera.",
                "amenities": ["Parqueadero", "Gimnasio", "Seguridad 24/7", "Terraza"],
                "url": "https://lahaus.com/property/12345"
            },
            {
                "id": "67890",
                "title": "Casa en Chía",
                "price": 650000000,
                "bedrooms": 3,
                "bathrooms": 3,
                "area": 120,
                "neighborhood": "Chía",
                "description": "Amplia casa con jardín, perfecta para familias que buscan tranquilidad cerca de Bogotá.",
                "amenities": ["Jardín", "Parqueadero", "Piscina"],
                "url": "https://lahaus.com/property/67890"
            },
            {
                "id": "24680",
                "title": "Apartamento en Usaquén",
                "price": 550000000,
                "bedrooms": 3,
                "bathrooms": 2,
                "area": 95,
                "neighborhood": "Usaquén",
                "description": "Apartamento con excelente vista, cerca a centros comerciales y zonas de entretenimiento.",
                "amenities": ["Parqueadero", "Gimnasio", "Seguridad 24/7"],
                "url": "https://lahaus.com/property/24680"
            }
        ]
    
    def test_format_property_card(self, sample_property):
        # Test standard card format
        card = format_property_card(sample_property)
        assert f"*{sample_property['title']}*" in card
        assert f"(Ref: {sample_property['id']})" in card
        assert format_price(sample_property['price']) in card
        assert f"{sample_property['bedrooms']} habitaciones" in card
        assert f"{sample_property['bathrooms']} baños" in card
        assert f"{sample_property['area']} m²" in card
        assert sample_property['neighborhood'] in card
        assert "¿Te gustaría más información sobre esta propiedad?" in card
        
        # Test detailed card format
        detailed_card = format_property_card(sample_property, detailed=True)
        assert "Descripción:" in detailed_card
        assert sample_property['description'].split()[0] in detailed_card
        assert "Año de construcción:" in detailed_card
        assert str(sample_property['construction_year']) in detailed_card
        assert "Estrato:" in detailed_card
        assert str(sample_property['stratum']) in detailed_card
        assert "¿Te gustaría agendar una visita a esta propiedad?" in detailed_card
        
        # Test with missing key
        incomplete_property = {k: v for k, v in sample_property.items() if k != 'price'}
        error_card = format_property_card(incomplete_property)
        assert "Error: Falta información de la propiedad" in error_card
    
    def test_format_property_brief(self, sample_property):
        # Test brief format without index
        brief = format_property_brief(sample_property)
        assert f"*{sample_property['title']}*" in brief
        assert format_price(sample_property['price']) in brief
        assert f"{sample_property['bedrooms']} hab" in brief
        assert f"{sample_property['area']} m²" in brief
        assert sample_property['neighborhood'] in brief
        assert sample_property['url'] in brief
        
        # Test brief format with index
        brief_with_index = format_property_brief(sample_property, index=1)
        assert f"*1. {sample_property['title']}*" in brief_with_index
        
        # Test with missing key
        incomplete_property = {k: v for k, v in sample_property.items() if k != 'area'}
        error_brief = format_property_brief(incomplete_property)
        assert "Error: Falta información de la propiedad" in error_brief
    
    def test_format_property_comparison(self, sample_properties):
        # Test comparison of multiple properties
        comparison = format_property_comparison(sample_properties)
        assert "COMPARACIÓN DE PROPIEDADES" in comparison
        assert "Propiedad 1" in comparison
        assert "Propiedad 2" in comparison
        assert "Propiedad 3" in comparison
        assert "Habitaciones:" in comparison
        assert "Baños:" in comparison
        assert "Área:" in comparison
        assert "Ubicación:" in comparison
        
        # Test with insufficient properties
        assert "Se necesitan al menos 2 propiedades" in format_property_comparison([sample_properties[0]])
        assert "Se necesitan al menos 2 propiedades" in format_property_comparison([])
    
    def test_format_property_list(self, sample_properties):
        # Test standard property list
        property_list = format_property_list(sample_properties)
        assert f"*He encontrado {len(sample_properties)} propiedades que podrían interesarte:*" in property_list
        for i, prop in enumerate(sample_properties, 1):
            assert prop['title'] in property_list
            assert format_price(prop['price']) in property_list
        
        # Test with limited number of properties
        limited_list = format_property_list(sample_properties, max_properties=2)
        assert "Y 1 propiedades más que coinciden con tus criterios" in limited_list
        
        # Test with empty list
        empty_list = format_property_list([])
        assert "No encontré propiedades que coincidan con tus criterios" in empty_list
    
    def test_format_property_gallery(self, sample_properties):
        # Test property gallery formatting
        gallery = format_property_gallery(sample_properties)
        assert "GALERÍA DE PROPIEDADES" in gallery
        assert f"({len(sample_properties)} resultados)" in gallery
        for i, prop in enumerate(sample_properties, 1):
            assert f"{i}. {prop['title']}" in gallery
            assert format_price(prop['price']) in gallery
        
        # Test with limited number of properties
        limited_gallery = format_property_gallery(sample_properties, max_properties=2)
        assert "...y 1 propiedades más disponibles" in limited_gallery
        
        # Test with empty list
        empty_gallery = format_property_gallery([])
        assert "No encontré propiedades que coincidan con tus criterios" in empty_gallery


class TestResponseTemplates:
    @pytest.fixture
    def sample_filters(self):
        return {
            "property_type": "apartamento",
            "neighborhoods": ["chapinero", "usaquén"],
            "min_price": 300000000,
            "max_price": 500000000,
            "min_bedrooms": 2,
            "min_bathrooms": 2,
            "min_area": 75,
            "amenities": ["parqueadero", "gimnasio"]
        }
        
    @pytest.fixture
    def sample_properties(self):
        return [
            {
                "id": "12345",
                "title": "Apartamento en Chapinero",
                "price": 450000000,
                "bedrooms": 2,
                "bathrooms": 2,
                "area": 85,
                "neighborhood": "Chapinero",
                "description": "Hermoso apartamento con excelente ubicación, luminoso y con acabados de primera.",
                "amenities": ["Parqueadero", "Gimnasio", "Seguridad 24/7", "Terraza"],
                "url": "https://lahaus.com/property/12345"
            },
            {
                "id": "67890",
                "title": "Casa en Chía",
                "price": 650000000,
                "bedrooms": 3,
                "bathrooms": 3,
                "area": 120,
                "neighborhood": "Chía",
                "description": "Amplia casa con jardín, perfecta para familias que buscan tranquilidad cerca de Bogotá.",
                "amenities": ["Jardín", "Parqueadero", "Piscina"],
                "url": "https://lahaus.com/property/67890"
            }
        ]
    
    def test_format_no_results_message(self, sample_filters):
        # Test with filters
        message = format_no_results_message(sample_filters)
        assert "No encontré propiedades que coincidan exactamente con tus criterios" in message
        assert "El presupuesto máximo de" in message
        assert format_price(sample_filters['max_price']) in message
        
        # Test without filters
        message = format_no_results_message()
        assert "No encontré propiedades que coincidan exactamente con tus criterios" in message
    
    def test_format_filter_summary(self, sample_filters):
        # Test with complete filters
        summary = format_filter_summary(sample_filters)
        assert "*Estoy buscando propiedades con las siguientes características:*" in summary
        assert "*Tipo:* Apartamento" in summary
        assert "*Ubicación:* Chapinero, Usaquén" in summary
        assert "*Precio:* Entre" in summary
        assert "*Habitaciones:* 2+" in summary
        assert "*Baños:* 2+" in summary
        assert "*Área mínima:* 75 m²" in summary
        assert "*Características:* Parqueadero, Gimnasio" in summary
        
        # Test with empty filters
        assert "Estoy buscando propiedades según tus preferencias generales." == format_filter_summary({})
    
    def test_format_viewing_request(self):
        # Test with property title
        message = format_viewing_request("12345", "Apartamento en Chapinero", "123-456-7890")
        assert "Para agendar una visita a la Apartamento en Chapinero (Ref: 12345)" in message
        assert "utilizaré tu información de contacto (123-456-7890)" in message
        
        # Test without contact info
        message = format_viewing_request("12345", "Apartamento en Chapinero")
        assert "necesitaré algunos datos adicionales" in message
        assert "¿Podrías proporcionarme un número de teléfono" in message
    
    def test_format_contact_agent_request(self):
        # Test with property ID and question
        message = format_contact_agent_request("12345", "¿Cuándo estará disponible para mudarse?")
        assert "con conocimiento específico sobre la propiedad (Ref: 12345)" in message
        assert "tienes la siguiente consulta: \"¿Cuándo estará disponible para mudarse?\"" in message
        
        # Test without property ID and question
        message = format_contact_agent_request()
        assert "Voy a solicitar que uno de nuestros asesores se ponga en contacto contigo" in message
    
    def test_format_whatsapp_message(self):
        # Test message within length limit
        short_message = "Este es un mensaje corto."
        assert format_whatsapp_message(short_message) == short_message
        
        # Test message exceeding length limit
        long_message = "a" * 5000
        truncated = format_whatsapp_message(long_message)
        assert len(truncated) < 4096
        assert "[Mensaje truncado debido a limitaciones de longitud" in truncated
    
    def test_format_welcome_message(self):
        welcome = format_welcome_message()
        assert "¡Hola! Soy Karol, tu asistente virtual de LaHaus" in welcome
        assert "zona o barrio" in welcome
        assert "presupuesto" in welcome
        assert "habitaciones y baños" in welcome
        assert "característica especial" in welcome
    
    def test_format_search_instructions(self):
        instructions = format_search_instructions()
        assert "Cómo buscar propiedades con LaHaus" in instructions
        assert "Tipo de propiedad:" in instructions
        assert "Ubicación:" in instructions
        assert "Presupuesto:" in instructions
        assert "Tamaño:" in instructions
        assert "Características especiales:" in instructions
    
    def test_format_follow_up_questions(self, sample_properties):
        # Test with properties
        questions = format_follow_up_questions(sample_properties)
        assert len(questions) <= 5
        assert any("presupuesto" in q.lower() for q in questions)
        assert any("zonas" in q.lower() for q in questions)
        
        # Test without properties
        questions = format_follow_up_questions()
        assert len(questions) == 5
        assert all(isinstance(q, str) for q in questions)