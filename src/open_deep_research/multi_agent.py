from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
import json
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import StructuredTool, tool
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.constants import START, END, Send
from langgraph.graph import MessagesState, StateGraph
from langgraph.types import Command

# Define schemas
class Section(TypedDict):
    """A section of the research report."""
    name: str
    description: str
    research: bool
    content: str

class Sections(TypedDict):
    """Report sections schema."""
    sections: List[Section]

class SearchResult(TypedDict):
    """Result from a search query."""
    query: str
    content: str

# Define states
class SupervisorState(MessagesState):
    """State for the supervisor agent."""
    topic: str
    sections: Optional[List[Section]]
    completed_sections: List[Section]

class WorkerState(MessagesState):
    """State for worker agents."""
    topic: str
    section: Section
    search_results: Optional[str]
    search_iterations: int
    completed_sections: List[Section]

# Create tools
tavily_search = TavilySearchResults(max_results=5)

@tool
def mark_section_complete(section_content: Annotated[str, "The completed content for the section"]) -> str:
    """
    Mark a section as complete with the provided content.
    Return a confirmation message.
    """
    return "Section completed successfully."

# Create supervisor tool functions
def create_supervisor_tools():
    """Create tools for the supervisor agent."""
    
    sections_schema = {
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "research": {"type": "boolean"},
                        "content": {"type": "string"}
                    },
                    "required": ["name", "description", "research", "content"]
                }
            }
        },
        "required": ["sections"]
    }

    sections_tool = StructuredTool.from_function(
        func=lambda sections: json.dumps(sections),
        name="Sections",
        description="Create sections for the research report",
        args_schema=Sections,
        return_direct=True
    )
    
    return [sections_tool]

# Create nodes
def create_supervisor_node():
    """Create the supervisor node for planning and managing the research process."""

    supervisor_prompt = """You are a research supervisor coordinating a team to create a comprehensive research report.

Your responsibilities:
1. Create a research plan with appropriate sections based on the user's topic
2. Assign research tasks to workers
3. Track progress and collect completed sections
4. Write the introduction and conclusion once all research is complete

For the research plan, consider:
- What are the key aspects of the topic that need coverage?
- What background information is necessary?
- What are the current developments, applications, or implications?

You will first create a structured plan with sections.
Each section should have:
- name: The section title
- description: A brief description of what should be covered
- research: Boolean flag indicating if this section needs research (true for all content sections, false for intro/conclusion)
- content: Initially empty string

The Introduction and Conclusion sections should have research=false, all other sections should have research=true.

Use the Sections tool to create your plan with the appropriate schema.
"""

    # Initialize the LLM with tools
    llm = init_chat_model("openai:o3")
    llm_with_tools = llm.bind_tools(create_supervisor_tools())

    def supervisor_node(state: SupervisorState):
        """Process the supervisor's actions."""
        
        # If we already have sections, update the prompt to reflect that
        if state.get("sections"):
            completed_sections = state.get("completed_sections", [])
            completed_names = [s["name"] for s in completed_sections]
            
            update_prompt = f"""You are a research supervisor coordinating a team to create a comprehensive research report on {state['topic']}.

You have created the following sections:
{json.dumps([s for s in state['sections']], indent=2)}

The following sections have been completed:
{', '.join(completed_names) if completed_names else 'None yet'}

When all research sections are complete, you should write the introduction and conclusion sections.
"""
            
            messages = [
                SystemMessage(content=update_prompt)
            ] + state.get("messages", [])
        else:
            # Initial prompt
            messages = [
                SystemMessage(content=supervisor_prompt),
                HumanMessage(content=f"I need a research report on the topic: {state['topic']}. Please create a plan with appropriate sections.")
            ] + state.get("messages", [])
        
        # Invoke the model
        response = llm_with_tools.invoke(messages)
        
        return {"messages": state.get("messages", []) + [response]}

    return supervisor_node

