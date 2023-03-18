[![Python 3.x](https://img.shields.io/badge/python-3.x-green.svg)](https://www.python.org/downloads/release/python-360/)

![logo](https://user-images.githubusercontent.com/10207709/225381809-51b4d378-fe26-4571-9135-d91957943d08.jpg)

# ChatGPT API with FastAPI
This repository contains a simple implementation of a ChatGPT API using FastAPI and OpenAI's GPT model. 
The API allows users to input a prompt and generate a response from the model.

Up to 10 messages are stored in Redis. 
The cache allows the conversation to continue with ChatGPT.

## Prerequisite
- Docker
- Redis

Before running the application, make sure that Docker and Redis are installed and running on your system.

important: Set and use all the environment variables in app/config/constants.py.

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

## Usage
![image](https://user-images.githubusercontent.com/10207709/225383322-2c7c24ad-8c4f-4864-be1e-a04ceae2c7fd.png)
You can save and continue conversations based on `user_id`. 
Just put in a value that identifies the user. 
For example, you can use the user's unique number, session information, etc. stored in the database.

- `user_id`: This is the parameter that identifies the user. Conversations will be stored and retrieved based on this parameter. In other words, the chat history with User A will be separate from the chat history with User B.
- `number_of_messages_to_keep`: This parameter specifies how many recent messages to keep in the chat history. It's generally better to keep more messages, but keep in mind that this can impact the cost of ChatGPT.
- `For the remaining parameters, please refer to the following link for more details: https://beta.openai.com/docs/api-reference/completions/create. This link provides the API reference for creating completions with ChatGPT.

## License
This project is licensed under the terms of the MIT license. See [LICENSE](license) for more information.
