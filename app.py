from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging
import re

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(filename='scraper.log', level=logging.DEBUG)

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    data = request.json
    company_name = data['company_name']
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
    news_types = data['news_types']
    num_articles = int(data['num_articles'])
    custom_instructions = data['custom_instructions']

    articles = []
    if news_types:
        for news_type in news_types:
            articles.extend(scrape_news(company_name, news_type,
                            start_date, end_date, num_articles))
    else:
        articles.extend(scrape_news(company_name, None,
                        start_date, end_date, num_articles))

    # Add debug print statements
    print(f"Number of articles scraped: {len(articles)}")
    print(f"Articles: {articles}")

    summary = summarize_articles(articles, custom_instructions, company_name)

    if not articles:
        return jsonify({'summary': "No articles found for the given criteria."})

    summary = summarize_articles(articles, custom_instructions, company_name)

    return jsonify({'summary': summary})


def scrape_news(company_name, news_type, start_date, end_date, num_articles):
    if news_type:
        url = f"https://www.google.com/search?q={
            company_name}+{news_type}&tbm=nws"
    else:
        url = f"https://www.google.com/search?q={company_name}&tbm=nws"

    print(f"Scraping URL: {url}")  # Debug print
    logging.info(f"Scraping URL: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    print(f"Response status code: {response.status_code}")  # Debug print
    logging.info(f"Response status code: {response.status_code}")

    # Log the HTML content
    logging.debug("HTML Content:")
    logging.debug(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')

    articles = []
    for item in soup.select('.SoaBEf'):
        link = item.select_one('.WlydOe')
        if link and 'href' in link.attrs:
            href = link['href']
            if href.startswith('/url?q='):
                link = href.split('/url?q=')[1].split('&sa=')[0]
            else:
                link = href

            print(f"Found link: {link}")  # Debug print
            logging.info(f"Found link: {link}")

            article_date = scrape_article_date(link)
            print(f"Article date: {article_date}")  # Debug print
            logging.info(f"Article date: {article_date}")

            if article_date and start_date <= article_date <= end_date:
                articles.append({
                    'url': link,
                    'date': article_date
                })
                print(f"Article added. Total articles: {
                      len(articles)}")  # Debug print
                logging.info(f"Article added. Total articles: {len(articles)}")

            if len(articles) >= num_articles:
                break

    print(f"Total articles scraped: {len(articles)}")  # Debug print
    logging.info(f"Total articles scraped: {len(articles)}")
    return articles


def scrape_article_date(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try multiple date meta tags
        for meta_name in ['article:published_time', 'pubdate', 'date', 'og:pubdate', 'og:publish_date']:
            date_tag = soup.find('meta', {'property': meta_name}) or soup.find(
                'meta', {'name': meta_name})
            if date_tag:
                date_str = date_tag['content']
                # Try parsing with different formats
                for date_format in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        parsed_date = datetime.strptime(
                            date_str[:10], date_format)
                        if parsed_date.year > datetime.now().year:
                            return None  # Ignore future dates
                        return parsed_date
                    except ValueError:
                        continue

        # If no meta tag found, look for a date in the text
        text = soup.get_text()
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
            r'\d{2}\.\d{2}\.\d{4}'     # DD.MM.YYYY
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                try:
                    parsed_date = datetime.strptime(
                        date_match.group(), '%d/%m/%Y')
                    if parsed_date.year > datetime.now().year:
                        return None  # Ignore future dates
                    return parsed_date
                except ValueError:
                    continue

        # If still no date found, return None
        return None

    except Exception as e:
        print(f"Error scraping date for {url}: {str(e)}")  # Debug print
        return None


def summarize_articles(articles, custom_instructions, company_name):
    print(f"Number of articles received: {len(articles)}")
    print(f"Articles received: {articles}")

    article_texts = []
    for article in articles:
        try:
            response = requests.get(article['url'], timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the main content (this is a simple approach and might need adjustment)
            main_content = soup.find('main') or soup.find(
                'article') or soup.find('body')
            if main_content:
                # Remove script and style elements
                for script in main_content(["script", "style"]):
                    script.decompose()
                text = main_content.get_text()
            else:
                text = soup.get_text()

            # Clean the text
            text = re.sub(r'\s+', ' ', text).strip()  # Remove extra whitespace
            text = text[:1000]  # Limit to first 1000 characters

            article_texts.append(f"Article from {article['url']} (Date: {
                                 article['date']}):\n{text}\n\n")
        except Exception as e:
            print(f"Error fetching article {article['url']}: {str(e)}")

    if not article_texts:
        return "No article content could be retrieved. Please try different search criteria."

    combined_text = "\n\n".join(article_texts)
    print(f"Combined text length: {len(combined_text)}")

    # Split the combined text into chunks if it's still too large
    max_chunk_size = 15000  # Adjust this value as needed
    chunks = [combined_text[i:i+max_chunk_size]
              for i in range(0, len(combined_text), max_chunk_size)]

    summaries = []
    for i, chunk in enumerate(chunks):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a news anchor summarizing recent events in a single paragraph."},
                    {"role": "user", "content": f"""
{custom_instructions}

Please summarize the following articles in a single paragraph, as if you were a news anchor announcing these events. Follow these guidelines:
1. Present the news in chronological order.
2. Highlight the main headline of each piece of news in bold and include the date it happened.
3. Use transitions to connect the different news items smoothly.
4. Maintain a professional and objective tone throughout the summary.
5. Focus only on news about {company_name}.

Here's an example of the format:
"OpenAI's CTO Mira Murati announced in May 2024 that she is **leaving the company**, to focus on other projects. She did not specify what exactly her next move is. The company also announced in June 2024 that it will be releasing a **new model called o1**. This new model promises to process information in a different way, to give better answers."

Here are the articles (part {i+1} of {len(chunks)}):\n{chunk}
                    """}
                ],
                max_tokens=500  # Limit the response size
            )
            summaries.append(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in OpenAI API call for chunk {i+1}: {str(e)}")
            summaries.append(f"Error summarizing chunk {i+1}")

    final_summary = " ".join(summaries)  # Join with spaces instead of newlines
    return final_summary


if __name__ == '__main__':
    app.run(debug=True)
