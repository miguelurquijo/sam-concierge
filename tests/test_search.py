import unittest
import os
import sys
import json
from unittest.mock import patch, mock_open, MagicMock

# Add parent directory to path so we can import the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.search import create_property_search_tool, get_property_by_id
from app.templates import format_property_list, format_property_card, format_filter_summary

class TestPropertySearch(unittest.TestCase):
    def setUp(self):
        # Sample property data for testing
        self.sample_properties = [
            {
                "id": "test1",
                "title": "Test Apartment 1",
                "price": 500000000,
                "bedrooms": 2,
                "bathrooms": 2,
                "area": 80,
                "neighborhood": "Chapinero",
                "description": "Test description",
                "url": "https://test.com/property1",
                "amenities": ["Gimnasio", "Piscina", "Seguridad 24h"]
            },
            {
                "id": "test2",
                "title": "Test House 2",
                "price": 800000000,
                "bedrooms": 3,
                "bathrooms": 3,
                "area": 150,
                "neighborhood": "Usaquén",
                "description": "Another test description",
                "url": "https://test.com/property2",
                "amenities": ["Jardín", "Parqueadero", "Seguridad 24h"]
            }
        ]
        
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_search_properties_with_sample_data(self, mock_json_load, mock_file_open, mock_os_exists):
        # Configure mocks
        mock_os_exists.return_value = True
        mock_json_load.return_value = self.sample_properties
        
        # Create the search tool
        search_tool = create_property_search_tool()
        
        # Run a search
        result = search_tool("apartments in Chapinero with 2 bedrooms")
        
        # Verify results
        self.assertIn("Encontré", result)
        self.assertIn("Test Apartment 1", result)
        self.assertIn("$500.000.000", result)
        self.assertIn("2 hab", result)
        
    def test_search_properties_fallback_data(self):
        # Test the fallback when no sample data file exists
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            search_tool = create_property_search_tool()
            result = search_tool("apartments in Chapinero")
            
            # Verify fallback data was used - modified to match new template format
            self.assertIn("Encontré", result)
            self.assertIn("Apartamento en Chapinero", result)
            # We don't expect "Casa en Usaquén" in the output anymore because the filter
            # extracts "chapinero" from the query and filters out other properties
            
    def test_filter_extraction(self):
        """Test the filter extraction functionality directly."""
        from app.search import extract_filters
        
        # Test price extraction
        filters = extract_filters("apartments under 500 millones")
        self.assertIn('max_price', filters)
        self.assertEqual(filters['max_price'], 500000000)
        
        # Test bedroom extraction
        filters = extract_filters("casa con 3 habitaciones")
        self.assertIn('property_type', filters)
        self.assertEqual(filters['property_type'], 'casa')
        self.assertIn('min_bedrooms', filters)
        self.assertEqual(filters['min_bedrooms'], 3)
        
        # Test neighborhood extraction
        filters = extract_filters("propiedades en chapinero")
        self.assertIn('neighborhoods', filters)
        self.assertIn('chapinero', filters['neighborhoods'])
        
        # Test amenity extraction
        filters = extract_filters("apartamento con piscina y gimnasio")
        self.assertIn('property_type', filters)
        self.assertEqual(filters['property_type'], 'apartamento')
        self.assertIn('amenities', filters)
        self.assertIn('piscina', filters['amenities'])
        self.assertIn('gimnasio', filters['amenities'])
            
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_property_by_id(self, mock_json_load, mock_file_open, mock_os_exists):
        # Configure mocks
        mock_os_exists.return_value = True
        mock_json_load.return_value = self.sample_properties
        
        # Test getting a property by ID
        property_data = get_property_by_id("test1")
        
        # Verify the result
        self.assertIsNotNone(property_data)
        self.assertEqual(property_data["id"], "test1")
        self.assertEqual(property_data["title"], "Test Apartment 1")
        
        # Test getting a non-existent property
        property_data = get_property_by_id("nonexistent")
        self.assertIsNone(property_data)
        
    def test_template_formatting(self):
        # Test property list formatting
        formatted_list = format_property_list(self.sample_properties, 2)
        self.assertIn("Encontré 2 propiedades", formatted_list)
        self.assertIn("Test Apartment 1", formatted_list)
        self.assertIn("Test House 2", formatted_list)
        
        # Test single property card formatting
        property_card = format_property_card(self.sample_properties[0])
        self.assertIn("Test Apartment 1", property_card)
        self.assertIn("$500.000.000", property_card)
        self.assertIn("2 habitaciones", property_card)
        
        # Test filter summary formatting
        filters = {
            "property_type": "apartamento",
            "neighborhoods": ["chapinero"],
            "max_price": 500000000,
            "min_bedrooms": 2
        }
        
        filter_summary = format_filter_summary(filters)
        self.assertIn("Tipo: Apartamento", filter_summary)
        self.assertIn("Ubicación: Chapinero", filter_summary)
        self.assertIn("Precio máximo: $500.000.000", filter_summary)
        self.assertIn("Habitaciones: 2+", filter_summary)

if __name__ == '__main__':
    unittest.main()