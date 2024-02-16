import json
import requests
from os import makedirs
from os.path import join, exists
from datetime import date, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from bs4 import BeautifulSoup
from xhtml2pdf import pisa
import os
import re
import html

ARTICLES_DIR = join('tempdata', 'articles')
PDF_DIR = join('tempdata', 'pdfs')
makedirs(ARTICLES_DIR, exist_ok=True)
makedirs(PDF_DIR, exist_ok=True)

# Add your keywords between "", 
keywords = [
    "key", "words"
]
keywords_query = ' OR '.join(f'"{kw}"' for kw in keywords)

# Endpoint da API e parâmetros
API_ENDPOINT = 'http://content.guardianapis.com/search'
my_params = {
    'q': keywords_query,
    'from-date': "",
    'to-date': "",
    'order-by': "newest",
    'show-fields': 'all',
    'show-references': 'author',
    'show-tags': 'all',
    'page-size': 200,
    'api-key': 'addhere'  # Add your API key
}

########################## Date range for article search #################
start_date = date(2024, 2, 2)
end_date = date(2024, 2, 7)
########################## Date range for article search #################
dayrange = range((end_date - start_date).days + 1)

def article_matches(article, keywords):
    text = f"{article.get('fields', {}).get('headline', '')} {article.get('fields', {}).get('body', '')}".lower()
    return any(keyword.lower() in text for keyword in keywords)

def strip_html_tags(text):
    """Remove HTML tags and entities from a string."""
    text = re.sub('<.*?>', '', text)
    return html.unescape(text)

def remove_emojis(text):
    """Remove emojis and other non-ASCII characters from the text."""
    emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def clean_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def convert_html_to_pdf(source_html, output_filename):
    with open(output_filename, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(source_html, dest=result_file)
    if pisa_status.err:
        print(f"Erro ao gerar o PDF: {output_filename}")
        return False
    else:
        print(f"PDF gerado com sucesso: {output_filename}")
        return True

def get_author_name(article):
    default_author = "Unknown Author"
    if "tags" in article and len(article["tags"]) > 0:
        for tag in article["tags"]:
            if tag["type"] == "contributor":
                return tag["webTitle"]
    return default_author


class PDFReportLab:
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(filename, pagesize=letter)
        self.styles = getSampleStyleSheet()
        self.story = []

    def sanitize_text(self, text):
        replacements = {
            '–': '-', '—': '--', '“': '"', '”': '"', '‘': "'", '’': "'", '•': '*', '…': '...',
        }
        for problematic_char, replacement in replacements.items():
            text = text.replace(problematic_char, replacement)
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        return text

    def add_article(self, article):
        title = self.sanitize_text(article['fields']['headline'])
        trail_text = self.sanitize_text(article['fields'].get('trailText', 'No summary available'))
        author_name = get_author_name(article)
        body_html = article['fields'].get('body', '')
        published_date = article['webPublicationDate']
        url = article['webUrl']
        thumbnail_url = article['fields'].get('thumbnail', '')  
        title_word_count = len(title.split())
        lead_word_count = len(trail_text.split())
        soup = BeautifulSoup(body_html, 'html.parser')
        body_text = soup.get_text(separator='\n')
        body_word_count = len(body_text.split())
        self.story.append(Paragraph(f"Title: {title} (Words: {title_word_count})", self.styles['Heading2']))
        if thumbnail_url:  
            self.story.append(Image(thumbnail_url, width=400, height=200))  
        self.story.append(Paragraph(f"Lead: {trail_text} (Words: {lead_word_count})", self.styles['Italic']))
        self.story.append(Paragraph(f"Author: {author_name}", self.styles['Italic']))
        self.story.append(Paragraph(f"Published: {published_date}", self.styles['Italic']))
        self.story.append(Paragraph(f"URL: {url}", self.styles['Italic']))
        self.story.append(Spacer(1, 12))
        self.story.append(Paragraph(f"Body (Words: {body_word_count})", self.styles['Normal']))
        self.story.append(Paragraph(body_text, self.styles['Normal']))
        self.story.append(Spacer(1, 12))

    def build(self):
        self.doc.build(self.story)

pdf_filename = join(PDF_DIR, f"{date.today().strftime('%Y-%m-%d')}_articles.pdf")
pdf = PDFReportLab(pdf_filename)

for daycount in dayrange:
    dt = start_date + timedelta(days=daycount)
    datestr = dt.strftime('%Y-%m-%d')
    print(f"Search for articles on date: {datestr}") 
    my_params['from-date'] = datestr
    my_params['to-date'] = datestr
    my_params['show-tags'] = 'keyword'  
    response = requests.get(API_ENDPOINT, my_params)
    data = response.json()
    print(f"Get {len(data['response']['results'])} total of article: {datestr}") 
    articles_filtered = [article for article in data['response']['results'] if article_matches(article, keywords)]
    for article in articles_filtered:
        title = article['fields']['headline']
        print(f"Creating the article '{title}' in PDF.")  
        body_html = article['fields'].get('body', '')
        soup = BeautifulSoup(body_html, 'html.parser')
        body_text = soup.get_text()
        published_date = article['webPublicationDate']
        url = article['webUrl']
        author_name = get_author_name(article)
        thumbnail_url = article['fields'].get('thumbnail', '')
        trail_text = article['fields'].get('trailText', 'No summary available')
        word_count = len(body_text.split())
        title_word_count = len(title.split())
        trail_text_word_count = len(trail_text.split())
        total_word_count = title_word_count + trail_text_word_count + word_count
        publication = article['fields'].get('publication', 'theguardian.com')  
        keywords1 = ', '.join([tag['webTitle'] for tag in article.get('tags', []) if tag['type'] == 'keyword'])
        body_html_with_title_and_url = f"""
        <h1>{title}</h1>
        <p>Author: {author_name}</p>
        <p>Lead: {trail_text}</p>
        <p>Published: {published_date}</p>
        <p>URL: <a href='{url}'>{url}</a></p>
        <p>Publication: {publication}</p>
        <p>Word Count total: {total_word_count}</p>
        """ 
        if keywords1:  
            body_html_with_title_and_url += f"<p>Keywords: {keywords1}</p>"
        if thumbnail_url: 
            body_html_with_title_and_url += f"<img src='{thumbnail_url}' alt='Article Thumbnail' style='width:100%;max-width:600px;'><br/>"
        body_html_with_title_and_url += body_html
        article_title = clean_filename(title)
        output_filename = f"{PDF_DIR}/{datestr}_{article_title}.pdf"
        success = convert_html_to_pdf(body_html_with_title_and_url, output_filename)
        if not success:
            print(f"Fail in creating the article: {title}")