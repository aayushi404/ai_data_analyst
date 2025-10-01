# Ai Data Analyst
Being a data analyst is not that much easy So I tried to build a mini kind or Ai data analyst.This is the backend api of the project.
You can send it any kind of question plus data you want to use and it will analyse the data or perform descrptive statistics if needed and give you your perfect answer.
## Features
- Data Analysis: Perform various data analysis tasks such as descriptive statistics, data visualization, and trend identification.
- Natural Language Processing: Understand and respond to user queries in natural language.
- Customizable: Allow users to customize the analysis based on their specific needs and requirements.
- It will turn out to be your best data analyst buddy who can also scrape data from the web if needed.

For now i will make a prototype of it and test it with some sample data and questions.
## First Stage
### To-Do
question.tsx -> send to api -> convert to json -> breakdown into small tasks -> Generate code for tasks -> Execute code -> Get results -> Send results to LLM with question -> Get final answer -> send to frontend

The core logic that i will use to implement it is this:
```python
def loop(llm):
    msg = [user_input()]  # App begins by taking user input
    while True:
        output, tool_calls = llm(msg, tools)  # ... and sends the conversation + tools to the LLM
        print("Agent: ", output)  # Always stream LLM output, if any
        if tool_calls:  # Continue executing tool calls until LLM decides it needs no more
            msg += [ handle_tool_call(tc) for tc in tool_calls ]  # Allow multiple tool calls (may be parallel)
        else:
            msg.append(user_input())  # Add the user input message and continue
```
