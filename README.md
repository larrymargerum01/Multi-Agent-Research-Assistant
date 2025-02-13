# Open Deep Research
 
Open Deep Research is a web research assistant that generates comprehensive reports on any topic following a workflow similar to [OpenAI](https://openai.com/index/introducing-deep-research/) and [Gemini](https://blog.google/products/gemini/google-gemini-deep-research/) Deep Research.However, it allows you to customize the models, prompts, report structure, search API, and research depth. Specifically, you can customize:

- provide an outline with a desired report structure
- set the planner model (e.g., DeepSeek, OpenAI reasoning model, etc)
- give feedback on the plan of report sections and iterate until user approval 
- set the search API (e.g., Tavily, Perplexity) and # of searches to run for each research iteration
- set the depth of search for each section (# of iterations of writing, reflection, search, re-write)
- customize the writer model (e.g., Anthropic)

Short summary:
<video src="https://github.com/user-attachments/assets/d9a66221-59cf-4c71-916d-33fdf3457fe8" controls></video>

## 📺 Video Tutorials

## 🚀 Quickstart

Clone the repository:
```bash
git clone https://github.com/langchain-ai/open_deep_research.git
cd open_deep_research
```

Select a web search tool, by default it is Tavily:

* [Tavily API](https://tavily.com/)
* [Perplexity API](https://www.perplexity.ai/hub/blog/introducing-the-sonar-pro-api)

Select a writer model, by default it is Anthropic:

* [Anthropic](https://www.anthropic.com/)

Select a planner model, by default it is OpenAI:
* [OpenAI](https://openai.com/)
* [Groq](https://groq.com/)

Set API keys for your selections above:

```bash
cp .env.example .env
```

Edit the `.env` file with your API keys (e.g., the API keys for default selections are shown below):

```bash
export TAVILY_API_KEY=<your_tavily_api_key>
export ANTHROPIC_API_KEY=<your_anthropic_api_key>
export OPENAI_API_KEY=<your_openai_api_key>
```

Launch the assistant with the LangGraph server, which will open in your browser:

#### Mac

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and start the LangGraph server
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev
```

#### Windows

```powershell
# Install dependencies 
pip install -e .
pip install langgraph-cli[inmem]

# Start the LangGraph server
langgraph dev
```

Use this to open the Studio UI:
```
- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs
```

(1) Provide a `Topic` and hit `Submit`:

![Screenshot 2025-01-31 at 8 12 21 PM](https://github.com/user-attachments/assets/70ce93d8-c29f-49ea-9e06-19377d8cac7b)

(2) This will generate a report plan:

![Screenshot 2025-01-31 at 8 12 44 PM](https://github.com/user-attachments/assets/a464e71c-e122-422f-9736-62f8bf0b8777)

(3) You can review the section of the plan in Studio. If you like them, hit `Continue`.

(4) If you want to add feedback, add `Feedback On Report Plan` and `Submit`:

![Screenshot 2025-01-31 at 8 13 40 PM](https://github.com/user-attachments/assets/d82102f3-0adb-4eca-ae96-2fe720b22b71)

(5) If you have given feedback, continue iterating until you are happy and then select `Accept Report Plan`:

![Screenshot 2025-01-31 at 8 14 19 PM](https://github.com/user-attachments/assets/1d693e16-79df-4823-8355-482999546922)

## 📖 Customizing the report

You can customize the research assistant's behavior through several parameters:

- `report_structure`: Define a custom structure for your report (defaults to a standard research report format)
- `number_of_queries`: Number of search queries to generate per section (default: 2)
- `max_search_depth`: Maximum number of reflection and search iterations (default: 2)
- `planner_provider`: Model provider for planning phase (default: "openai", but can be "groq")
- `planner_model`: Specific model for planning (default: "o3-mini", but can be any Groq hosted model such as "deepseek-r1-distill-llama-70b")
- `writer_model`: Model for writing the report (default: "claude-3-5-sonnet-latest")
- `search_api`: API to use for web searches (default: Tavily)

These configurations allow you to fine-tune the research process based on your needs, from adjusting the depth of research to selecting specific AI models for different phases of report generation.

## How it works
   
1. `Plan and Execute` - Open Deep Research follows a [plan-and-execute workflow](https://github.com/assafelovic/gpt-researcher) that separates planning from research, allowing for human-in-the-loop approval of a report plan before the more time-consuming research phase. It uses, by default, a [reasoning model](https://www.youtube.com/watch?v=f0RbwrBcFmc) to plan the report sections. During this phase, it uses web search to gather general information about the report topic to help in planning the report sections. But, it also accepts a report structure from the user to help guide the report sections as well as human feedback on the report plan.
   
2. `Research and Write` - Each section of the report is written in parallel. The research assistant uses web search via [Tavily API](https://tavily.com/) or [Perplexity](https://www.perplexity.ai/hub/blog/introducing-the-sonar-pro-api) to gather information about each section topic. It will reflect on each report section and suggest follow-up questions for web search. This "depth" of research will proceed for any many iterations as the user wants. Any final sections, such as introductions and conclusions, are written after the main body of the report is written, which helps ensure that the report is cohesive and coherent. The planner determines main body versus final sections during the planning phase.

3. `Managing different types` - Open Deep Research is built on LangGraph, which has native support for configuration management [using assistants](https://langchain-ai.github.io/langgraph/concepts/assistants/). The report `structure` is a field in the graph configuration, which allows users to create different assistants for different types of reports. 

## UX

### Local deployment

Follow the [quickstart](#quickstart) to start LangGraph server locally.

### Hosted deployment
 
You can easily deploy to [LangGraph Platform ](https://langchain-ai.github.io/langgraph/concepts/#deployment-options). 
