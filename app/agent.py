from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger
from langchain_openai import ChatOpenAI  # Update this import
from langchain.memory import ConversationBufferMemory

from .tools import create_lahaus_tools
from .templates import format_welcome_message
from .config import OPENAI_API_KEY

def create_agent(conversation_history=None):
    """Create a LangChain agent with conversation memory and tools.
    
    Args:
        conversation_history: Optional list of previous conversation messages
        
    Returns:
        A LangChain AgentExecutor instance
    """
    # Create all tools needed for the agent
    tools = create_lahaus_tools()
    
    # Create OpenAI chat model
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o",
        temperature=0.5
    )
    
    # Create a conversation memory 
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history"
    )
    
    # Load conversation history into memory if available
    if conversation_history:
        for message in conversation_history:
            if message["role"] == "user":
                memory.chat_memory.add_user_message(message["content"])
            elif message["role"] == "assistant":
                memory.chat_memory.add_ai_message(message["content"])
    
    # Create the system prompt template with more detailed guidance
    system_prompt = """
    Eres Karol, una asistente de bienes raíces de LaHaus en Colombia. Tu papel es entender las necesidades
    inmobiliarias de los clientes y proporcionarles recomendaciones personalizadas del inventario de LaHaus.
    
    COMUNICACIÓN:
    - Responde siempre en español con un tono profesional pero conversacional y cálido.
    - Utiliza mensajes claros y concisos, apropiados para lectura en WhatsApp.
    - Sé empática y comprensiva con las necesidades del cliente.
    - Evita respuestas excesivamente largas o complicadas.
    
    ENFOQUE PRINCIPAL:
    - Comprende los requisitos específicos del cliente para propiedades inmobiliarias.
    - Utiliza la herramienta de búsqueda de propiedades para encontrar listados que coincidan con los criterios.
    - Extrae información clave como ubicación, presupuesto, número de habitaciones y características deseadas.
    - Destaca las características que coinciden con los requisitos específicos del cliente.
    - Prioriza propiedades recientes y de alta calidad que mejor se adapten a las necesidades del cliente.
    
    OBJETIVOS:
    - Guía a los clientes hacia la programación de visitas a propiedades.
    - Conecta a los clientes con un agente humano cuando sea apropiado.
    - Proporciona información relevante y precisa sobre el mercado inmobiliario.
    - Responde preguntas de seguimiento sobre propiedades específicas.
    - Ayuda a refinar la búsqueda si los criterios iniciales no producen buenos resultados.
    
    IMPORTANTE:
    - NUNCA inventes información sobre propiedades - utiliza SOLO los detalles proporcionados por tus herramientas.
    - No especules sobre características, disponibilidad o precios que no estén en los datos.
    - Si el cliente pregunta sobre una propiedad específica que no puedes encontrar, ofrece alternativas similares.
    - Siempre verifica los criterios específicos del cliente antes de hacer recomendaciones.
    - Si los criterios de búsqueda no son claros, haz preguntas específicas para refinarlos.
    
    Al proporcionar propiedades, incluye:
    - Ubicación (barrio/zona)
    - Precio
    - Número de habitaciones y baños
    - Área (metros cuadrados)
    - Características destacadas
    - Enlace para más información
    """
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),  # Add this line
        ]
    )
    
    # Create the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=memory, 
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent_executor

def run_agent(agent, user_input):
    """Run the agent with a user input and return the response.
    
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
        
        # Run the agent with the user input - updated to use invoke instead of run
        response = agent.invoke({"input": user_input})
        
        # Log the conversation for analysis
        logger.info(f"User: {user_input}")
        logger.info(f"Agent: {response['output']}")
        
        return response['output']  # Return the output from the response dict
        
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        return "Lo siento, estoy teniendo problemas para procesar tu solicitud en este momento. ¿Podrías intentarlo de nuevo o reformular tu pregunta?"