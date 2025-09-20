import feedparser
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import requests
import time
from dateutil import parser
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # For NewsAPI integration
CRYPTOPANIC_API_KEY = os.getenv('CRYPTOPANIC_API_KEY')  # For CryptoPanic

# Enhanced RSS feeds from multiple sources
RSS_FEEDS = {
    'CoinTelegraph': 'https://cointelegraph.com/rss',
    'CoinDesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'Decrypt': 'https://decrypt.co/feed',
    'CryptoSlate': 'https://cryptoslate.com/feed/',
    'BeInCrypto': 'https://beincrypto.com/feed/',
    'CryptoNews': 'https://cryptonews.com/news/feed/',
    'Blockworks': 'https://blockworks.co/rss.xml'
}

# News API sources (requires API key)
NEWS_API_SOURCES = [
    'crypto-coins-news',
    'coindesk',
    'the-verge'
]

def get_db_connection():
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def fetch_cryptopanic_news():
    """Fetch news from CryptoPanic API"""
    if not CRYPTOPANIC_API_KEY:
        print("⚠️  CryptoPanic API key not configured, skipping...")
        return []
    
    try:
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {
            'auth_token': CRYPTOPANIC_API_KEY,
            'kind': 'news',
            'filter': 'hot',
            'page': 1
        }
        
        print("📰 Fetching news from CryptoPanic API...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for post in data.get('results', []):
            articles.append({
                'title': post.get('title'),
                'link': post.get('url'),
                'published_date': parser.parse(post.get('published_at')),
                'source': 'CryptoPanic'
            })
        
        print(f"✅ Fetched {len(articles)} articles from CryptoPanic")
        return articles
        
    except Exception as e:
        print(f"❌ Error fetching CryptoPanic news: {e}")
        return []

def fetch_newsapi_crypto():
    """Fetch cryptocurrency news from NewsAPI"""
    if not NEWS_API_KEY:
        print("⚠️  NewsAPI key not configured, skipping...")
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'apiKey': NEWS_API_KEY,
            'q': 'cryptocurrency OR bitcoin OR ethereum OR crypto',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 50,
            'from': (datetime.now() - timedelta(days=1)).isoformat()
        }
        
        print("📱 Fetching news from NewsAPI...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for article in data.get('articles', []):
            if article.get('title') and article.get('url'):
                articles.append({
                    'title': article['title'],
                    'link': article['url'],
                    'published_date': parser.parse(article['publishedAt']),
                    'source': f"NewsAPI-{article.get('source', {}).get('name', 'Unknown')}"
                })
        
        print(f"✅ Fetched {len(articles)} articles from NewsAPI")
        return articles
        
    except Exception as e:
        print(f"❌ Error fetching NewsAPI articles: {e}")
        return []

def save_articles_to_db(articles, conn):
    """Save articles to database with enhanced error handling"""
    new_articles_count = 0
    
    try:
        for article in articles:
            try:
                cur = conn.cursor()
                
                insert_query = sql.SQL("""
                    INSERT INTO news_articles (title, link, published_date, source)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING;
                """)
                
                cur.execute(insert_query, (
                    article['title'], 
                    article['link'], 
                    article['published_date'], 
                    article['source']
                ))
                
                if cur.rowcount > 0:
                    new_articles_count += 1
                    print(f"[DEBUG] --> SUCCESS: Saved '{article['title'][:50]}...'")
                
                cur.close()
                
            except Exception as e:
                print(f"[DEBUG] --> FAILED to save article: {e}")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error saving articles to database: {e}")
        conn.rollback()
    
    return new_articles_count
def fetch_and_save_news():
    """Enhanced news fetching from multiple sources"""
    conn = get_db_connection()
    if conn is None: 
        return

    print("🚀 Starting Enhanced News Fetch Process...")
    print(f"🗞️ Processing {len(RSS_FEEDS)} RSS feeds + API sources")
    
    total_new_articles = 0
    all_articles = []
    
    # 1. Fetch from RSS Feeds
    print("\n📈 Phase 1: RSS Feeds")
    print("=" * 40)
    
    for source, url in RSS_FEEDS.items():
        print(f"Fetching news from {source} at {url}...")
        try:
            feed = feedparser.parse(url)
            
            print(f"[DEBUG] Found {len(feed.entries)} entries in {source} RSS feed.")

            if not feed.entries:
                if feed.bozo:
                    print(f"[DEBUG] Warning: {source} feed is malformed. Bozo Exception: {feed.bozo_exception}")
                continue

            source_articles = []
            for entry in feed.entries:
                try:
                    source_articles.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published_date': parser.parse(entry.published),
                        'source': source
                    })
                except Exception as e:
                    print(f"[DEBUG] --> FAILED to process RSS entry: {e}")
            
            # Save RSS articles
            new_count = save_articles_to_db(source_articles, conn)
            total_new_articles += new_count
            print(f"✅ {source}: {new_count} new articles saved")
            
        except Exception as e:
            print(f"❌ FAILED to fetch from {source}: {e}")
        
        # Rate limiting
        time.sleep(1)
    
    # 2. Fetch from CryptoPanic API
    print("\n💰 Phase 2: CryptoPanic API")
    print("=" * 40)
    
    cryptopanic_articles = fetch_cryptopanic_news()
    if cryptopanic_articles:
        new_count = save_articles_to_db(cryptopanic_articles, conn)
        total_new_articles += new_count
        print(f"✅ CryptoPanic: {new_count} new articles saved")
    
    time.sleep(2)  # Longer delay between different APIs
    
    # 3. Fetch from NewsAPI
    print("\n📱 Phase 3: NewsAPI")
    print("=" * 40)
    
    newsapi_articles = fetch_newsapi_crypto()
    if newsapi_articles:
        new_count = save_articles_to_db(newsapi_articles, conn)
        total_new_articles += new_count
        print(f"✅ NewsAPI: {new_count} new articles saved")
    
    # Final summary
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"🎉 Enhanced News Fetch Complete!")
    print(f"📊 Total new articles saved: {total_new_articles}")
    print(f"🕰️ Sources processed: {len(RSS_FEEDS)} RSS + 2 APIs")
    print(f"✅ Enhanced news aggregation successful!")

if __name__ == "__main__":
    fetch_and_save_news()