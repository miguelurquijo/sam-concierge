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
            
            # Verify fallback data was used
            self.assertIn("Encontré", result)
            self.assertIn("Apartamento en Chapinero", result)
            self.assertIn("Casa en Usaquén", result)
            
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_filter_extraction(self, mock_json_load, mock_file_open, mock_os_exists):
        # Configure mocks
        mock_os_exists.return_value = True
        mock_json_load.return_value = self.sample_properties
        
        # Create the search tool and access its internals for testing
        search_tool = create_property_search_tool()
        
        # Test different queries to exercise filter extraction
        with patch('app.search.extract_filters', wraps=None) as mock_extract:
            # Setup the mock to call the real function and capture its return value
            def side_effect(query):
                # Import here to avoid circular import
                from app.search import extract_filters
                return extract_filters(query)
            
            mock_extract.side_effect = side_effect
            
            # Test price extraction
            search_tool("apartments under 500 millones")
            mock_extract.assert_called()
            
            # Test bedroom extraction
            search_tool("casa con 3 habitaciones")
            mock_extract.assert_called()
            
            # Test neighborhood extraction
            search_tool("propiedades en chapinero")
            mock_extract.assert_called()
            
            # Test amenity extraction
            search_tool("apartamento con piscina y gimnasio")
            mock_extract.assert_called()
            
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