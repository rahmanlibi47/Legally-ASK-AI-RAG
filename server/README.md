# Flask Server Setup Guide

This is a Flask-based server application that provides a RAG (Retrieval-Augmented Generation) system with document management and chat functionality.

## Prerequisites

- Python 3.x
- pip (Python package manager)

## Installation

1. Clone the repository and navigate to the server directory:

```bash
cd server
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Unix or MacOS
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Database Setup

1. Initialize the database:

```bash
flask db init
```

2. Create the initial migration:

```bash
flask db migrate -m "Initial migration"
```

3. Apply the migration to create the database tables:

```bash
flask db upgrade
```

This will create the following tables:
- `document`: Stores document information and embeddings
- `chat_history`: Stores chat interactions
- `document_chunk`: Stores document chunks for processing

## Running the Application

1. Start the Flask server:

```bash
python main.py
```

The server will start running on `http://localhost:5000` by default.

## API Endpoints

- `POST /api/scrape`: Scrape content from a URL and store it in the database

## Project Structure

- `app/`: Main application package
  - `__init__.py`: Application factory and configuration
  - `models.py`: Database models
  - `routes.py`: API endpoints
- `main.py`: Application entry point
- `requirements.txt`: Project dependencies
- `alembic.ini`: Database migration configuration

## Database Models

- `Document`: Stores document information including URL, content, and embeddings
- `ChatHistory`: Stores chat interactions linked to documents
- `DocumentChunk`: Stores document chunks with efficient processing