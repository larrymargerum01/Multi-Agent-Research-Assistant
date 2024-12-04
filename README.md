# Report mAIstro

Report mAIstro creates easily customizable reports on any user-supplied topic.

> See [report examples here](report_examples/reports/)!

![report_mAIstro](https://github.com/user-attachments/assets/720aae16-dc68-4725-a880-1e4e0c7e6fd4)

## Quickstart

1. Populate the `.env` file: 
```
$ cp .env.example .env
```

2. Load this folder in [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio?tab=readme-ov-file#download) 

![Screenshot 2024-11-22 at 4 03 47 PM](https://github.com/user-attachments/assets/34a5504d-fa97-4076-9bb8-2f0ecc0352ca)

3. Optionally, provide a description of the report structure you want as a configuration. 

> See [some example report types here](report_examples/reports/)! 

![Screenshot 2024-11-22 at 4 04 47 PM](https://github.com/user-attachments/assets/7a488a5e-a768-4113-bce4-3fb2b479dc5e)

4. Provide a topic and run the graph to produce a report

## Motivation 

[RAG systems](https://github.com/langchain-ai/rag-from-scratch) are a powerful tool for interacting with LLMs, enabling quick and accurate question-answering capabilities. However, individual questions often serve a larger purpose: informing decisions and strategies. While [reports are essential decision-making tools](https://jxnl.co/writing/2024/06/05/predictions-for-the-future-of-rag/), creating comprehensive reports remains a time-consuming challenge. Report mAIstro transforms this process by leveraging LLMs to generate detailed reports through natural language, making report creation more accessible and efficient!

## Overview

| Phase | Objective | Report mAIstro Implementation |
|-------|-----------|------------------------------|
| Structure | How is the report organized? | Uses LLM to convert natural language instructions into structured section objects |
| Research | What are the information sources? | Web search via Tavily API |
| Orchestration | How is report generation managed? | Three-phase LangGraph workflow: 1) Planning to define sections, 2) Parallel research for content, 3) Generation of introduction/conclusion using gathered context |
| Reporting | How is the report presented to the user? | Generates structured markdown files |
| UX | What is the user interaction pattern? | Synchronous workflow where user provides inputs and waits for the report to be generated |

1. `Natural Language Report Creation` - Report mAIstro requires just two inputs from users:
   - A `topic` for the report
   - An optional `structure` in natural language

   While a topic alone can generate basic reports, we found that providing a structure significantly improves quality. For example, business strategy reports might need case studies, while comparative analyses benefit from structured comparison tables. The natural language structure acts as a flexible template, guiding the AI to create more focused and relevant reports.

2. `Plan and Execute` - Report mAIstro follows a [plan-and-execute workflow](https://github.com/assafelovic/gpt-researcher) that separates planning from research, allowing for better resource management and significantly reducing overall report creation time:

   - **Planning Phase**: An LLM analyzes the user's `topic` and `structure` using a planning prompt to create the report sections first. 
   - **Research Phase**: The system parallelizes web research across all sections requiring external data:
     - Uses [Tavily API](https://tavily.com/) for targeted web searches
     - Processes multiple sections simultaneously for faster report generation
     - Synthesizes gathered information into coherent section content
   
3. `Sequential Writing` - The report generation follows a logical sequence:
   - First, completes all research-dependent sections in parallel
   - Then generates connecting sections like introductions and conclusions
   - Uses insights from research sections to create cohesive narratives
   - Maintains contextual awareness across all sections
   
   While this sequence can be customized via the `structure`, the default flow ensures that conclusions meaningfully incorporate research findings.

4. `Managing different types` - Report mAIstro is built on LangGraph, which has native support for configuration management [using assistants](https://langchain-ai.github.io/langgraph/concepts/assistants/). The report `structure` is a field in the graph configuration, which allows users to create different assistants for different types of reports. 

> See the provided [notebook](ntbk/report_maistro.ipynb) or [example reports](report_examples/reports/) for examples! These include:
>   - Market Analysis: Compare products, services, or companies across key metrics
>   - Industry Research: Analyze market trends, innovations, and future outlook
>   - Strategic Case Studies: Extract actionable insights from business histories
>   - Technical Guides: Step-by-step implementation instructions
>   - Custom Templates: Design your own report structure in natural language

## Testing in notebook

Create a virtual environment and install dependencies:
```
$ python3 -m venv report_maistro
$ source report_maistro/bin/activate
$ pip install -r requirements.txt
```

Supply your OpenAI API key:
```
$ cp .env.example .env
```

Run the notebook:
```
$ cd ntbk
$ jupyter notebook report_maistro.ipynb
```

## Deploying 

LangGraph Platform allows various [deployment options](https://langchain-ai.github.io/langgraph/concepts/#deployment-options). 
