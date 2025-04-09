# DP - Prompt Optimization Platform

DP is a platform for prompt optimization, evaluation, and comparison of AI model outputs. The application consists of two main parts: a frontend and a backend. They communicate via a REST API, and data is stored in a MongoDB database.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation and Setup](#installation-and-setup)
  - [Frontend](#frontend)
  - [Backend](#backend)
- [Configuration](#configuration)
  - [config.yaml](#configyaml)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

DP provides the following functionalities:
- **Prompt Optimization:** Optimize queries using various techniques (e.g., Chain of Thought, Self-Consistency, ReAct, etc.).
- **Prompt Evaluation:** Evaluate prompts using either AI-based or human-defined criteria.
- **Prompt Comparison:** Compare original and optimized prompts, including generation of "blind" results.
- **User Management:** Registration, login, and fetching user details.

The frontend is built using React with PrimeReact and Vite, while the backend is implemented in Python using FastAPI. The backend also integrates with MongoDB for data storage.

## Requirements

Before installation, ensure you have the following installed:
- [Node.js](https://nodejs.org/) (v14+)
- [Python](https://www.python.org/) (3.8+)
- MongoDB (either locally or via cloud)
- Package managers: npm and pip

## Installation and Setup

### Frontend

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
2. Install the necessary packages:
   ```bash
   npm install
   npm install vite
3. Start the development server:
   ```bash
   npm run dev
The development server will run on port 5173 or 5174. Open the address shown in the terminal in your browser to access the application.

### BACKEND

1. Navigate to the project root and install Python dependencies:
   ```bash
   pip install -r requirements.txt
2. Start the FastAPI server using uvicorn:
   ```bash
   uvicorn backend.db.main:app
The server will listen on port 8000 for incoming requests. It processes prompt optimization and evaluation tasks and interacts with the MongoDB database.

### Configuration

The application uses a YAML configuration file (config.yaml) to store settings such as API keys and database connection details.

config.yaml
Below is an example of the config.yaml file content:
provider: "openai"

auth_secret_key: "VQ2MfKMyZH5yFRXwluE5WTRZhvP24BD1"

api_keys:
  openai: "your_openai_api_key_here"
  claude: "your_claude_api_key_here"

models:
  openai:
    gpt-3.5-turbo: "gpt-3.5-turbo"
    gpt-4o: "gpt-4o"
    gpt-4o-mini: "gpt-4o-mini"
    o3-mini: "o3-mini"
  claude:
    claude-3-haiku-20240307: "claude-3-haiku-20240307"
    claude-3-5-haiku-latest: "claude-3-5-haiku-latest"
    claude-3-7-sonnet-latest: "claude-3-7-sonnet-latest"

prompts:
  evaluator_human: "prompts/evaluator_human_prompt.txt"
  evaluator_llm: "prompts/evaluator_llm_prompt.txt"
  key_extraction: "prompts/extractor_key_elements.txt"
  CoT: "prompts/CoT_prompt.txt"
  SC: "prompts/SC_prompt.txt"
  CoD: "prompts/CoD_prompt.txt"
  PC: "prompts/PC_prompt.txt"
  ReAct: "prompts/ReAct_prompt.txt"
  SC_ReAct: "prompts/SC_React_prompt.txt"
  expert_finder: "prompts/expert_finder_prompt.txt"
  independent_agent: "prompts/independent_agent.txt"

database:
  uri: "mongodb+srv://{user}:{pass}@dp-database.fczwf.mongodb.net/?retryWrites=true&w=majority&appName=DP-Database"
  database_name: "dp_database"

Important: Before starting the project, replace your_openai_api_key_here and your_claude_api_key_here with valid API keys. Also, update the MongoDB connection parameters (replace {user} and {pass} with your actual credentials).

### API Endpoints

The backend exposes the following endpoints:

 - Users (/users): Registration, login, and retrieving user data.

 - Evaluations (/evaluations): Create prompt evaluations, comparisons, and generate blind results.

 - Optimized Prompts (/optimizations): Create and update optimized prompt records.

For detailed API documentation, please visit:
http://localhost:8000/docs
