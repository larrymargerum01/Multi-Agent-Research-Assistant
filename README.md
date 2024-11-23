# Report mAIstro

Report mAIstro is an agent for generating reports based on user-supplied topics following a [plan-and-execute workflow](https://github.com/assafelovic/gpt-researcher).

## Key Concepts

1. `Topic-Driven Reports` - Generate comprehensive reports based on user-specified topics, with flexibility to accommodate various research needs.

2. `Natural Language Report Templates` - Define report structures using plain English, supporting multiple formats:
   - Market Analysis: Compare products, services, or companies across key metrics
   - Industry Research: Analyze market trends, innovations, and future outlook
   - Strategic Case Studies: Extract actionable insights from business histories
   - Technical Guides: Step-by-step implementation instructions
   - Custom Templates: Design your own report structure in natural language

3. `Three-Phase Research Engine` - Ensures comprehensive and well-structured reports:
   - Planning: Generate detailed outlines based on template and topic
   - Research: Parallel processing of research tasks for each section
   - Synthesis: Create cohesive introduction and conclusion based on findings

4. `Advanced Web Research` - Powered by [Tavily API](https://tavily.com/) for intelligent information gathering:
   - Context-Aware Search:
     * Real-time data for trend analysis (filtered by recency)
     * Comprehensive search for strategic and comparative reports
     * Academic sources for technical documentation
   - Multi-Query Strategy: Generate varied search queries per section
   - Parallel Processing: Concurrent research across all sections
   - Source Validation: Automatic verification of information reliability

## Quick Start

1. Populate the `.env` file: 
```
$ cp .env.example .env
```

2. Load the graph in LangGraph Studio [here](https://github.com/langchain-ai/langgraph-studio?tab=readme-ov-file#download).

## Testing in notebook

Install dependencies and create virtual environment:
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

## Deploying to LangGraph Platform 

TO ADD