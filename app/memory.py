from typing import Dict, List, Any, Optional
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMemory
from langchain_openai import ChatOpenAI
from langchain.memory.chat_message_histories import ChatMessageHistory
from langchain.schema.messages import BaseMessage, HumanMessage, AIMessage
import json
from loguru import logger

from .config import MAX_CONVERSATION_HISTORY, SUMMARY_INTERVAL

class PropertyConciergeMemory(ConversationBufferMemory):
    """Custom memory class for the LaHaus property concierge.
    
    This memory extends ConversationBufferMemory with additional
    specialized storage for property-related information:
    1. User preferences
    2. Property viewing history
    3. Engagement metrics
    
    It also provides summarization after a certain number of messages.
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        memory_key: str = "chat_history",
        return_messages: bool = True,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        **kwargs
    ):
        super().__init__(
            memory_key=memory_key,
            return_messages=return_messages,
            human_prefix=human_prefix,
            ai_prefix=ai_prefix
        )
        self.llm = llm
        self.user_preferences = {}
        self.property_history = []
        self.engagement_metrics = {
            "message_count": 0,
            "search_count": 0,
            "property_clicks": 0,
            "interest_indicators": 0
        }
    
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
    
    def _summarize_older_messages(self) -> None:
        """Summarize older messages to prevent context window overflow."""
        if len(self.chat_memory.messages) <= MAX_CONVERSATION_HISTORY * 2:
            return
            
        # Keep the most recent messages intact
        recent_messages = self.chat_memory.messages[-MAX_CONVERSATION_HISTORY * 2:]
        older_messages = self.chat_memory.messages[:-MAX_CONVERSATION_HISTORY * 2]
        
        if not older_messages or not self.llm:
            return
            
        # Create a summary of older messages
        try:
            from langchain.memory import ConversationSummaryMemory
            summary_memory = ConversationSummaryMemory(llm=self.llm)
            
            # Add message pairs to the summary memory
            for i in range(0, len(older_messages), 2):
                if i + 1 < len(older_messages):
                    human_msg = older_messages[i]
                    ai_msg = older_messages[i + 1]
                    if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                        summary_memory.save_context(
                            {"input": human_msg.content},
                            {"output": ai_msg.content}
                        )
            
            # Get the summary
            summary = summary_memory.load_memory_variables({})
            
            # Create a system message with the summary
            from langchain.schema.messages import SystemMessage
            summary_msg = SystemMessage(content=f"Previous conversation summary: {summary}")
            
            # Update chat memory with summary + recent messages
            self.chat_memory.messages = [summary_msg] + recent_messages
            
            logger.info(f"Summarized {len(older_messages)} older messages")
            
        except Exception as e:
            logger.error(f"Error summarizing messages: {str(e)}")
            # Fall back to truncation if summarization fails
            self.chat_memory.messages = recent_messages
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save the input/output pairs to the chat message history.
        
        Override to add summarization and metrics tracking.
        
        Args:
            inputs: Dictionary of inputs
            outputs: Dictionary of outputs
        """
        # Call the parent method to save the context
        super().save_context(inputs, outputs)
        
        # Update engagement metrics
        self.engagement_metrics["message_count"] += 1
        
        # Check if we need to summarize
        if (self.engagement_metrics["message_count"] % SUMMARY_INTERVAL == 0 and 
            self.llm is not None):
            self._summarize_older_messages()
    
    def clear(self) -> None:
        """Clear memory contents."""
        super().clear()
        self.user_preferences = {}
        self.property_history = []
        self.engagement_metrics = {
            "message_count": 0,
            "search_count": 0,
            "property_clicks": 0,
            "interest_indicators": 0
        }