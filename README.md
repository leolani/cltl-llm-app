# cltl-llm-app
A conversational Agent that uses a generative Large Language Module within the Leolani event-bus architecture.
It contains the basic modules for launching an event-bus on which user messages are posted to an LLM service and
the responses from the LLM are given back. The agent come with a basic chat interface that runs in a browser.

# Installation

Clone this repository to your local machine.
Make sure you have Python 3.10 installed and active and create a virtual environment from the command line:

- (base)> pyenv local 3.10
- (base)> python -m venv venv
- (base)> source venv/bin/activate
- (venv) (base)> python -m pip install --upgrade pip

With the ```venv``` active now install the required packages from the commandline:

```(venv) (base)> pip install -r requirements.txt```

After installing the requirements, you need to install the LLM locally.
There are two options for running an LLM as s server locally:

1. Using the llama.cpp server: https://github.com/ggml-org/llama.cpp
2. Using the Ollama package: https://ollama.com

For installing ```llama.cpp``` or ```Ollama``` please follow the instructions on the Githubs.
The documentation also explains how to install LLMs locally.

# How to run the conversational Agent

The main application of the Leolani event bus is in the folder ```py-app``` which contains:

- ```config``` folder that contains the ```default.config``` file with the runtime settings
- ```storage``` folder for storing the conversations in EMISSOR format
- ```app.py``` main script for running the application

To run the application, call the ```app.py``` script from within the active ```venv```:

```(venv) (base)> python3 app.py```

This launches the Leolani event bus and a webclient to start a chat. 
The main script will loads the ```default.config``` file with the run-time settings. 

In a browser open the webclient through the following URL:

http://localhost:8000/chatui/static/chat.html

You will see a chat window with a welcoming message:

![](/Users/piek/Desktop/d-Leolani/cltl-llm-app/doc/chatui.png)

You can now start chatting with the selected LLM through the event bus.
