from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_community.callbacks.manager import get_openai_callback
from loguru import logger
import json
import re

from .tools import create_lahaus_tools
from .templates import format_welcome_message, format_filter_summary
from .memory import PropertyConciergeMemory
from .config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE

def create_agent_prompt():
    """Creates the detailed system prompt for the LaHaus real estate agent.
    
    Returns:
        String containing the formatted system prompt
    """
    system_prompt = """
    # PERFIL Y FUNCIÓN
    Eres Karol, una asistente virtual especializada en bienes raíces de LaHaus en Colombia. Tu misión es ayudar a los clientes a encontrar la propiedad ideal según sus necesidades específicas.

    # TONO Y ESTILO
    - Comunícate en español de manera profesional pero cálida y conversacional.
    - Sé concisa y clara, evitando tecnicismos innecesarios.
    - Adapta tu comunicación para WhatsApp, con mensajes directos y bien estructurados.
    - Utiliza un tono empático y servicial que refleje la marca LaHaus.
    - Incluye emojis relevantes para hacer la conversación más amigable (🏠, 🔍, 💰, etc.).

    # PROCESO DE ASISTENCIA
    1. COMPRENSIÓN DE NECESIDADES:
       - Identifica los criterios esenciales: ubicación, presupuesto, tamaño, características especiales.
       - Si falta información clave, pregunta específicamente por ella.
       - Resume los criterios entendidos para verificar comprensión.

    2. BÚSQUEDA DE PROPIEDADES:
       - Utiliza siempre la herramienta de búsqueda con los criterios identificados.
       - Nunca inventes propiedades o detalles que no estén en los resultados.
       - Si no hay resultados exactos, sugiere ampliar criterios o alternativas.

    3. PRESENTACIÓN DE OPCIONES:
       - Muestra las propiedades más relevantes (máximo 3-5 por mensaje).
       - Destaca características que coincidan con los criterios del cliente.
       - Ordena por relevancia según las prioridades expresadas por el cliente.
       - Proporciona enlaces directos para ver más detalles.

    4. SEGUIMIENTO:
       - Pregunta si alguna propiedad les interesa para dar más detalles.
       - Ofrece programar visitas virtuales o presenciales.
       - Conecta con asesores humanos cuando sea apropiado.
       - Mantén el contexto de la conversación para no repetir información.

    # LIMITACIONES
    - NUNCA inventes información sobre propiedades o el mercado.
    - NO hagas afirmaciones sobre plazos de entrega específicos sin datos.
    - SOLO utiliza la información proporcionada por las herramientas de búsqueda.
    - NO solicites información personal sensible (como números de documentos o datos bancarios).

    # FORMATO DE RESPUESTAS
    Cuando presentes propiedades, incluye siempre:
    - Ubicación/barrio exacto
    - Precio (en formato $XXX.XXX.XXX)
    - Configuración (habitaciones/baños)
    - Área en metros cuadrados
    - 2-3 características destacadas relevantes para el cliente
    - Enlace para más información

    # INTERACCIONES ESPECÍFICAS
    - Si el cliente saluda, responde cordialmente y pregunta por sus necesidades de vivienda.
    - Si no entiendes alguna petición, pide aclaraciones específicas.
    - Si el cliente pide información muy específica que no tienes, ofrece contactar a un asesor.
    - Si el cliente desea una visita, facilita el proceso ofreciendo coordinar con un asesor.
    """
    
    return system_prompt

