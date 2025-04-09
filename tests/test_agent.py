import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import create_agent_prompt, extract_client_preferences
from app.memory import PropertyConciergeMemory

class TestAgentConfiguration(unittest.TestCase):
    def test_agent_prompt_creation(self):
        """Test that the agent prompt is created correctly"""
        prompt = create_agent_prompt()
        
        # Check that the prompt contains key sections
        self.assertIn("PERFIL Y FUNCIÓN", prompt)
        self.assertIn("TONO Y ESTILO", prompt)
        self.assertIn("PROCESO DE ASISTENCIA", prompt)
        self.assertIn("LIMITACIONES", prompt)
        self.assertIn("FORMATO DE RESPUESTAS", prompt)
        
    def test_preference_extraction(self):
        """Test extracting client preferences from conversation"""
        test_conversation = [
            {"role": "user", "content": "Estoy buscando un apartamento en Chapinero con 2 habitaciones"},
            {"role": "assistant", "content": "Claro, te ayudaré a buscar apartamentos en Chapinero con 2 habitaciones."},
            {"role": "user", "content": "Mi presupuesto es de 500 millones de pesos y necesito que tenga parqueadero"},
        ]
        
        preferences = extract_client_preferences(test_conversation)
        
        # Check that preferences were extracted correctly
        self.assertIn("locations", preferences)
        self.assertIn("chapinero", preferences["locations"])
        self.assertEqual(preferences["bedrooms"], 2)
        self.assertEqual(preferences["budget_max"], 500000000)
        self.assertIn("amenities", preferences)
        self.assertIn("parqueadero", preferences["amenities"])
        
    @patch('langchain_openai.ChatOpenAI')
    def test_property_concierge_memory(self, mock_chatmodel):
        """Test the custom memory implementation"""
        # Setup mock
        mock_chatmodel.return_value = MagicMock()
        
        # Create memory instance
        memory = PropertyConciergeMemory(llm=mock_chatmodel.return_value)
        
        # Test adding messages
        memory.chat_memory.add_user_message("Hola, busco un apartamento en Bogotá")
        memory.chat_memory.add_ai_message("¡Hola! Claro, te puedo ayudar a encontrar un apartamento en Bogotá.")
        
        # Test loading variables
        variables = memory.load_memory_variables({})
        self.assertIn("chat_history", variables)
        self.assertEqual(len(variables["chat_history"]), 2)
        
        # Test user preferences
        test_preferences = {
            "locations": ["bogota", "chapinero"],
            "budget_max": 600000000,
            "bedrooms": 2
        }
        memory.update_user_preferences(test_preferences)
        self.assertEqual(memory.user_preferences, test_preferences)
        
        # Test property history
        test_property = {"id": "prop1", "title": "Apartamento en Chapinero"}
        memory.add_property_to_history(test_property)
        self.assertIn(test_property, memory.property_history)
        
        # Test clearing memory
        memory.clear()
        self.assertEqual(len(memory.chat_memory.messages), 0)
        self.assertEqual(memory.user_preferences, {})
        self.assertEqual(memory.property_history, [])

if __name__ == '__main__':
    unittest.main()