def create_worker_node():
    """Create the worker node for researching and writing sections."""

    worker_prompt = """You are a research assistant responsible for gathering information and writing a section of a research report.

Your responsibilities:
1. Review the assigned section topic carefully
2. Analyze the search results to extract relevant information
3. Synthesize the information into a well-written section
4. Include citations when appropriate
5. Ensure the section addresses the topic thoroughly

Guidelines for writing:
- Be concise but comprehensive
- Use clear topic sentences and structured paragraphs
- Synthesize information rather than just summarizing sources
- Maintain an objective tone
- Include relevant data, examples, or case studies if available

When you've completed the section, use the mark_section_complete tool with your final content.
"""

    # Initialize the LLM with tools
    llm = init_chat_model("openai:o3")
    llm_with_tools = llm.bind_tools([mark_section_complete])

    def worker_node(state: WorkerState):
        """Process the worker's actions."""
        
        # If we don't have search results yet, perform the search
        if not state.get("search_results"):
            query = f"{state['topic']} {state['section']['name']} {state['section']['description']}"
            results = tavily_search.invoke(query)
            
            formatted_results = "\n\n".join([
                f"Source: {result.get('source', 'Unknown')}\nTitle: {result.get('title', 'No title')}\nContent: {result.get('content', 'No content')}"
                for result in results
            ])
            
            # Create messages with search results
            messages = [
                SystemMessage(content=worker_prompt),
                HumanMessage(content=f"""You need to write a section on "{state['section']['name']}" for a report about {state['topic']}.

Section description: {state['section']['description']}

Here are the search results to use as sources:

{formatted_results}

Please write a comprehensive section that addresses the topic thoroughly.
""")
            ] + state.get("messages", [])
            
            # Update state with search results
            state["search_results"] = formatted_results
        else:
            # Continue with existing messages
            messages = state.get("messages", [])
        
        # Invoke the model
        response = llm_with_tools.invoke(messages)
        
        return {"messages": messages + [response]}

    return worker_node

# Define edge functions
def route_supervisor(state: SupervisorState) -> str:
    """Route from the supervisor node based on tool calls."""
    
    messages = state.get("messages", [])
    if not messages:
        return "supervisor"  # Initial call
    
    last_message = messages[-1]
    
    # Check if the last message was a tool call to Sections
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "Sections":
                # Parse the sections from the tool call
                try:
                    sections_json = json.loads(tool_call["args"])
                    sections = sections_json.get("sections", [])
                    
                    # Route research tasks to workers
                    research_sections = [s for s in sections if s.get("research", True)]
                    if research_sections:
                        # Use Send API to dispatch research tasks
                        return [
                            Send("worker", {
                                "topic": state["topic"], 
                                "section": section, 
                                "search_iterations": 0, 
                                "search_results": None,
                                "messages": []
                            }) 
                            for section in research_sections
                        ]
                    
                    return "supervisor"  # No research sections
                except Exception:
                    return "supervisor"  # Error parsing sections
    
    # If all sections are complete, continue with supervisor to generate intro/conclusion
    if state.get("sections") and len(state.get("completed_sections", [])) == len([s for s in state["sections"] if s.get("research", True)]):
        return "supervisor"
    
    # Otherwise, continue normally
    return "supervisor"

def route_worker(state: WorkerState) -> str:
    """Route from the worker node based on tool calls."""
    
    messages = state.get("messages", [])
    if not messages:
        return "worker"  # Initial call
    
    last_message = messages[-1]
    
    # Check if the last message was a tool call to mark_section_complete
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "mark_section_complete":
                # Extract the section content
                section_content = tool_call["args"].get("section_content", "")
                
                # Update the section content
                section = state["section"]
                section["content"] = section_content
                
                # Return to supervisor with completed section
                return Command(
                    goto="supervisor",
                    update={"completed_sections": [section]}
                )
    
    # Otherwise, continue with worker
    return "worker"

# Build the multi-agent graph
def build_multi_agent_graph():
    """Build the multi-agent research graph."""
    
    # Create the main graph
    main_graph = StateGraph(SupervisorState)
    
    # Add nodes
    main_graph.add_node("supervisor", create_supervisor_node())
    
    # Create worker graph
    worker_graph = StateGraph(WorkerState)
    worker_graph.add_node("worker", create_worker_node())
    worker_graph.add_conditional_edges("worker", route_worker)
    worker = worker_graph.compile()
    
    # Add worker to main graph
    main_graph.add_node("worker", worker)
    
    # Add edges
    main_graph.add_edge(START, "supervisor")
    main_graph.add_conditional_edges("supervisor", route_supervisor)
    main_graph.add_edge("worker", "supervisor")
    
    # Compile and return
    return main_graph.compile()

# Run function
def run_multi_agent_research(topic: str):
    """Run the multi-agent research process on a topic."""
    
    # Build the graph
    graph = build_multi_agent_graph()
    
    # Initialize state
    initial_state = SupervisorState(
        topic=topic,
        sections=None,
        completed_sections=[],
        messages=[]
    )
    
    # Run the workflow
    for event in graph.stream(initial_state):
        # Process streaming events as needed
        pass
    
    # Return the final result from the graph
    result = graph.invoke(initial_state)
    
    # Format final report
    if result.get("sections") and result.get("completed_sections"):
        # Create the final report
        completed_sections = {s["name"]: s["content"] for s in result["completed_sections"]}
        
        report = {
            "topic": topic,
            "sections": []
        }
        
        for section in result["sections"]:
            section_name = section["name"]
            section_content = completed_sections.get(section_name, "")
            report["sections"].append({
                "name": section_name,
                "content": section_content
            })
        
        return report
    
    return {"topic": topic, "error": "Research process did not complete successfully."}