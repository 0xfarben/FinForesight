from typing import Dict, Any
import asyncio
from .dtmac import DTMAC
from .data_analyst_agent import DataAnalystAgent
from .trade_strategy_agent import TradeStrategyAgent
from .trade_advisor_agent import TradeAdvisorAgent
from .risk_advisor_agent import RiskAdvisorAgent

class AgentOrchestrator:
    def __init__(self):
        # Initialize DTMAC
        self.dtmac = DTMAC()
        
        # Initialize agents
        self.agents = {
            "data_analyst": DataAnalystAgent(self.dtmac),
            "trade_strategy": TradeStrategyAgent(self.dtmac),
            "trade_advisor": TradeAdvisorAgent(self.dtmac),
            "risk_advisor": RiskAdvisorAgent(self.dtmac)
        }
        
        # Define system-wide topics
        self.system_topics = {
            "market_data": ["data_analyst", "trade_strategy", "trade_advisor", "risk_advisor"],
            "analysis_results": ["trade_strategy", "trade_advisor", "risk_advisor"],
            "trading_signals": ["trade_advisor", "risk_advisor"],
            "risk_alerts": ["trade_strategy", "trade_advisor"],
            "economic_data": ["trade_advisor", "risk_advisor"]
        }
    
    async def start(self):
        """Start the agent system"""
        # Register system topics
        for topic, agent_ids in self.system_topics.items():
            for agent_id in agent_ids:
                if agent_id in self.agents:
                    self.dtmac.register_agent(agent_id, [topic])
        
        # Start agent-specific tasks
        tasks = []
        for agent in self.agents.values():
            if hasattr(agent, 'start'):
                tasks.append(asyncio.create_task(agent.start()))
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    
    async def process_user_request(self, request: Dict[str, Any]):
        """Process a user request through the agent system"""
        request_type = request.get("type")
        
        if request_type == "analyze":
            # Forward to data analyst
            await self.dtmac.send_message(
                sender="orchestrator",
                recipients=["data_analyst"],
                content=request,
                message_type="analysis_request",
                priority=MessagePriority.HIGH
            )
        elif request_type == "trade_advice":
            # Forward to trade advisor
            await self.dtmac.send_message(
                sender="orchestrator",
                recipients=["trade_advisor"],
                content=request,
                message_type="advice_request",
                priority=MessagePriority.NORMAL
            )
        elif request_type == "risk_assessment":
            # Forward to risk advisor
            await self.dtmac.send_message(
                sender="orchestrator",
                recipients=["risk_advisor"],
                content=request,
                message_type="risk_assessment_request",
                priority=MessagePriority.HIGH
            )
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get the current status of all agents"""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = await agent.get_status()
        return status
    
    async def stop(self):
        """Stop the agent system"""
        for agent in self.agents.values():
            if hasattr(agent, 'stop'):
                await agent.stop() 