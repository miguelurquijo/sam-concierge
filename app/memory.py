from typing import Dict, List, Any, Optional
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.schema import BaseMemory, BaseChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain.memory.chat_message_histories import ChatMessageHistory
from langchain.schema.messages import BaseMessage, HumanMessage, AIMessage
import json
from loguru import logger

from .config import MAX_CONVERSATION_HISTORY, SUMMARY_INTERVAL

class PropertyConciergeMemory(BaseMemory):
    """Custom memory class for the LaHaus property concierge.
    
    This memory manages:
    1. Regular conversation context
    2. User preferences extracted from the conversation
    3. Property search history
    4. User engagement metrics
    
    It also provides summarization after a certain number of messages.
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        max_token_limit: int = 4000,
        memory_key: str = "chat_history",
        return_messages: bool = True,
    ):
        self.chat_memory = ChatMessageHistory()
        self.llm = llm
        self.max_token_limit = max_token_limit
        self.memory_key = memory_key
        self.return_messages = return_messages
        
        # Additional memory components
        self.user_preferences = {}  # Extracted user preferences
        self.property_history = []  # Properties previously shown
        self.engagement_metrics = {
            "message_count": 0,
            "search_count": 0,
            "property_clicks": 0,
            "interest_indicators": 0
        }
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables to be passed to the model.
        
        Args:
            inputs: Dictionary of input variables
            
        Returns:
            Dictionary containing the chat history and other memory variables
        """
        if self.return_messages:
            return {self.memory_key: self.chat_memory.messages}
        else:
            return {self.memory_key: self._buffer_as_string()}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context from this conversation to memory.
        
        Args:
            inputs: Dictionary of inputs
            outputs: Dictionary of outputs
        """
        # Extract the input and output strings
        input_str = inputs.get("input", "")
        output_str = outputs.get("output", "")
        
        # Save to chat memory
        self.chat_memory.add_user_message(input_str)
        self.chat_memory.add_ai_message(output_str)
        
        # Update engagement metrics
        self.engagement_metrics["message_count"] += 1
        
        # Check if we need to summarize
        if (self.engagement_metrics["message_count"] % SUMMARY_INTERVAL == 0 and 
            self.llm is not None and len(self.chat_memory.messages) > SUMMARY_INTERVAL * 2):
            self._summarize_older_messages()
    
    def _buffer_as_string(self) -> str:
        """Convert buffer to a string for models that don't support message format.
        
        Returns:
            String representation of the chat history
        """
        buffer_string = ""
        for message in self.chat_memory.messages:
            if isinstance(message, HumanMessage):
                buffer_string += f"Human: {message.content}\n"
            elif isinstance(message, AIMessage):
                buffer_string += f"AI: {message.content}\n"
            else:
                buffer_string += f"{message.type}: {message.content}\n"
        return buffer_string
    
    def _summarize_older_messages(self) -> None:
        """Summarize older messages to prevent context window overflow."""
        if len(self.chat_memory.messages) <= MAX_CONVERSATION_HISTORY:
            return
            
        # Keep the most recent messages intact
        recent_messages = self.chat_memory.messages[-MAX_CONVERSATION_HISTORY:]
        older_messages = self.chat_memory.messages[:-MAX_CONVERSATION_HISTORY]
        
        if not older_messages:
            return
            
        # Create a summary of older messages
        try:
            summary_memory = ConversationSummaryMemory(llm=self.llm)
            for i in range(0, len(older_messages), 2):
                if i + 1 < len(older_messages):
                    human_msg = older_messages[i]
                    ai_msg = older_messages[i + 1]
                    if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                        summary_memory.save_context(
                            {"input": human_msg.content},
                            {"output": ai_msg.content}
                        )
            
            summary = summary_memory.load_memory_variables({})
            
            # Replace older messages with summary
            system_summary = f"The conversation history has been summarized as follows: {summary}"
            logger.info(f"Summarized {len(older_messages)} older messages")
            
            # Update chat memory with the summary as a system message
            self.chat_memory.messages = [system_summary] + recent_messages
            
        except Exception as e:
            logger.error(f"Error summarizing messages: {str(e)}")
            # Fall back to truncation if summarization fails
            self.chat_memory.messages = recent_messages
    
    def update_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences based on conversation.
        
        Args:
            preferences: Dictionary of user preferences
        """
        self.user_preferences.update(preferences)
        logger.info(f"Updated user preferences: {json.dumps(self.user_preferences, ensure_ascii=False)}")
    
    def add_property_to_history(self, property_info: Dict[str, Any]) -> None:
        """Add a property to the history of shown properties.
        
        Args:
            property_info: Dictionary containing property information
        """
        if property_info and "id" in property_info:
            # Check if property is already in history
            existing_ids = [p.get("id") for p in self.property_history]
            if property_info["id"] not in existing_ids:
                self.property_history.append(property_info)
                logger.info(f"Added property {property_info['id']} to history")
    
    def log_property_click(self, property_id: str) -> None:
        """Log when a user clicks on a property link.
        
        Args:
            property_id: ID of the property that was clicked
        """
        self.engagement_metrics["property_clicks"] += 1
        logger.info(f"User clicked on property {property_id}")
    
    def log_search(self, query: str) -> None:
        """Log when a search is performed.
        
        Args:
            query: The search query
        """
        self.engagement_metrics["search_count"] += 1
        logger.info(f"Search performed: {query}")
    
    def clear(self) -> None:
        """Clear memory contents."""
        self.chat_memory.clear()
        self.user_preferences = {}
        self.property_history = []
        self.engagement_metrics = {
            "message_count": 0,
            "search_count": 0,
            "property_clicks": 0,
            "interest_indicators": 0
        }
    
    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]