def create_agent(conversation_history=None):
    """Create a LangChain agent with conversation memory and tools.
    
    This function sets up an advanced real estate agent powered by GPT-4o
    with specialized tools for property search and conversation management.
    
    Args:
        conversation_history: Optional list of previous conversation messages
        
    Returns:
        A LangChain AgentExecutor instance
    """
    # Create all tools needed for the agent
    tools = create_lahaus_tools()
    
    # Create OpenAI chat model with appropriate parameters
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=MODEL_NAME,
        temperature=TEMPERATURE
    )
    
    # Create a specialized property concierge memory
    memory = PropertyConciergeMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True
    )
    
    # Load conversation history into memory if available
    if conversation_history:
        for message in conversation_history:
            if message["role"] == "user":
                memory.chat_memory.add_user_message(message["content"])
            elif message["role"] == "assistant":
                memory.chat_memory.add_ai_message(message["content"])
    
    # Create the system prompt template with detailed guidance
    system_prompt = create_agent_prompt()
    
    # Create the chat prompt template with appropriate placeholders
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    
    # Create the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # Create the agent executor with memory and verbose mode
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=memory, 
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        early_stopping_method="generate",
        return_intermediate_steps=True
    )
    
    return agent_executor

def extract_client_preferences(message_history):
    """Extract client preferences from conversation history.
    
    This function uses pattern matching to identify mentioned preferences
    throughout the conversation history, providing continuity.
    
    Args:
        message_history: List of conversation messages
        
    Returns:
        Dictionary of extracted preferences
    """
    preferences = {
        "locations": [],
        "budget_min": None,
        "budget_max": None,
        "bedrooms": None,
        "bathrooms": None,
        "property_type": None,
        "amenities": []
    }
    
    # Common Colombian neighborhoods and cities
    locations = [
        "chapinero", "usaquen", "chico", "cedritos", "salitre", 
        "poblado", "laureles", "envigado", "sabaneta", "belen",
        "bogota", "medellin", "cali", "barranquilla", "cartagena"
    ]
    
    # Common amenities
    amenities = [
        "piscina", "gimnasio", "gym", "parqueadero", "parking", 
        "terraza", "balcón", "balcon", "jardín", "jardin", 
        "seguridad", "vigilancia", "ascensor", "bbq", "playground"
    ]
    
    # Extract user messages only
    user_messages = [msg["content"].lower() for msg in message_history if msg["role"] == "user"]
    
    # Join all messages for pattern matching
    conversation_text = " ".join(user_messages)
    
    # Extract locations
    for location in locations:
        if location in conversation_text:
            preferences["locations"].append(location)
    
    # Extract budget with regex
    # Format: X-Y millones, X millones, hasta Y millones
    budget_range = re.search(r'entre\s*(\d+)[\s,]*y\s*(\d+)\s*millones', conversation_text)
    if budget_range:
        preferences["budget_min"] = int(budget_range.group(1)) * 1000000
        preferences["budget_max"] = int(budget_range.group(2)) * 1000000
    else:
        max_budget = re.search(r'(hasta|maximo|máximo)\s*(\d+)\s*millones', conversation_text)
        if max_budget:
            preferences["budget_max"] = int(max_budget.group(2)) * 1000000
        
        min_budget = re.search(r'(desde|minimo|mínimo)\s*(\d+)\s*millones', conversation_text)
        if min_budget:
            preferences["budget_min"] = int(min_budget.group(2)) * 1000000
        
        # Single budget mention
        single_budget = re.search(r'(\d+)\s*millones', conversation_text)
        if single_budget and not preferences["budget_max"]:
            # Assume this is a maximum budget
            preferences["budget_max"] = int(single_budget.group(1)) * 1000000
    
    # Extract bedrooms
    bedrooms = re.search(r'(\d+)\s*(?:habitaciones|hab|habitación|cuartos|recámaras)', conversation_text)
    if bedrooms:
        preferences["bedrooms"] = int(bedrooms.group(1))
    
    # Extract bathrooms
    bathrooms = re.search(r'(\d+)\s*(?:baños|baño)', conversation_text)
    if bathrooms:
        preferences["bathrooms"] = int(bathrooms.group(1))
    
    # Extract property type
    if re.search(r'\b(?:apartamento|apto|apartamentos)\b', conversation_text):
        preferences["property_type"] = "apartamento"
    elif re.search(r'\b(?:casa|casas)\b', conversation_text):
        preferences["property_type"] = "casa"
    
    # Extract amenities
    for amenity in amenities:
        if amenity in conversation_text:
            preferences["amenities"].append(amenity)
    
    # Filter out empty preferences
    return {k: v for k, v in preferences.items() if v}

