from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .dtmac import DTMAC, DTMessage, MessagePriority

class BaseAgent(ABC):
    def __init__(self, agent_id: str, dtmac: DTMAC, topics: List[str]):
        self.agent_id = agent_id
        self.dtmac = dtmac
        self.topics = topics
        
        # Register agent with DTMAC
        self.dtmac.register_agent(agent_id, topics)
        
        # Register default message handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.dtmac.register_handler(self.agent_id, "ping", self._handle_ping)
        self.dtmac.register_handler(self.agent_id, "status_request", self._handle_status_request)
    
    async def _handle_ping(self, message: DTMessage):
        """Handle ping messages"""
        await self.dtmac.send_message(
            sender=self.agent_id,
            recipients=[message.sender],
            content={"status": "alive"},
            message_type="pong",
            priority=MessagePriority.HIGH
        )
    
    async def _handle_status_request(self, message: DTMessage):
        """Handle status request messages"""
        status = await self.get_status()
        await self.dtmac.send_message(
            sender=self.agent_id,
            recipients=[message.sender],
            content={"status": status},
            message_type="status_response",
            priority=MessagePriority.NORMAL
        )
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of the agent"""
        pass
    
    async def send_to_agent(self, 
                          recipient: str, 
                          content: Dict[str, Any], 
                          message_type: str,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          metadata: Dict[str, Any] = None):
        """Send message to specific agent"""
        await self.dtmac.send_message(
            sender=self.agent_id,
            recipients=[recipient],
            content=content,
            message_type=message_type,
            priority=priority,
            metadata=metadata
        )
    
    async def broadcast_to_topic(self, 
                               topic: str, 
                               content: Dict[str, Any], 
                               message_type: str,
                               priority: MessagePriority = MessagePriority.NORMAL):
        """Broadcast message to all agents subscribed to a topic"""
        await self.dtmac.broadcast_to_topic(
            sender=self.agent_id,
            topic=topic,
            content=content,
            message_type=message_type,
            priority=priority
        )
    
    def get_message_history(self) -> List[DTMessage]:
        """Get message history for this agent"""
        return self.dtmac.get_message_history(self.agent_id)
    
    def get_subscribed_topics(self) -> List[str]:
        """Get topics this agent is subscribed to"""
        return self.dtmac.get_agent_topics(self.agent_id)
    
    def get_topic_subscribers(self, topic: str) -> List[str]:
        """Get all agents subscribed to a topic"""
        return self.dtmac.get_topic_subscribers(topic) 