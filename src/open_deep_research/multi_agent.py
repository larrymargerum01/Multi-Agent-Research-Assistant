
from typing import List, Dict, Optional, Annotated, TypedDict, operator, Literal
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain_core.tools import InjectedToolCallId, tool
from langgraph_supervisor import create_supervisor, create_handoff_tool
from langgraph.prebuilt import InjectedState
from langgraph.graph import MessagesState
from langchain_tavily import TavilySearch

from langgraph.types import Command, Send
from langgraph.prebuilt import create_react_agent
from langgraph.graph import START, END, StateGraph

## LLM 
llm = init_chat_model(
    model="openai:o3-mini",
    temperature=0.0
)

## Tools 
tavily_search_tool = TavilySearch(
    max_results=5,
    topic="general",
)

class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Research scope for this section of the report.",
    )
    content: str = Field(
        description="The content of the section."
    )

@tool
class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the report.",
    )

@tool
class Introduction(BaseModel):
    name: str = Field(
        description="Name for the report.",
    )
    content: str = Field(
        description="The content of the introduction, giving an overview of the report."
    )

@tool
class Conclusion(BaseModel):
    name: str = Field(
        description="Name for the conclusion of the report.",
    )
    content: str = Field(
        description="The content of the conclusion, summarizing the report."
    )

@tool
class Done(BaseModel):
      """Tool to signal that the work is complete."""
      done: bool

# Handoff Tool
@tool()
def handoff_to_researchers(
    state: Annotated[dict, InjectedState], # What is this?
    tool_call_id: Annotated[str, InjectedToolCallId], # What is this?
):  
    # Tool Message
    tool_message = [{"role": "tool", 
    "content": f"Successfully transferred to research_agent team", 
    "name": "handoff_to_researchers", "tool_call_id": tool_call_id}]

    # Send to research_agent team
    return Command(
        graph=Command.PARENT,
        # Parallel handoffs to each researcher
        goto=[Send("research_agent", {"section": s, "messages": state['messages'] + tool_message}) for s in state['sections']],
        )

## State
class ReportStateOutput(TypedDict):
    final_report: str # Final report

class ReportState(MessagesState):
    sections: list[Section] # List of report sections 
    completed_sections: Annotated[list, operator.add] # Send() API key
    final_report: str # Final report

class SectionState(MessagesState):
    section: Section # Report section  
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API

class SectionOutputState(TypedDict):
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API

## Supervisor

SUPERVISOR_INSTRUCTIONS = """
You are scoping research for a report based on a user-provided topic.

### Your responsibilities:

1. **Clarify the Topic**  
   Engage with the user to clarify their intent. Ask follow-up questions to fully understand the topic, goals, constraints, and any preferences for the report.

2. **Gather Background Information**  
   Use the `tavily_search_tool` to collect relevant information about the topic. Use multiple focused queries to build context from different angles.

3. **Define Report Structure**  
   Once you understand the topic:
   - Use the `Sections` tool to define a structured outline of the report.
   - Each section should include a clear name and scope description.
   - Leave the content preview empty because the research agent will fill it in.
   - Ensure sections are scoped to be independently researchable.

4. **Delegate to Researchers**  
   After the sections are defined, call the `handoff_to_researchers` tool. This will send each section to the `research_agent` team for parallel research.

5. **Assemble the Final Report**  
   When all sections are returned:
   - Use the `Introduction` tool to generate a clear and informative introduction.
   - Use the `Conclusion` tool to summarize key insights and close the report.

6. **Finish the Workflow**  
   When the final report is complete, call the `Done` tool to signal that the work is finished.

### Additional Notes:
- You are a reasoning model. Think through problems step-by-step before acting.
- Use your tools wisely—especially the search tool—to improve research quality.
- Maintain a clear, informative, and professional tone throughout."""

# Tools
supervisor_tools = [tavily_search_tool, handoff_to_researchers, Introduction, Conclusion]
supervisor_tools_by_name = {tool.name: tool for tool in supervisor_tools}

def llm_call(state: ReportState):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            llm.bind_tools(supervisor_tools_by_name).invoke(
                [
                    {"role": "system",
                     "content": SUPERVISOR_INSTRUCTIONS
                    }
                ]
                + state["messages"]
            )
        ]
    }

