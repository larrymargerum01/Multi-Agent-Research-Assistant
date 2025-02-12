# Open Deep Research
 
Open Deep Research is a web research assistant that generates comprehensive reports on any topic following a workflow similar to [OpenAI](https://openai.com/index/introducing-deep-research/) and [Gemini](https://blog.google/products/gemini/google-gemini-deep-research/) Deep Research.However, it allows you to customize the models, prompts, report structure, and search API used. Specifically, you can customize:

Key features:
- Optionally, provide an outline with a desired report structure
- Optionally, customize the planner model (e.g., DeepSeek, OpenAI reasoning model, etc)
- Provide feedback on the plan of report sections and iterate until user approval 
- Optionally, choose different search APIs (e.g., Tavily, Perplexity) and set the # of searches to perform during research on each section
- Optionally, set the number of section writing, reflection, search, re-write to perform during report generation
- Optionally, customize the writer model (e.g., Anthropic)

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

Edit the `.env` file with your API keys:

```bash
export TAVILY_API_KEY=<your_tavily_api_key>
export ANTHROPIC_API_KEY=<your_anthropic_api_key>
export OPENAI_API_KEY=<your_openai_api_key>
export GROQ_API_KEY=<your_groq_api_key>
export PERPLEXITY_API_KEY=<your_perplexity_api_key>
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

Optionally, provide a description of the report structure you want as a configuration. You can further tune this during the feedback phase. While a topic alone can generate reports, we found that providing a structure significantly improves quality. For example, business strategy reports might need case studies, while comparative analyses benefit from structured comparison tables. The natural language structure acts as a flexible template, guiding the AI to create more focused and relevant reports.

> See [some example report types here](report_examples/)!

## Motivation 

This mirrors the flow of [OpenAI](https://openai.com/index/introducing-deep-research/) and [Gemini](https://blog.google/products/gemini/google-gemini-deep-research/) Deep Research, but allow you to customize the models, prompts, and research report structure.

## How it works
   
1. `Plan and Execute` - Open Deep Research follows a [plan-and-execute workflow](https://github.com/assafelovic/gpt-researcher) that separates planning from research, allowing for better resource management, human-in-the-loop approval, and significantly reducing overall report creation time:

   - **Planning Phase**: An LLM analyzes the user's `topic` and `structure` using a planning prompt to create the report sections first. 
   - **Research Phase**: The system parallelizes web research across all sections requiring external data:
     - Uses [Tavily API](https://tavily.com/) or [Perplexity](https://www.perplexity.ai/hub/blog/introducing-the-sonar-pro-api) for targeted web searches
     - Processes multiple sections simultaneously for faster report generation
     - Synthesizes gathered information into coherent section content
   
2. `Sequential Writing` - The report generation follows a logical sequence:
   - First, completes all research-dependent sections in parallel
   - Then generates connecting sections like introductions and conclusions
   - Uses insights from research sections to create cohesive narratives
   - Maintains contextual awareness across all sections
   
   While this sequence can be customized via the `structure`, the default flow ensures that conclusions meaningfully incorporate research findings.

3. `Managing different types` - Open Deep Research is built on LangGraph, which has native support for configuration management [using assistants](https://langchain-ai.github.io/langgraph/concepts/assistants/). The report `structure` is a field in the graph configuration, which allows users to create different assistants for different types of reports. 

## UX

### Local deployment

Follow the [quickstart](#quickstart) to run the assistant locally.

### Hosted deployment
 
You can easily deploy to [LangGraph Platform ](https://langchain-ai.github.io/langgraph/concepts/#deployment-options). 
