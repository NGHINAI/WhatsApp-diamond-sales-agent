import json
from typing import Dict, Any, List, Tuple, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from config.config import OPENAI_API_KEY, AGENT_MODEL, MAX_HISTORY_MESSAGES
from database.queries import DiamondQueries, ChatHistoryQueries
from agent.prompts import SYSTEM_PROMPT
from agent.tools import get_agent_tools

# Define the agent state
class AgentState(BaseModel):
    """State for the diamond sales agent."""
    chat_id: str = Field(..., description="The chat ID (phone number) of the customer")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Chat message history")
    current_input: Optional[str] = Field(None, description="Current user input")
    current_output: Optional[str] = Field(None, description="Current agent output")
    diamond_context: Dict[str, Any] = Field(default_factory=dict, description="Context about diamonds being discussed")
    customer_preferences: Dict[str, Any] = Field(default_factory=dict, description="Customer preferences for diamonds")
    conversation_summary: Optional[str] = Field(None, description="Summary of the conversation so far")
    next_steps: List[str] = Field(default_factory=list, description="Next steps for the agent to take")

# Create the agent using LangGraph
class DiamondSalesAgent:
    """Agent for handling diamond sales inquiries via WhatsApp."""
    
    def __init__(self):
        """Initialize the diamond sales agent."""
        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=AGENT_MODEL, temperature=0.2)
        self.tools = get_agent_tools()
        self.tool_executor = ToolExecutor(self.tools)
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the agent workflow graph."""
        # Define the workflow
        workflow = StateGraph(AgentState)
        
        # Define the nodes
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("update_state", self._update_state)
        
        # Define the edges
        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_edge("generate_response", "execute_tools")
        workflow.add_edge("execute_tools", "update_state")
        workflow.add_edge("update_state", END)
        
        # Set the entry point
        workflow.set_entry_point("retrieve_context")
        
        return workflow.compile()
    
    async def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve context for the conversation."""
        # Get chat history
        chat_history = await ChatHistoryQueries.get_recent_conversation(
            chat_id=state.chat_id, 
            limit=MAX_HISTORY_MESSAGES
        )
        
        # Format messages for the agent
        messages = []
        for msg in chat_history:
            if msg["sender"] == "user":
                messages.append({"role": "user", "content": msg["message"]})
            else:
                messages.append({"role": "assistant", "content": msg["message"]})
        
        # Get conversation summary
        summary = await ChatHistoryQueries.get_conversation_summary(state.chat_id)
        
        # Update state
        state.messages = messages
        state.conversation_summary = summary
        
        return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate a response or tool calls based on the conversation."""
        # Create the prompt
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        
        # Add conversation summary if available
        if state.conversation_summary:
            system_message.content += f"\n\nConversation summary: {state.conversation_summary}"
        
        # Add diamond context if available
        if state.diamond_context:
            context_str = json.dumps(state.diamond_context, indent=2)
            system_message.content += f"\n\nDiamond context: {context_str}"
        
        # Add customer preferences if available
        if state.customer_preferences:
            prefs_str = json.dumps(state.customer_preferences, indent=2)
            system_message.content += f"\n\nCustomer preferences: {prefs_str}"
        
        # Create message history
        messages = [system_message]
        for msg in state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current input
        messages.append(HumanMessage(content=state.current_input))
        
        # Generate response
        response = await self.llm.ainvoke(messages)
        
        # Check if the response contains tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            state.next_steps = [tool_call.name for tool_call in response.tool_calls]
            state.current_output = response.tool_calls
        else:
            state.current_output = response.content
            state.next_steps = []
        
        return state
    
    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute any tools called by the agent."""
        if not state.next_steps:
            return state
        
        # Execute each tool call
        tool_results = []
        for tool_call in state.current_output:
            try:
                # Create tool invocation
                invocation = ToolInvocation(
                    name=tool_call.name,
                    arguments=json.loads(tool_call.arguments)
                )
                
                # Execute the tool
                result = await self.tool_executor.ainvoke(invocation)
                tool_results.append(result)
                
                # Update diamond context if this was a diamond query
                if tool_call.name in ["search_diamonds", "get_diamond_details", "recommend_diamonds"]:
                    state.diamond_context[tool_call.name] = result
                
                # Update customer preferences if this was a preference extraction
                if tool_call.name == "extract_preferences":
                    state.customer_preferences.update(result)
            
            except Exception as e:
                tool_results.append({"error": str(e)})
        
        # Generate a response based on tool results
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        messages = [system_message]
        for msg in state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current input
        messages.append(HumanMessage(content=state.current_input))
        
        # Add tool results
        tool_results_str = json.dumps(tool_results, indent=2)
        messages.append(AIMessage(content=f"I've looked up some information for you: {tool_results_str}"))
        
        # Generate final response
        response = await self.llm.ainvoke(messages)
        state.current_output = response.content
        
        return state
    
    async def _update_state(self, state: AgentState) -> AgentState:
        """Update the agent state with the final response."""
        # Add the final response to messages
        state.messages.append({"role": "user", "content": state.current_input})
        state.messages.append({"role": "assistant", "content": state.current_output})
        
        # Limit message history
        if len(state.messages) > MAX_HISTORY_MESSAGES * 2:  # *2 for user+assistant pairs
            state.messages = state.messages[-MAX_HISTORY_MESSAGES * 2:]
        
        return state
    
    async def handle_message(self, chat_id: str, message: str) -> str:
        """Handle an incoming message and generate a response.
        
        Args:
            chat_id: Chat ID (phone number) of the sender
            message: Message text from the user
            
        Returns:
            Response text to send back
        """
        # Create initial state
        state = AgentState(
            chat_id=chat_id,
            current_input=message
        )
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(state)
        
        # Return the final response
        return final_state.current_output

# Singleton instance
diamond_agent = DiamondSalesAgent()