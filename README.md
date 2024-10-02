# 📰 News Flash

News Flash is a web application that scrapes and summarizes news articles about a specified company within a given date range. It uses Flask for the backend, BeautifulSoup for web scraping, and OpenAI's GPT model for summarizing the articles.

## Features

- Search for news articles about a specific company
- Filter articles by date range
- Select specific news types (e.g., mergers, investments, projects)
- Customize the summary with additional instructions
- Responsive web interface built with Tailwind CSS

## Prerequisites

- Python 3.7+
- OpenAI API key

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/jpfaraco/newsflash.git
   cd newsflash
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Start the Flask development server:

   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Enter a company name, select a date range, and optionally choose specific news types or add custom instructions

4. Click "Summarize news" to generate a summary of recent news articles about the company

## Configuration

You can modify the following parameters in `app.py`:

- `num_articles`: The number of articles to scrape (default is 5)
- `max_chunk_size`: The maximum size of text chunks sent to the OpenAI API (default is 15000)

## Disclaimer

This application is for educational purposes only. Be sure to comply with the terms of service of the websites you're scraping and the OpenAI API usage guidelines.
