# Scott's Lead Qualification 
- Render.com Deploy

## Project Overview

This project is a Lead Qualification System designed to automatically evaluate and score potential sales leads based on various data points. It combines information from multiple sources, including social media profiles and professional networks, to provide a comprehensive assessment of each lead.

The system can be used by sales and marketing teams to:
- Prioritize high-value leads
- Automate the initial qualification process
- Gain insights into leads' professional and social profiles
- Generate qualification summaries for each lead

## Core Technologies

1. **Python**: The main backend logic is implemented in Python, utilizing FastAPI for the API server.
2. **PHP**: A client script is provided in PHP to interact with the Python backend.
3. **FastAPI**: Used to create the RESTful API endpoints.
4. **Guzzle**: PHP HTTP client used in the client script to make requests to the API.
5. **Various APIs and Libraries**:
   - LinkedIn API
   - Instagram API (via instaloader)
   - Facebook Scraper
   - Twitter API (via tweepy)

## Core Components

1. **Lead Qualification Machine** (`LeadQualificationMachine` class in `main.py`):
   - Handles the core logic for scraping data from various sources
   - Calculates lead scores
   - Generates qualification summaries

2. **FastAPI Application** (in `main.py`):
   - Provides the `/qualify` endpoint for lead qualification

3. **PHP Client** (`lead_qualify.php`):
   - Demonstrates how to interact with the API from a PHP environment

4. **Data Models** (Pydantic models in `main.py`):
   - `LeadInput`: Defines the structure of input lead data
   - `QualifiedLead`: Defines the structure of the qualified lead output

## How to Build and Run

### Backend (Python)

1. Ensure Python 3.7+ is installed.
2. Install required packages:
   ```
   pip install fastapi uvicorn python-dotenv linkedin-api instaloader facebook-scraper tweepy
   ```
3. Set up environment variables in a `.env` file with necessary API keys and credentials.
4. Run the FastAPI server:
   ```
   python main.py
   ```

### PHP Client

1. Ensure PHP 7.4+ is installed with Composer.
2. Install Guzzle:
   ```
   composer require guzzlehttp/guzzle
   ```
3. Update the `$apiUrl` in `lead_qualify.php` to point to your running FastAPI server.
4. Run the PHP script:
   ```
   php lead_qualify.php
   ```

## Usage

1. The Python backend exposes a `/qualify` endpoint that accepts a list of lead data.
2. Send a POST request to this endpoint with lead information.
3. The system will process each lead, scraping available data from social profiles.
4. A qualification score and summary will be generated for each lead.
5. The response will include detailed information about each qualified lead.

Note: Ensure all necessary API keys and credentials are properly set up in the `.env` file for full functionality.