def run_agent(agent, user_input):
    """Run the agent with a user input and return the response.
    
    This function processes the user input, handles special cases like
    greetings, and tracks conversation tokens and performance.
    
    Args:
        agent: The LangChain agent executor
        user_input: String containing the user's message
        
    Returns:
        The agent's response as a string
    """
    try:
        # Check if this is the first message (could be a greeting)
        is_first_message = False
        if agent.memory and len(agent.memory.chat_memory.messages) <= 1:
            is_first_message = True
            
            # If it's a greeting or very short first message, return welcome message
            if len(user_input.split()) < 3 or any(greeting in user_input.lower() 
                                              for greeting in ["hola", "buenos días", "buenas", "saludos"]):
                return format_welcome_message()
        
        # Track token usage and performance
        with get_openai_callback() as cb:
            # Run the agent with the user input
            response = agent.invoke({"input": user_input})
            
            # Log token usage
            logger.info(f"Total Tokens: {cb.total_tokens}")
            logger.info(f"Prompt Tokens: {cb.prompt_tokens}")
            logger.info(f"Completion Tokens: {cb.completion_tokens}")
            logger.info(f"Total Cost (USD): ${cb.total_cost}")
        
        # Extract client preferences if the message history is available
        if agent.memory and len(agent.memory.chat_memory.messages) > 1:
            chat_history = [{"role": "user" if i % 2 == 0 else "assistant", 
                            "content": msg.content}
                          for i, msg in enumerate(agent.memory.chat_memory.messages)]
            
            # Extract and save preferences to specialized memory if available
            preferences = extract_client_preferences(chat_history)
            if preferences and hasattr(agent.memory, 'update_user_preferences'):
                agent.memory.update_user_preferences(preferences)
                
            # Check if any tool was used for property search
            if hasattr(response, 'intermediate_steps') and response.intermediate_steps:
                for step in response.intermediate_steps:
                    if step[0].tool == "search_properties" and hasattr(agent.memory, 'log_search'):
                        agent.memory.log_search(step[0].tool_input)
                        
                        # Extract property IDs from tool output
                        property_links = re.findall(r'https://lahaus.com/properties/(\w+)', step[1])
                        for prop_id in property_links:
                            property_info = {"id": prop_id, "shown_at": json.dumps({"role": "assistant", "content": response['output']})}
                            if hasattr(agent.memory, 'add_property_to_history'):
                                agent.memory.add_property_to_history(property_info)
        
        # Log the conversation for analysis
        logger.info(f"User: {user_input}")
        logger.info(f"Agent: {response['output']}")
        
        # Return the formatted response
        return response['output']
        
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        return "Lo siento, estoy teniendo problemas para procesar tu solicitud en este momento. ¿Podrías intentarlo de nuevo o reformular tu pregunta?"

def analyze_conversation(conversation_history):
    """Analyze the conversation to identify patterns and provide insights.
    
    Args:
        conversation_history: List of conversation messages
        
    Returns:
        Dictionary with conversation analysis
    """
    if not conversation_history:
        return {"status": "No conversation history available"}
    
    analysis = {
        "message_count": len(conversation_history),
        "user_messages": 0,
        "assistant_messages": 0,
        "average_user_message_length": 0,
        "average_assistant_message_length": 0,
        "preferences": {},
        "conversation_topics": []
    }
    
    user_lengths = []
    assistant_lengths = []
    
    for message in conversation_history:
        if message["role"] == "user":
            analysis["user_messages"] += 1
            user_lengths.append(len(message["content"]))
        elif message["role"] == "assistant":
            analysis["assistant_messages"] += 1
            assistant_lengths.append(len(message["content"]))
    
    if user_lengths:
        analysis["average_user_message_length"] = sum(user_lengths) / len(user_lengths)
    
    if assistant_lengths:
        analysis["average_assistant_message_length"] = sum(assistant_lengths) / len(assistant_lengths)
    
    # Extract client preferences
    analysis["preferences"] = extract_client_preferences(conversation_history)
    
    return analysis