# cltl-llm-app
A conversational Agent that uses a generative Large Language Module within the Leolani event-bus architecture.
It contains the basic modules for launching an event-bus on which user messages are posted to an LLM service and
the responses from the LLM are given back. The agent come with a basic chat interface that runs in a browser.

## Installation of the Leolani application

Clone this repository to your local machine.
Make sure you have Python 3.10 installed and active and create a virtual environment from the command line:

- (base)> pyenv local 3.10
- (base)> python -m venv venv
- (base)> source venv/bin/activate
- (venv) (base)> python -m pip install --upgrade pip

With the ```venv``` active now install the required packages from the commandline:

```(venv) (base)> pip install -r requirements.txt```

## Installation of the LLM server
After installing the requirements, you need to install the LLM locally.
There are two options for running an LLM as s server locally:

1. Using the llama.cpp server: https://github.com/ggml-org/llama.cpp
2. Using the Ollama package: https://ollama.com

For installing ```llama.cpp``` or ```Ollama``` please follow the instructions on the Githubs.
The documentation also explains how to install LLMs locally. In the case of Ollama, you can install a model from the command line as follows:

```(base)> ollama pull llama3.2```

## How to run the conversational Agent event-bus

The main application of the Leolani event bus is in the folder ```py-app``` which contains:

- ```config``` folder that contains the ```default.config``` file with the runtime settings
- ```storage``` folder for storing the conversations in EMISSOR format
- ```app.py``` main script for running the application

To run the application, call the ```app.py``` script from within the active ```venv```:

```(venv) (base)> python3 app.py```

This launches the Leolani event bus and a webclient to start a chat. 
The main script will loads the ```default.config``` file with the run-time settings.
Most of these settings are standard for the Leolani event-bus. For adatping the behaviour of the LLM agent,
you can change the settings in [cltl.llm]:

```
[cltl.llm]
model:llama3.2
#server
#port:9001
instruction: "You are a medical robot. You will have an extensive conversation with an elderly person. 
You first ask for his or her name and you address the person with his or her name. Answer in short sentences with no more than 15 wprds."
intro: "Hi, I am Leolani and I want to help you. I listen to what you tell me and give medical advice. Tell be about yourself. Who are you?"
stop: "It was great talking to you. See you soon!"
temperature:0.9
max_history: 15
topic_input: cltl.topic.text_in
topic_output: cltl.topic.text_out
topic_scenario : cltl.topic.scenario
```
The ```model``` setting is required for the Ollama server, which should match the name of any LLM you pulled through Ollama.
If you use the the ```llama.cpp``` server instead, you should uncomment the ```server``` and ```port``` options. In that case,
the model that is launched in the ```llama.cpp``` server is being called.

You can further adapt the ```instruction``` prompt and also the ```intro``` that starts the conversation and the ```stop``` that terminates the conversation.
The ```temperature``` is a value between ```0``` and ```1.0```. Closer to ```0``` makes the response closer to the instruction and closer to ```1.0```
makes the response more creative. The ```max_history``` limits the conversational context that is included in the prompt. Turns upto this maximum are given as preceeeding context.

## How to access the chat user interface:

If there are no error messages in the command line window that runs the event-bus agent, you can open the chat interface in a browser through the following URL:

http://localhost:8000/chatui/static/chat.html

You will see a chat window with a welcoming message:

![](/Users/piek/Desktop/d-Leolani/cltl-llm-app/doc/chatui.png)

You can now start chatting with the selected LLM through the event bus.
