# ChatGPT API with FastAPI
This repository contains a simple implementation of a ChatGPT API using FastAPI and OpenAI's GPT model. 
The API allows users to input a prompt and generate a response from the model.

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
