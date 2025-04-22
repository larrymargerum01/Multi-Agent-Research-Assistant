#!/usr/bin/env python

import os
import uuid
import pytest
import asyncio
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langsmith import testing as t

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

# Import the report generation agents
from open_deep_research.graph import builder
from open_deep_research.multi_agent import supervisor_builder

class CriteriaGrade(BaseModel):
    """Score the response against specific criteria."""
    grade: bool = Field(description="Does the response meet the provided criteria?")
    justification: str = Field(description="The justification for the grade and score, including specific examples from the response.")

# Create a global LLM for evaluation to avoid recreating it for each test
# Use environment variable for the evaluation model if provided, otherwise default to gpt-4.1
eval_model = os.environ.get("EVAL_MODEL", "openai:gpt-4-turbo")
criteria_eval_llm = init_chat_model(eval_model)
criteria_eval_structured_llm = criteria_eval_llm.with_structured_output(CriteriaGrade)

RESPONSE_CRITERIA_SYSTEM_PROMPT = """
You are evaluating the quality of a research report. Please assess the report against the following criteria, being especially strict about section relevance.

1. Topic Relevance (Overall): Does the report directly address the user's input topic thoroughly?

2. Section Relevance (Critical): CAREFULLY assess each individual section for relevance to the main topic:
   - Identify each section by its ## header
   - For each section, determine if it is directly relevant to the primary topic
   - Flag any sections that seem tangential, off-topic, or only loosely connected to the main topic
   - A high-quality report should have NO irrelevant sections

3. Structure and Flow: Do the sections flow logically from one to the next, creating a cohesive narrative?

4. Introduction Quality: Does the introduction effectively provide context and set up the scope of the report?

5. Conclusion Quality: Does the conclusion meaningfully summarize key findings and insights from the report?

6. Section Headers: Are section headers properly formatted with Markdown (# for title, ## for sections, ### for subsections)?

7. Citations: Does the report properly cite sources?

8. Overall Quality: Is the report well-researched, accurate, and professionally written?

Evaluation Instructions:
- Be STRICT about section relevance - ALL sections must clearly connect to the primary topic
- A report with even ONE irrelevant section should be considered flawed
- You must individually mention each section by name and assess its relevance
- Provide specific examples from the report to justify your evaluation for each criterion
- The report fails if any sections are irrelevant to the main topic, regardless of other qualities
""" 

@pytest.mark.langsmith
def test_response_criteria_evaluation():
    """Test if a report meets the specified quality criteria."""
    # Get agent type from environment variable
    research_agent = os.environ.get("RESEARCH_AGENT", "multi_agent")
    print(f"Testing {research_agent} report generation...")
    
    # Log inputs to LangSmith
    t.log_inputs({
        "agent_type": research_agent, 
        "test": "report_quality_evaluation",
        "description": f"Testing report quality for {research_agent}"
    })
 
    # Run the appropriate agent based on the parameter
    if research_agent == "multi_agent":

        # Initial messages
        initial_msg = [{"role": "user", "content": "What is model context protocol?"}]
        followup_msg = [{"role": "user", "content": "high-level overview of MCP, tell me about interesting specific MCP servers, developer audience, just focus on MCP. generate the report now and don't ask any more follow-up questions."}]

        # Checkpointer for the multi-agent approach
        checkpointer = MemorySaver()
        graph = supervisor_builder.compile(checkpointer=checkpointer)

        # Create configuration with custom models if provided
        config = {
            "thread_id": str(uuid.uuid4()),
            "search_api": os.environ.get("SEARCH_API", "tavily"),
            "supervisor_model": os.environ.get("SUPERVISOR_MODEL", "anthropic:claude-3-7-sonnet-latest"),
            "researcher_model": os.environ.get("RESEARCHER_MODEL", "anthropic:claude-3-5-sonnet-latest"),
        }
        
        thread_config = {"configurable": config}

        # Run the workflow with asyncio
        asyncio.run(graph.ainvoke({"messages": initial_msg}, config=thread_config))
        asyncio.run(graph.ainvoke({"messages": followup_msg}, config=thread_config))
        
        # Get the final state once both invocations are complete
        final_state = graph.get_state(thread_config)
        print(f"Final state values: {final_state.values}")
        report = final_state.values.get('final_report', "No report generated")
        print(f"Report length: {len(report)}")

    elif research_agent == "graph":
        
         # Topic query 
        topic_query = "What is model context protocol? high-level overview of MCP, tell me about interesting specific MCP servers, developer audience, just focus on MCP"
   
        # Checkpointer for the graph approach
        checkpointer = MemorySaver()
        graph = builder.compile(checkpointer=checkpointer)
        
        # Configuration for the graph agent with environment variables
        thread = {"configurable": {
            "thread_id": str(uuid.uuid4()),
            "search_api": os.environ.get("SEARCH_API", "tavily"),
            "planner_provider": os.environ.get("PLANNER_PROVIDER", "anthropic"),
            "planner_model": os.environ.get("PLANNER_MODEL", "claude-3-7-sonnet-latest"),
            "writer_provider": os.environ.get("WRITER_PROVIDER", "anthropic"),
            "writer_model": os.environ.get("WRITER_MODEL", "claude-3-5-sonnet-latest"),
            "max_search_depth": 2,
        }}
        
        async def run_graph_agent(thread):    
            # Run the graph until the interruption
            async for event in graph.astream({"topic":topic_query}, thread, stream_mode="updates"):
                if '__interrupt__' in event:
                    interrupt_value = event['__interrupt__'][0].value

            # Pass True to approve the report plan 
            async for event in graph.astream(Command(resume=True), thread, stream_mode="updates"):
                print(event)
                print("\n")
            
            final_state = graph.get_state(thread)
            report = final_state.values.get('final_report', "No report generated")
            return report
    
        report = asyncio.run(run_graph_agent(thread))

    # Evaluate the report against our quality criteria
    eval_result = criteria_eval_structured_llm.invoke([
        {"role": "system", "content": RESPONSE_CRITERIA_SYSTEM_PROMPT},
        {"role": "user", "content": f"""\n\n Report: \n\n{report}\n\nEvaluate whether the report meets the criteria and provide detailed justification for your evaluation."""}
    ])

    # Extract section headers for analysis
    import re
    section_headers = re.findall(r'##\s+([^\n]+)', report)
    
    # Print the evaluation results
    print(f"Evaluation result: {'PASSED' if eval_result.grade else 'FAILED'}")
    print(f"Report contains {len(section_headers)} sections: {', '.join(section_headers)}")
    print(f"Justification: {eval_result.justification}")
    
    # Log outputs to LangSmith
    t.log_outputs({
        "report": report,
        "evaluation_result": eval_result.grade,
        "justification": eval_result.justification,
        "report_length": len(report),
        "section_count": len(section_headers),
        "section_headers": section_headers,
    })
    
    # Test passes if the evaluation criteria are met
    assert eval_result.grade