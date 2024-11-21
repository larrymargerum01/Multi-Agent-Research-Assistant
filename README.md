# Report mAIstro

Report mAIstro simple agent for report generation based upon two user inputs: 

* `Topic`: research topic
* `Structure`: report outline (can be natural language or a schema)

The agent solves a few problems: 

* `Section structure`: Users can describe what they want at varying levels of detail. On one extreme, a user may just describe the structure of the report in natural language. On the other extreme, the user may provide a JSON schema for the report structure. To handle these, report mAIstro will produce a plan for the report derived from the user's specified structure with, with the report divided into `Section` objects.
* `Research vs distillation`: Some sections of a report require research (e.g., external sources such as web search) whereas other sections (e.g., the introduction or conclusion) are simply distillations of the report body. Report mAIstro will handle this seamlessly, reflecting on which sections require research at the start of the research process and tackling those first.
* `Parallelization`: Research can be parallelized for an improved UX (lower latency). We use map-reduce to parallelize writing of every section that requires research first, and then write any remaining sections of the report in parallel. 

## Environment

Install dependencies:
```
$ python3 -m venv report_maistro
$ source report_maistro/bin/activate
$ pip install -r requirements.txt
```

Supply your OpenAI API key:
```
$ cp .env.example .env
```

## Testing in notebook

```
$ cd ntbk
$ jupyter notebook report_maistro.ipynb
```

## Deploying to LangGraph Platform 

TO ADD