def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    # Get the last message
    for tool_call in state["messages"][-1].tool_calls:
        # Get the tool
        tool = supervisor_tools_by_name[tool_call["name"]]
        # Perform the tool call
        observation = tool.invoke(tool_call["args"])
        # Append to messages 
        result.append([{"role": "tool", 
                        "content": observation, 
                        "name": tool_call["name"], 
                        "tool_call_id": tool_call["id"]}])
        # Update state depending on the tool call 
        if tool_call["name"] == "Sections":
            return {"messages": result, "sections": tool_call["args"]}
        if tool_call["name"] == "Introduction":
            return {"messages": result, "sections": [tool_call["args"]] + state["sections"]}
        if tool_call["name"] == "Conclusion":
            return {"messages": result, "sections": state["sections"] + [tool_call["args"]]}
        else:
            return {"messages": result}

def should_continue(state: MessagesState) -> Literal["environment", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "Action"
    
    # Otherwise research is complete and we can assemble the final report
    all_sections = "\n\n".join([s.content for s in state["sections"]])
    return Command(goto=END, update={"final_report": all_sections})

# Build workflow
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("environment", tool_node)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        # Name returned by should_continue : Name of next node to visit
        "Action": "environment",
        END: END,
    },
)
agent_builder.add_edge("environment", "llm_call")
supervisor = agent_builder.compile()


# Research Agent

RESEARCH_INSTRUCTIONS = """
You are a researcher responsible for completing a specific section of a report.

### Your goals:

1. **Understand the Section Scope**  
   Begin by reviewing the section name and description. This defines your research focus. Use it as your objective.

<Section Name>
{section_name}
</Section Name>

<Section Description>
{section_description}
</Section Description>

2. **Research the Topic**  
   Use the `tavily_search_tool` to gather relevant information and evidence. Search iteratively if needed to fully understand the section’s scope.

3. **Use the Section Tool**  
   Once you’ve gathered sufficient context, write a high-quality called the Section tool to write the section. Your content should:
   - `name`: The title of the section
   - `description`: The scope of research you completed 
   - `content`: The completed body of text for the section

---

### Reasoning Guidance

You are a reasoning model. Think through the task step-by-step before writing. Break down complex questions. If you're unsure about something, search again.

- You may reason internally before producing content.
- Your job is not to summarize randomly—it's to **research and synthesize a strong, scoped contribution** to a report.

---

### Notes:
- Do not write introductions or conclusions unless explicitly part of your section.
- Keep a professional, factual tone.
- If you do not have enough information to complete the section, search again or clarify your approach before continuing.
"""

# Tools
research_tools = [tavily_search_tool, Section]
research_tools_by_name = {tool.name: tool for tool in research_tools}

def llm_call(state: ReportState):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            llm.bind_tools(research_tools).invoke(
                [
                    {"role": "system",
                     "content": RESEARCH_INSTRUCTIONS.format(section_name=state["section"].name, section_description=state["section"].description)
                    }
                ]
                + state["messages"]
            )
        ]
    }

def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    # Get the last message
    for tool_call in state["messages"][-1].tool_calls:
        # Get the tool
        tool = research_tools_by_name[tool_call["name"]]
        # Perform the tool call
        observation = tool.invoke(tool_call["args"])
        # Append to messages 
        result.append([{"role": "tool", 
                        "content": observation, 
                        "name": tool_call["name"], 
                        "tool_call_id": tool_call["id"]}])
        # Update state depending on the tool call 
        if tool_call["name"] == "Section":
            return {"messages": result, "section": tool_call["args"]}
        else:
            return {"messages": result}

def should_continue(state: MessagesState) -> Literal["environment", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "Action"
    
    # Otherwise research is complete and we can assemble the final report
    all_sections = "\n\n".join([s.content for s in state["sections"]])
    return Command(goto=END, update={"final_report": all_sections})

# Build workflow
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("environment", tool_node)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        # Name returned by should_continue : Name of next node to visit
        "Action": "environment",
        END: END,
    },
)
agent_builder.add_edge("environment", "llm_call")
research_agent = agent_builder.compile()

research_team = create_supervisor(
    [research_agent, math_agent],
    model=model,
    supervisor_name="research_supervisor"
).compile(name="research_team")