from typing import Literal
import uuid

from langchain_core.messages import MessageLikeRepresentation
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from open_deep_research.graph import builder
from open_deep_research.multi_agent import supervisor_builder


async def generate_report_workflow(
    query: str,
    process_search_results: Literal["summarize", "split_and_rerank"] | None = None,
    include_source: bool = True
):
    """Generate a report using the open deep research workflow"""
    graph = builder.compile(checkpointer=MemorySaver())
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
        }
    }
    if include_source:
        config["configurable"]["include_source_str"] = True

    if process_search_results:
        config["configurable"]["process_search_results"] = process_search_results

    # Run the graph until the interruption
    await graph.ainvoke(
        {"topic": query},
        config
    )
    # Pass True to approve the report plan
    final_state = await graph.ainvoke(Command(resume=True), config)
    return final_state


async def generate_report_multi_agent(
    messages: list[MessageLikeRepresentation],
    process_search_results: Literal["summarize", "split_and_rerank"] | None = None,
    include_source: bool = True
):
    """Generate a report using the open deep research multi-agent architecture"""
    graph = supervisor_builder.compile()
    config = {"configurable": {}}
    if include_source:
        config["configurable"]["include_source_str"] = True

    if process_search_results:
        config["configurable"]["process_search_results"] = process_search_results

    final_state = await graph.ainvoke(
        # this is a hack
        {"messages": messages + [{"role": "user", "content": "Generate the report now and don't ask any more follow-up questions"}]},
        config
    )
    return final_state