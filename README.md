[![Python 3.x](https://img.shields.io/badge/python-3.10-green.svg)](https://www.python.org/downloads/release/python-360/)

![logo](https://user-images.githubusercontent.com/10207709/225381809-51b4d378-fe26-4571-9135-d91957943d08.jpg)

# ChatGPT API with FastAPI
This repository contains implementations that use OpenAI's ChatGPT model. 
The basic structure is simple. When a message comes in via Slack, we generate a response via the ChatGPT API.

All settings are set via environment variables.
See [here](./app/config/constants.py).
- slack_token: A Slack token that begins with `XOXB`.
- openai_token: An OpenAI token that begins with `sk`.
- number_of_messages_to_keep: Set how many conversation histories to keep.

## Prerequisite
- Docker
- Redis

Before running the application, make sure that Docker and Redis are installed and running on your system.

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
You can use the --reload option to automatically reload the application when file changes are detected.

## Installation
1. Clone the repository:
```bash
https://github.com/jybaek/Hello-ChatGPT.git
cd Hello-ChatGPT
```

2. Build the Docker image:
```bash
docker build -t chatgpt-api .
```

3. Run the Docker container:
```bash
docker run --rm -it -p8000:8000 chatgpt-api
```

4. Open your web browser and go to `http://localhost:8000/docs` to access the Swagger UI and test the API.

## API Documentation
The API documentation can be found at `http://localhost:8000/docs` once the Docker container is running.

## License
This project is licensed under the terms of the MIT license. See [LICENSE](license) for more information.
