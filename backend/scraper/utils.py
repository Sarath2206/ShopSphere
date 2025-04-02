from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import requests
import re
import time
import logging
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Increase timeout values
DEFAULT_TIMEOUT = 30  # seconds
PAGE_LOAD_TIMEOUT = 40  # seconds
SCROLL_WAIT_TIME = 5  # seconds
MAX_RETRIES = 3  # Number of retries for failed scraping attempts
MAX_CONCURRENT_SCRAPERS = 5  # Maximum number of concurrent scrapers

def setup_driver():
    """Set up and return a configured Selenium WebDriver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Rotate user agents to avoid detection
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver

def normalize_price(price_str):
    """Extract and normalize price from string."""
    if not price_str or price_str == 'N/A':
        return None
    
    # Extract digits and decimal point
    # Handle currency symbols like ₹, $, €, etc.
    price_match = re.search(r'[\d,]+\.?\d*', price_str)
    if price_match:
        # Remove commas and convert to float
        price = float(price_match.group().replace(',', ''))
        return price
    return None

def normalize_material(material_str):
    """Normalize material descriptions."""
    if not material_str or material_str == 'N/A':
        return 'N/A'
    
    material_str = material_str.lower()
    
    # Map common variations to standard terms
    material_mapping = {
        'cotton blend': 'Cotton Blend',
        'cotton mix': 'Cotton Blend',
        'cotton': 'Cotton',
        'polyester': 'Polyester',
        'wool': 'Wool',
        'silk': 'Silk',
        'linen': 'Linen',
        'rayon': 'Rayon',
        'nylon': 'Nylon',
        'denim': 'Denim',
        'spandex': 'Spandex',
        'elastane': 'Spandex',
        'viscose': 'Viscose',
        'modal': 'Modal',
        'lycra': 'Spandex'
    }
    
    for key, value in material_mapping.items():
        if key in material_str:
            return value
    
    return material_str.capitalize()

def scrape_with_retry(scrape_func, query, max_retries=MAX_RETRIES):
    """Execute a scraping function with retries."""
    for attempt in range(max_retries):
        try:
            return scrape_func(query)
        except TimeoutException:
            logger.warning(f"Timeout on attempt {attempt + 1} for {scrape_func.__name__}")
            if attempt == max_retries - 1:
                logger.error(f"Max retries reached for {scrape_func.__name__}")
                return []
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Error in {scrape_func.__name__}: {str(e)}")
            return []
    return []

def scrape_all_sites(query):
    """Scrape all supported e-commerce sites concurrently."""
    scraping_functions = [
        scrape_meesho,
        scrape_nykaa_fashion,
        scrape_fabindia,
        scrape_myntra,
        scrape_ajio,
        scrape_flipkart,
        scrape_amazon,
        scrape_tatacliq
    ]
    
    all_products = []
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SCRAPERS) as executor:
        # Create futures for each scraping function
        future_to_site = {
            executor.submit(scrape_with_retry, func, query): func.__name__
            for func in scraping_functions
        }
        
        # Process completed futures as they finish
        for future in as_completed(future_to_site):
            site_name = future_to_site[future]
            try:
                products = future.result()
                all_products.extend(products)
                logger.info(f"Completed scraping {site_name} - found {len(products)} products")
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {str(e)}")
    
    return all_products

def scrape_meesho(query):
    """Scrape product data from Meesho."""
    logger.info(f"Scraping Meesho for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.meesho.com/search?q={query}"
        driver.get(search_url)
        
        # Wait for product cards to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductList__GridCol-sc-8lnc8o-0"))
        )
        
        # Scroll down to load more products
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all product cards
        product_cards = soup.find_all('div', class_=lambda c: c and 'ProductList__GridCol' in c)
        
        for item in product_cards[:10]:  # Limit to first 10 products for performance
            try:
                name_elem = item.find('p', class_=lambda c: c and 'Text__StyledText' in c)
                price_elem = item.find('h5', class_=lambda c: c and 'Text__StyledText' in c)
                image_elem = item.find('img')
                rating_elem = item.find('span', class_=lambda c: c and 'Rating__StyledRating' in c)
                
                name = name_elem.text if name_elem else 'N/A'
                price = price_elem.text if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                rating = rating_elem.text if rating_elem else 'N/A'
                
                # Material is often not directly available on search results
                material = 'N/A'
                
                normalized_price = normalize_price(price)
                
                products.append({
                    'name': name,
                    'price': normalized_price,
                    'price_display': price,
                    'image': image,
                    'material': material,
                    'rating': rating,
                    'site': 'Meesho'
                })
            except Exception as e:
                logger.error(f"Error parsing Meesho product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Meesho: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_nykaa_fashion(query):
    """Scrape product data from Nykaa Fashion."""
    logger.info(f"Scraping Nykaa Fashion for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.nykaafashion.com/search?q={query}"
        driver.get(search_url)
        
        # Wait for product cards to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card"))
            )
            
            # Scroll down to load more products
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all product cards
            product_cards = soup.find_all('div', class_='product-card')
            
            for item in product_cards[:10]:  # Limit to first 10 products
                try:
                    name_elem = item.find('div', class_='product-name')
                    brand_elem = item.find('div', class_='brand-name')
                    price_elem = item.find('span', class_='primary-price')
                    image_elem = item.find('img')
                    
                    brand = brand_elem.text.strip() if brand_elem else ''
                    name = name_elem.text.strip() if name_elem else 'N/A'
                    if brand and name != 'N/A':
                        name = f"{brand} - {name}"
                        
                    price = price_elem.text.strip() if price_elem else 'N/A'
                    image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                    
                    # Material and rating often not available in search results
                    material = 'N/A'
                    rating = 'N/A'
                    
                    normalized_price = normalize_price(price)
                    
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': material,
                        'rating': rating,
                        'site': 'Nykaa Fashion'
                    })
                except Exception as e:
                    logger.error(f"Error parsing Nykaa Fashion product: {e}")
                    continue
        except TimeoutException:
            logger.warning("Timeout waiting for Nykaa Fashion products to load")
            
    except Exception as e:
        logger.error(f"Error scraping Nykaa Fashion: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_fabindia(query):
    """Scrape product data from FabIndia."""
    logger.info(f"Scraping FabIndia for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.fabindia.com/search?q={query}"
        driver.get(search_url)
        
        # Wait for product cards to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item"))
            )
            
            # Scroll down to load more products
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all product cards
            product_cards = soup.find_all('div', class_='product-item')
            
            for item in product_cards[:10]:  # Limit to first 10 products
                try:
                    name_elem = item.find('div', class_='product-name')
                    price_elem = item.find('span', class_='price')
                    image_elem = item.find('img', class_='product-image')
                    
                    name = name_elem.text.strip() if name_elem else 'N/A'
                    price = price_elem.text.strip() if price_elem else 'N/A'
                    image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                    
                    # FabIndia often uses natural materials
                    material = 'Cotton' if 'cotton' in name.lower() else 'N/A'
                    rating = 'N/A'
                    
                    normalized_price = normalize_price(price)
                    
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': material,
                        'rating': rating,
                        'site': 'FabIndia'
                    })
                except Exception as e:
                    logger.error(f"Error parsing FabIndia product: {e}")
                    continue
        except TimeoutException:
            logger.warning("Timeout waiting for FabIndia products to load")
            
    except Exception as e:
        logger.error(f"Error scraping FabIndia: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_google_shopping(query):
    """Scrape product data from Google Shopping."""
    logger.info(f"Scraping Google Shopping for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        # Use the complete query text for search
        search_url = f"https://www.google.com/search?q={query}&tbm=shop"
        driver.get(search_url)
        
        # Wait for product cards to load
        try:
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.sh-dgr__grid-result"))
            )
            
            # Scroll down to load more products
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(SCROLL_WAIT_TIME)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all product cards
            product_cards = soup.find_all('div', class_='sh-dgr__grid-result')
            
            for item in product_cards[:15]:  # Get more products from Google
                try:
                    # Extract product details
                    name_elem = item.find('h3', class_='tAxDx')
                    price_elem = item.find('span', class_='a8Pemb')
                    merchant_elem = item.find('div', class_='aULzUe')
                    image_elem = item.find('img', class_='TL92Hc')
                    
                    name = name_elem.text.strip() if name_elem else 'N/A'
                    price = price_elem.text.strip() if price_elem else 'N/A'
                    merchant = merchant_elem.text.strip() if merchant_elem else 'N/A'
                    image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                    
                    # Material is often not directly available on search results
                    material = 'N/A'
                    rating = 'N/A'
                    
                    # Try to find rating if available
                    rating_elem = item.find('div', class_='QIrs8')
                    if rating_elem:
                        rating = rating_elem.text.strip()
                    
                    normalized_price = normalize_price(price)
                    
                    # Add merchant name to the site field
                    site_name = f"Google Shopping - {merchant}" if merchant != 'N/A' else "Google Shopping"
                    
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': material,
                        'rating': rating,
                        'site': site_name
                    })
                except Exception as e:
                    logger.error(f"Error parsing Google Shopping product: {e}")
                    continue
        except TimeoutException:
            logger.warning("Timeout waiting for Google Shopping products to load")
            
    except Exception as e:
        logger.error(f"Error scraping Google Shopping: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_myntra(query):
    """Scrape product data from Myntra."""
    logger.info(f"Scraping Myntra for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.myntra.com/{query.replace(' ', '-')}"
        driver.get(search_url)
        
        # Wait for product cards to load
        try:
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.product-base"))
            )
            
            # Scroll down to load more products
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(SCROLL_WAIT_TIME)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all product cards
            product_cards = soup.find_all('li', class_='product-base')
            
            for item in product_cards[:10]:
                try:
                    # Extract product details
                    brand_elem = item.find('h3', class_='product-brand')
                    name_elem = item.find('h4', class_='product-product')
                    price_elem = item.find('span', class_='product-discountedPrice')
                    if not price_elem:
                        price_elem = item.find('div', class_='product-price')
                    image_elem = item.find('img', class_='product-image')
                    
                    brand = brand_elem.text.strip() if brand_elem else ''
                    product_name = name_elem.text.strip() if name_elem else 'N/A'
                    name = f"{brand} - {product_name}" if brand else product_name
                    price = price_elem.text.strip() if price_elem else 'N/A'
                    image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                    
                    # Material and rating often not available in search results
                    material = 'N/A'
                    rating = 'N/A'
                    
                    # Try to find rating if available
                    rating_elem = item.find('div', class_='product-ratingsContainer')
                    if rating_elem:
                        rating = rating_elem.text.strip()
                    
                    normalized_price = normalize_price(price)
                    
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': material,
                        'rating': rating,
                        'site': 'Myntra'
                    })
                except Exception as e:
                    logger.error(f"Error parsing Myntra product: {e}")
                    continue
        except TimeoutException:
            logger.warning("Timeout waiting for Myntra products to load")
            
    except Exception as e:
        logger.error(f"Error scraping Myntra: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_ajio(query):
    """Scrape product data from AJIO."""
    logger.info(f"Scraping AJIO for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.ajio.com/search/?text={query}"
        driver.get(search_url)
        
        # Wait for product cards to load
        try:
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.item.rilrtl-products-list__item"))
            )
            
            # Scroll down to load more products
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(SCROLL_WAIT_TIME)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all product cards
            product_cards = soup.find_all('div', class_='item rilrtl-products-list__item')
            
            for item in product_cards[:10]:
                try:
                    # Extract product details
                    brand_elem = item.find('div', class_='brand')
                    name_elem = item.find('div', class_='nameCls')
                    price_elem = item.find('span', class_='price')
                    image_elem = item.find('img')
                    
                    brand = brand_elem.text.strip() if brand_elem else ''
                    product_name = name_elem.text.strip() if name_elem else 'N/A'
                    name = f"{brand} - {product_name}" if brand else product_name
                    price = price_elem.text.strip() if price_elem else 'N/A'
                    image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                    
                    # Material and rating often not available in search results
                    material = 'N/A'
                    rating = 'N/A'
                    
                    normalized_price = normalize_price(price)
                    
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': material,
                        'rating': rating,
                        'site': 'AJIO'
                    })
                except Exception as e:
                    logger.error(f"Error parsing AJIO product: {e}")
                    continue
        except TimeoutException:
            logger.warning("Timeout waiting for AJIO products to load")
            
    except Exception as e:
        logger.error(f"Error scraping AJIO: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_flipkart(query):
    """Scrape product data from Flipkart."""
    logger.info(f"Scraping Flipkart for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.flipkart.com/search?q={query}"
        driver.get(search_url)
        
        # Wait for product cards to load
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div._1AtVbE"))
        )
        
        # Scroll to load more products
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(SCROLL_WAIT_TIME)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_cards = soup.find_all('div', class_='_1AtVbE')
        
        for item in product_cards[:10]:
            try:
                name_elem = item.find('div', class_='_4rR01T')
                price_elem = item.find('div', class_='_30jeq3')
                image_elem = item.find('img', class_='_396QI4')
                rating_elem = item.find('div', class_='_3LWZlK')
                
                name = name_elem.text if name_elem else 'N/A'
                price = price_elem.text if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                rating = rating_elem.text if rating_elem else 'N/A'
                
                normalized_price = normalize_price(price)
                
                products.append({
                    'name': name,
                    'price': normalized_price,
                    'price_display': price,
                    'image': image,
                    'material': 'N/A',
                    'rating': rating,
                    'site': 'Flipkart'
                })
            except Exception as e:
                logger.error(f"Error parsing Flipkart product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Flipkart: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_amazon(query):
    """Scrape product data from Amazon."""
    logger.info(f"Scraping Amazon for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.amazon.in/s?k={query}"
        driver.get(search_url)
        
        # Wait for product cards to load
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )
        
        # Scroll to load more products
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(SCROLL_WAIT_TIME)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_cards = soup.find_all('div', attrs={'data-component-type': 's-search-result'})
        
        for item in product_cards[:10]:
            try:
                name_elem = item.find('span', class_='a-text-normal')
                price_elem = item.find('span', class_='a-price-whole')
                image_elem = item.find('img', class_='s-image')
                rating_elem = item.find('span', class_='a-icon-alt')
                
                name = name_elem.text if name_elem else 'N/A'
                price = price_elem.text if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                rating = rating_elem.text if rating_elem else 'N/A'
                
                normalized_price = normalize_price(price)
                
                products.append({
                    'name': name,
                    'price': normalized_price,
                    'price_display': price,
                    'image': image,
                    'material': 'N/A',
                    'rating': rating,
                    'site': 'Amazon'
                })
            except Exception as e:
                logger.error(f"Error parsing Amazon product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Amazon: {e}")
    finally:
        driver.quit()
        
    return products

def scrape_tatacliq(query):
    """Scrape product data from Tata CLiQ."""
    logger.info(f"Scraping Tata CLiQ for: {query}")
    driver = setup_driver()
    products = []
    
    try:
        search_url = f"https://www.tatacliq.com/search/?searchCategory=all&text={query}"
        driver.get(search_url)
        
        # Wait for product cards to load
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductList__GridCol"))
        )
        
        # Scroll to load more products
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(SCROLL_WAIT_TIME)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_cards = soup.find_all('div', class_='ProductList__GridCol')
        
        for item in product_cards[:10]:
            try:
                name_elem = item.find('div', class_='ProductDescription__ProductName')
                price_elem = item.find('div', class_='ProductDescription__Price')
                image_elem = item.find('img', class_='ProductImage')
                rating_elem = item.find('div', class_='ProductDescription__Rating')
                
                name = name_elem.text if name_elem else 'N/A'
                price = price_elem.text if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                rating = rating_elem.text if rating_elem else 'N/A'
                
                normalized_price = normalize_price(price)
                
                products.append({
                    'name': name,
                    'price': normalized_price,
                    'price_display': price,
                    'image': image,
                    'material': 'N/A',
                    'rating': rating,
                    'site': 'Tata CLiQ'
                })
            except Exception as e:
                logger.error(f"Error parsing Tata CLiQ product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Tata CLiQ: {e}")
    finally:
        driver.quit()
        
    return products
