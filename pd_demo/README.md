# Prisoner's Dilemma Demo

A simple web application demonstrating the Prisoner's Dilemma game using OpenAI's GPT models.

## Setup

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file

## Running the Application

```bash
python app.py
```

The application will be available at http://127.0.0.1:5000

## Environment Variables

The application uses the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required)

These should be set in your `.env` file. Do not commit this file to version control! 