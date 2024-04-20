[![Python 3.x](https://img.shields.io/badge/python-3.10-green.svg)](https://www.python.org/downloads/release/python-360/)

![image](https://github.com/jybaek/llm-with-slack/assets/10207709/d92980a9-7f30-470c-850a-2a530a32dc80)

> This is an image created with DALL-E 2. Use it for your Slatbot profile image.

# LLM API with FastAPI
This repository connects the LLM API to Slack. 
It currently supports implementations using OpenAI's ChatGPT and Google's Gemini model. 
The basic structure is straightforward. 
When a message arrives through Slack, we generate a response using the LLM's API.
It has multimodal capabilities, enabling us to process and analyze images.

All settings are set via environment variables.
See [here](./app/config/constants.py).


| envrionment                | description                                 | values        |
|----------------------------|---------------------------------------------|---------------|
| slack_token                | A Slack token that begins with `XOXB`       | required      |
| openai_token               | An OpenAI token that begins with `sk`       | required      |
| number_of_messages_to_keep | Set how many conversation histories to keep | 5             |
| system_content             | Enter the system content for ChatGPT        |               |
| model                      | GPT Model                                   | gpt-3.5-turbo |
| gemini_slack_token         | A Slack token that begins with `XOXB`       |               |


## Prerequisite
- Docker

Before running the application, make sure that Docker is installed and running on your system.

important: Set and use all the environment variables in [app/config/constants.py](app/config/constants.py).

## Local Execution Guide
1. First, to run this application in your local environment, please execute the following command to install the required libraries.
```bash
pip install -r requirements.txt
```

2. Once the necessary libraries have been installed, execute the following command to run the application.
```bash
uvicorn app.main:app --reload
```
This command will run the application based on the app object in the main module of the app package. 
You can use the `--reload` option to automatically reload the application when file changes are detected.

![image](https://github.com/jybaek/llm-with-slack/assets/10207709/fb235e7e-c99b-412d-8d54-765f74950794)

## Installation
1. Clone the repository:
```bash
https://github.com/jybaek/llm-with-slack.git
cd llm-with-slack
```

2. Build the Docker image:
```bash
docker build -t llm-api .
```

3. Run the Docker container:
```bash
docker run --rm -it -p8000:8000 llm-api
```

4. Open your web browser and go to `http://localhost:8000/docs` to access the Swagger UI and test the API.

## Sample
|Gemini|GPT|
|------|---|
|![Gemini](https://github.com/jybaek/llm-with-slack/assets/10207709/e4144e6a-82e9-493b-b951-754424751bab)|![GPT](https://github.com/jybaek/llm-with-slack/assets/10207709/4c4dbe4b-3221-4263-b0e2-ca02bc37f9fa)|

## API Documentation
The API documentation can be found at `http://localhost:8000/docs` once the Docker container is running.

## License
This project is licensed under the terms of the Apache license. See [LICENSE](license) for more information.
