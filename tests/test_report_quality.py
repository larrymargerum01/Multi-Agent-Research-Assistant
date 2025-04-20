#!/usr/bin/env python

import uuid
import asyncio
import importlib
import sys
import os
import pytest
from typing import Dict, List, Any, Tuple
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
criteria_eval_llm = init_chat_model("openai:gpt-4o")
criteria_eval_structured_llm = criteria_eval_llm.with_structured_output(CriteriaGrade)

RESPONSE_CRITERIA_SYSTEM_PROMPT = """
You are evaluating the quality of a research report. Please assess the report against the following criteria:

1. Topic Relevance: Does the report directly address the user's input topic thoroughly?
2. Structure and Flow: Do the sections flow logically from one to the next, creating a cohesive narrative?
3. Introduction Quality: Does the introduction effectively provide context and set up the scope of the report?
4. Conclusion Quality: Does the conclusion meaningfully summarize key findings and insights from the report?
5. Section Headers: Are section headers properly formatted with Markdown (# for title, ## for sections, ### for subsections)?
6. Citations: Does the report properly cite sources?
7. Overall Quality: Is the report well-researched, accurate, and professionally written?

Provide specific examples from the report to justify your evaluation for each criterion.
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
        followup_msg = [{"role": "user", "content": "high-level overview of MCP, tell me about interesting specific MCP servers, developer audience, just focus on MCP."}]

        # Checkpointer for the multi-agent approach
        checkpointer = MemorySaver()
        graph = supervisor_builder.compile(checkpointer=checkpointer)

        # Run the multi-agent with initial query and follow-up clarification
        thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # Run initial question
        graph.invoke({"messages": initial_msg}, config=thread_config)
        
        # Run follow-up clarification 
        graph.invoke({"messages": followup_msg}, config=thread_config)
        
        # Get the final state and extract the report
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
        
        # Configuration for the graph agent
        thread = {"configurable": {
            "thread_id": str(uuid.uuid4()),
            "search_api": "tavily",
            "planner_provider": "openai",
            "planner_model": "o3-mini",
            "writer_provider": "openai",
            "writer_model": "o3-mini",
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

    # Print the evaluation results
    print(f"Evaluation result: {'PASSED' if eval_result.grade else 'FAILED'}")
    print(f"Justification: {eval_result.justification}")
        
    # Log outputs to LangSmith
    t.log_outputs({
        "report": report,
        "evaluation_result": eval_result.grade,
        "justification": eval_result.justification,
        "report_length": len(report)
    })
    
    # Test passes if the evaluation criteria are met
    assert eval_result.grade