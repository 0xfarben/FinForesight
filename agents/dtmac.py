from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
from enum import Enum
import json
import uuid

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class DTMessage:
    message_id: str
    sender: str
    recipients: List[str]
    content: Dict[str, Any]
    timestamp: datetime
    priority: MessagePriority
    message_type: str
    metadata: Dict[str, Any] = None

class DTMAC:
    def __init__(self):
        self.message_queue: Dict[str, List[DTMessage]] = {}  # Agent ID -> Message Queue
        self.message_handlers: Dict[str, Dict[str, callable]] = {}  # Agent ID -> {Message Type -> Handler}
        self.message_history: List[DTMessage] = []
        self.agent_topics: Dict[str, List[str]] = {}  # Agent ID -> List of topics
        self.message_routing_table: Dict[str, List[str]] = {}  # Topic -> List of agent IDs
        
    def register_agent(self, agent_id: str, topics: List[str]):
        """Register an agent with specific topics of interest"""
        self.message_queue[agent_id] = []
        self.message_handlers[agent_id] = {}
        self.agent_topics[agent_id] = topics
        
        # Update routing table
        for topic in topics:
            if topic not in self.message_routing_table:
                self.message_routing_table[topic] = []
            if agent_id not in self.message_routing_table[topic]:
                self.message_routing_table[topic].append(agent_id)
    
    def register_handler(self, agent_id: str, message_type: str, handler: callable):
        """Register a message handler for specific message type"""
        if agent_id not in self.message_handlers:
            self.message_handlers[agent_id] = {}
        self.message_handlers[agent_id][message_type] = handler
    
    async def send_message(self, 
                          sender: str, 
                          recipients: List[str], 
                          content: Dict[str, Any], 
                          message_type: str,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          metadata: Optional[Dict[str, Any]] = None):
        """Send a message to specific recipients"""
        message = DTMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            recipients=recipients,
            content=content,
            timestamp=datetime.now(),
            priority=priority,
            message_type=message_type,
            metadata=metadata
        )
        
        self.message_history.append(message)
        
        # Route message to recipients
        for recipient in recipients:
            if recipient in self.message_queue:
                self.message_queue[recipient].append(message)
                # Trigger message processing
                asyncio.create_task(self._process_message(recipient))
    
    async def broadcast_to_topic(self, 
                               sender: str, 
                               topic: str, 
                               content: Dict[str, Any], 
                               message_type: str,
                               priority: MessagePriority = MessagePriority.NORMAL):
        """Broadcast message to all agents subscribed to a topic"""
        if topic in self.message_routing_table:
            recipients = self.message_routing_table[topic]
            await self.send_message(sender, recipients, content, message_type, priority)
    
    async def _process_message(self, agent_id: str):
        """Process messages in the agent's queue"""
        while self.message_queue[agent_id]:
            message = self.message_queue[agent_id].pop(0)
            if message.message_type in self.message_handlers[agent_id]:
                handler = self.message_handlers[agent_id][message.message_type]
                await handler(message)
    
    def get_message_history(self, agent_id: Optional[str] = None) -> List[DTMessage]:
        """Get message history, optionally filtered by agent"""
        if agent_id:
            return [msg for msg in self.message_history 
                   if msg.sender == agent_id or agent_id in msg.recipients]
        return self.message_history
    
    def get_agent_topics(self, agent_id: str) -> List[str]:
        """Get topics an agent is subscribed to"""
        return self.agent_topics.get(agent_id, [])
    
    def get_topic_subscribers(self, topic: str) -> List[str]:
        """Get all agents subscribed to a topic"""
        return self.message_routing_table.get(topic, []) 