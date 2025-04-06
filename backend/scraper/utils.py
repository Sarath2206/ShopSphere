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

# Increase timeout values and optimize settings
DEFAULT_TIMEOUT = 30  # seconds
PAGE_LOAD_TIMEOUT = 45  # seconds
SCROLL_WAIT_TIME = 2  # seconds
MAX_RETRIES = 3  # Number of retries for failed scraping attempts
MAX_CONCURRENT_SCRAPERS = 2  # Reduce concurrent scrapers to avoid overwhelming

def setup_driver():
    """Set up and return a configured Selenium WebDriver with advanced anti-bot bypasses."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-browser-side-navigation')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # Advanced anti-bot detection bypasses
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Performance optimizations
    prefs = {
        'profile.default_content_setting_values.notifications': 2,
        'profile.default_content_setting_values.images': 1,
        'profile.default_content_settings.popups': 0,
        'profile.managed_default_content_settings.javascript': 1,
        'profile.managed_default_content_settings.cookies': 1,
        'profile.managed_default_content_settings.plugins': 1,
        'profile.managed_default_content_settings.popups': 2,
        'profile.managed_default_content_settings.geolocation': 2,
        'profile.managed_default_content_settings.media_stream': 2,
    }
    options.add_experimental_option('prefs', prefs)
    
    # More realistic user agents with better distribution
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(DEFAULT_TIMEOUT)
        
        # Execute CDP commands to bypass anti-bot detection
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": random.choice(user_agents)
        })
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = {
                    runtime: {}
                };
            '''
        })
        
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver: {str(e)}")
        raise

def wait_for_element(driver, selector, timeout=DEFAULT_TIMEOUT):
    """Wait for an element to be present with multiple selectors."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return True
    except TimeoutException:
        return False

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
            if attempt > 0:
                time.sleep(2 ** attempt)  # Exponential backoff
            return scrape_func(query)
        except TimeoutException:
            logger.warning(f"Timeout on attempt {attempt + 1} for {scrape_func.__name__}")
            if attempt == max_retries - 1:
                logger.error(f"Max retries reached for {scrape_func.__name__}")
                return []
        except WebDriverException as e:
            logger.error(f"WebDriver error in {scrape_func.__name__}: {str(e)}")
            if attempt == max_retries - 1:
                return []
        except Exception as e:
            logger.error(f"Error in {scrape_func.__name__}: {str(e)}")
            if attempt == max_retries - 1:
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
    errors = []
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SCRAPERS) as executor:
        future_to_site = {
            executor.submit(scrape_with_retry, func, query): func.__name__
            for func in scraping_functions
        }
        
        for future in as_completed(future_to_site):
            site_name = future_to_site[future]
            try:
                products = future.result()
                if products:
                    all_products.extend(products)
                    logger.info(f"Completed scraping {site_name} - found {len(products)} products")
                else:
                    errors.append(f"No products found from {site_name}")
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {str(e)}")
                errors.append(f"Failed to scrape {site_name}: {str(e)}")
    
    if errors:
        logger.warning("Scraping completed with errors: %s", ", ".join(errors))
    
    return all_products

def scrape_meesho(query):
    """Scrape product data from Meesho with improved error handling."""
    logger.info(f"Scraping Meesho for: {query}")
    driver = None
    products = []
    
    try:
        driver = setup_driver()
        search_url = f"https://www.meesho.com/search?q={query}"
        driver.get(search_url)
        
        # Handle potential captcha or bot detection
        try:
            if "captcha" in driver.page_source.lower():
                logger.warning("Captcha detected on Meesho, waiting...")
                time.sleep(10)
                driver.refresh()
            
            if "robot" in driver.page_source.lower() or "verify" in driver.page_source.lower():
                logger.warning("Bot detection triggered on Meesho, waiting...")
                time.sleep(15)
                driver.refresh()
        except:
            pass
        
        # Wait for product cards with multiple selectors
        selectors = [
            "div.ProductList__GridCol-sc-8lnc8o-0",
            "div.ProductCard",
            "div[data-testid='product']",
            "div[class*='ProductList']",
            "div[class*='ProductCard']"
        ]
        
        for selector in selectors:
            if wait_for_element(driver, selector, 20):
                break
        
        # Scroll in a more natural way
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Additional wait for dynamic content
        time.sleep(random.uniform(2, 3))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find product cards with multiple selectors
        product_cards = []
        for selector in [
            lambda s: s.find_all('div', class_=lambda c: c and 'ProductList__GridCol' in c),
            lambda s: s.find_all('div', class_=lambda c: c and 'ProductCard' in c),
            lambda s: s.find_all('div', attrs={'data-testid': lambda x: x and 'product' in x.lower()}),
            lambda s: s.find_all('div', class_=lambda c: c and 'ProductList' in c),
            lambda s: s.find_all('div', class_=lambda c: c and 'ProductCard' in c)
        ]:
            product_cards = selector(soup)
            if product_cards:
                break
        
        for item in product_cards[:10]:
            try:
                name_elem = (
                    item.find('p', class_=lambda c: c and 'Text__StyledText' in c) or
                    item.find('div', class_=lambda c: c and 'ProductName' in c) or
                    item.find(class_=lambda c: c and 'name' in c.lower()) or
                    item.find('h3') or
                    item.find('h4')
                )
                
                price_elem = (
                    item.find('h5', class_=lambda c: c and 'Text__StyledText' in c) or
                    item.find(class_=lambda c: c and 'price' in c.lower()) or
                    item.find('span', class_=lambda c: c and 'rupee' in c.lower()) or
                    item.find('div', class_=lambda c: c and 'Price' in c)
                )
                
                image_elem = item.find('img')
                rating_elem = (
                    item.find('span', class_=lambda c: c and 'Rating' in c) or
                    item.find(class_=lambda c: c and 'rating' in c.lower())
                )
                
                # Find product link
                link_elem = item.find('a', href=True)
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.meesho.com{product_url}"
                
                if not name_elem or not price_elem:
                    continue
                
                name = name_elem.text.strip() if name_elem else 'N/A'
                price = price_elem.text.strip() if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                rating = rating_elem.text.strip() if rating_elem else 'N/A'
                
                normalized_price = normalize_price(price)
                
                if name != 'N/A' and normalized_price is not None:
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': 'N/A',
                        'rating': rating,
                        'site': 'Meesho',
                        'url': product_url
                    })
            except Exception as e:
                logger.error(f"Error parsing Meesho product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Meesho: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
    return products

def scrape_nykaa_fashion(query):
    """Scrape product data from Nykaa Fashion with improved error handling."""
    logger.info(f"Scraping Nykaa Fashion for: {query}")
    driver = None
    products = []
    
    try:
        driver = setup_driver()
        search_url = f"https://www.nykaafashion.com/search/?q={query}&type=text"
        driver.get(search_url)
        
        # Handle potential captcha or bot detection
        try:
            if "captcha" in driver.page_source.lower():
                logger.warning("Captcha detected on Nykaa Fashion, waiting...")
                time.sleep(10)
                driver.refresh()
            
            if "robot" in driver.page_source.lower() or "verify" in driver.page_source.lower():
                logger.warning("Bot detection triggered on Nykaa Fashion, waiting...")
                time.sleep(15)
                driver.refresh()
        except:
            pass
        
        # Wait for product cards with multiple selectors
        selectors = [
            "div[data-testid='product-card']",
            "div.product-card",
            "div.plp-card",
            "div[class*='product-card']",
            "div[class*='plp-card']"
        ]
        
        for selector in selectors:
            if wait_for_element(driver, selector, 20):
                break
        
        # Scroll in a more natural way
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Additional wait for dynamic content
        time.sleep(random.uniform(2, 3))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find product cards with multiple selectors
        product_cards = []
        for selector in [
            lambda s: s.find_all('div', attrs={'data-testid': 'product-card'}),
            lambda s: s.find_all('div', class_='product-card'),
            lambda s: s.find_all('div', class_='plp-card'),
            lambda s: s.find_all('div', class_=lambda c: c and 'product-card' in c),
            lambda s: s.find_all('div', class_=lambda c: c and 'plp-card' in c)
        ]:
            product_cards = selector(soup)
            if product_cards:
                break
        
        for item in product_cards[:10]:
            try:
                name_elem = (
                    item.find('p', class_='product-name') or
                    item.find('div', class_='product-name') or
                    item.find(class_=lambda c: c and 'name' in c.lower())
                )
                
                brand_elem = (
                    item.find('p', class_='brand-name') or
                    item.find('div', class_='brand-name') or
                    item.find(class_=lambda c: c and 'brand' in c.lower())
                )
                
                price_elem = (
                    item.find('span', class_='primary-price') or
                    item.find('span', class_='price') or
                    item.find(class_=lambda c: c and 'price' in c.lower())
                )
                
                image_elem = item.find('img')
                
                # Find product link
                link_elem = item.find('a', href=True)
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.nykaafashion.com{product_url}"
                
                if not name_elem or not price_elem:
                    continue
                
                brand = brand_elem.text.strip() if brand_elem else ''
                name = name_elem.text.strip() if name_elem else 'N/A'
                if brand and name != 'N/A':
                    name = f"{brand} - {name}"
                
                price = price_elem.text.strip() if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                
                normalized_price = normalize_price(price)
                
                if name != 'N/A' and normalized_price is not None:
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': 'N/A',
                        'rating': 'N/A',
                        'site': 'Nykaa Fashion',
                        'url': product_url
                    })
            except Exception as e:
                logger.error(f"Error parsing Nykaa Fashion product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Nykaa Fashion: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
    return products

def scrape_fabindia(query):
    """Scrape product data from FabIndia with improved error handling."""
    logger.info(f"Scraping FabIndia for: {query}")
    driver = None
    products = []
    
    try:
        driver = setup_driver()
        search_url = f"https://www.fabindia.com/search?q={query}"
        driver.get(search_url)
        
        # Handle potential captcha or bot detection
        try:
            if "captcha" in driver.page_source.lower():
                logger.warning("Captcha detected on FabIndia, waiting...")
                time.sleep(10)
                driver.refresh()
            
            if "robot" in driver.page_source.lower() or "verify" in driver.page_source.lower():
                logger.warning("Bot detection triggered on FabIndia, waiting...")
                time.sleep(15)
                driver.refresh()
        except:
            pass
        
        # Wait for product cards with multiple selectors
        selectors = [
            "div.product-item",
            "div[class*='product-item']",
            "div[class*='product-card']",
            "div[class*='product-grid']"
        ]
        
        for selector in selectors:
            if wait_for_element(driver, selector, 20):
                break
        
        # Scroll in a more natural way
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Additional wait for dynamic content
        time.sleep(random.uniform(2, 3))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find product cards with multiple selectors
        product_cards = []
        for selector in [
            lambda s: s.find_all('div', class_='product-item'),
            lambda s: s.find_all('div', class_=lambda c: c and 'product-item' in c),
            lambda s: s.find_all('div', class_=lambda c: c and 'product-card' in c),
            lambda s: s.find_all('div', class_=lambda c: c and 'product-grid' in c)
        ]:
            product_cards = selector(soup)
            if product_cards:
                break
        
        for item in product_cards[:10]:
            try:
                name_elem = (
                    item.find('div', class_='product-name') or
                    item.find('h2', class_='product-name') or
                    item.find(class_=lambda c: c and 'name' in c.lower())
                )
                
                price_elem = (
                    item.find('span', class_='price') or
                    item.find('div', class_='price') or
                    item.find(class_=lambda c: c and 'price' in c.lower())
                )
                
                image_elem = item.find('img', class_='product-image')
                
                # Find product link
                link_elem = item.find('a', href=True)
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.fabindia.com{product_url}"
                
                if not name_elem or not price_elem:
                    continue
                
                name = name_elem.text.strip() if name_elem else 'N/A'
                price = price_elem.text.strip() if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                
                normalized_price = normalize_price(price)
                
                if name != 'N/A' and normalized_price is not None:
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': 'N/A',
                        'rating': 'N/A',
                        'site': 'FabIndia',
                        'url': product_url
                    })
            except Exception as e:
                logger.error(f"Error parsing FabIndia product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping FabIndia: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
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
        
        # Wait for any product card to load with multiple selectors
        selectors = [
            "div.item.rilrtl-products-list__item",
            "div.preview",
            "div.product-card"
        ]
        
        for selector in selectors:
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                continue
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Scroll down multiple times to load more products
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(SCROLL_WAIT_TIME)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Try different selectors for product cards
        product_cards = []
        for selector in [
            lambda s: s.find_all('div', class_='item rilrtl-products-list__item'),
            lambda s: s.find_all('div', class_='preview'),
            lambda s: s.find_all('div', class_='product-card')
        ]:
            product_cards = selector(soup)
            if product_cards:
                break
        
        for item in product_cards[:10]:
            try:
                # Try multiple selectors for each element
                brand_elem = (
                    item.find('div', class_='brand') or
                    item.find('div', class_='brand-name') or
                    item.find(class_=lambda c: c and 'brand' in c.lower())
                )
                
                name_elem = (
                    item.find('div', class_='nameCls') or
                    item.find('div', class_='name') or
                    item.find(class_=lambda c: c and 'name' in c.lower())
                )
                
                price_elem = (
                    item.find('span', class_='price') or
                    item.find('div', class_='price') or
                    item.find(class_=lambda c: c and 'price' in c.lower())
                )
                
                image_elem = item.find('img')
                
                # Find product link
                link_elem = item.find('a', href=True)
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.ajio.com{product_url}"
                
                if not brand_elem or not price_elem:
                    continue
                
                brand = brand_elem.text.strip() if brand_elem else ''
                product_name = name_elem.text.strip() if name_elem else 'N/A'
                name = f"{brand} - {product_name}" if brand else product_name
                price = price_elem.text.strip() if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                
                normalized_price = normalize_price(price)
                
                if name != 'N/A' and normalized_price is not None:
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': 'N/A',
                        'rating': 'N/A',
                        'site': 'AJIO',
                        'url': product_url
                    })
            except Exception as e:
                logger.error(f"Error parsing AJIO product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping AJIO: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        
    return products

def scrape_flipkart(query):
    """Scrape product data from Flipkart with improved error handling."""
    logger.info(f"Scraping Flipkart for: {query}")
    driver = None
    products = []
    
    try:
        driver = setup_driver()
        search_url = f"https://www.flipkart.com/search?q={query}&type=product"
        driver.get(search_url)
        
        # Handle potential captcha or bot detection
        try:
            # Check for captcha page
            if "captcha" in driver.page_source.lower():
                logger.warning("Captcha detected on Flipkart, waiting...")
                time.sleep(10)
                driver.refresh()
            
            # Check for bot detection
            if "robot" in driver.page_source.lower() or "verify" in driver.page_source.lower():
                logger.warning("Bot detection triggered on Flipkart, waiting...")
                time.sleep(15)
                driver.refresh()
        except:
            pass
        
        # Wait for product cards with multiple selectors
        selectors = [
            "div[data-id]",
            "div._1AtVbE",
            "div._4ddWXP",
            "div._2B099V",
            "div[class*='_1AtVbE']",
            "div[class*='_4ddWXP']",
            "div[class*='_2B099V']"
        ]
        
        for selector in selectors:
            if wait_for_element(driver, selector, 20):
                break
        
        # Scroll in a more natural way
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Additional wait for dynamic content
        time.sleep(random.uniform(2, 3))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find product cards with multiple selectors
        product_cards = []
        for selector in [
            'div[data-id]',
            'div._1AtVbE',
            'div._4ddWXP',
            'div._2B099V',
            lambda s: s.find_all('div', class_=lambda c: c and '_1AtVbE' in c),
            lambda s: s.find_all('div', class_=lambda c: c and '_4ddWXP' in c),
            lambda s: s.find_all('div', class_=lambda c: c and '_2B099V' in c)
        ]:
            if isinstance(selector, str):
                product_cards = soup.find_all('div', attrs={'class': selector.replace('div.', '')} if '.' in selector else {'data-id': True})
            else:
                product_cards = selector(soup)
            if product_cards:
                break
        
        for item in product_cards[:10]:
            try:
                name_elem = (
                    item.find('a', class_='IRpwTa') or
                    item.find('a', class_='s1Q9rs') or
                    item.find('div', class_='_4rR01T') or
                    item.find('a', class_='_2rpwqI') or
                    item.find('div', class_=lambda c: c and 'title' in c.lower()) or
                    item.find('a', class_=lambda c: c and 'title' in c.lower())
                )
                
                price_elem = (
                    item.find('div', class_='_30jeq3') or
                    item.find('div', class_='_3I9_wc') or
                    item.find('div', class_=lambda c: c and 'price' in c.lower()) or
                    item.find('span', class_=lambda c: c and 'price' in c.lower())
                )
                
                image_elem = (
                    item.find('img', class_='_2r_T1I') or
                    item.find('img', class_='_396cs4') or
                    item.find('img', class_='_2QN9ow') or
                    item.find('img', class_=lambda c: c and 'image' in c.lower())
                )
                
                rating_elem = (
                    item.find('div', class_='_3LWZlK') or
                    item.find('div', class_='gUuXy-') or
                    item.find('div', class_=lambda c: c and 'rating' in c.lower())
                )
                
                # Find product link
                link_elem = item.find('a', href=True)
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.flipkart.com{product_url}"
                
                if not name_elem or not price_elem:
                    continue
                
                name = name_elem.text.strip() if name_elem else 'N/A'
                price = price_elem.text.strip() if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                rating = rating_elem.text.strip() if rating_elem else 'N/A'
                
                normalized_price = normalize_price(price)
                
                if name != 'N/A' and normalized_price is not None:
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': 'N/A',
                        'rating': rating,
                        'site': 'Flipkart',
                        'url': product_url
                    })
            except Exception as e:
                logger.error(f"Error parsing Flipkart product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Flipkart: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
    return products

def scrape_amazon(query):
    """Scrape product data from Amazon with improved error handling."""
    logger.info(f"Scraping Amazon for: {query}")
    driver = None
    products = []
    
    try:
        driver = setup_driver()
        search_url = f"https://www.amazon.in/s?k={query}"
        driver.get(search_url)
        
        # Handle potential captcha or bot detection
        try:
            # Check for captcha page
            if "captcha" in driver.page_source.lower():
                logger.warning("Captcha detected on Amazon, waiting...")
                time.sleep(10)
                driver.refresh()
            
            # Check for bot detection
            if "robot" in driver.page_source.lower() or "verify" in driver.page_source.lower():
                logger.warning("Bot detection triggered on Amazon, waiting...")
                time.sleep(15)
                driver.refresh()
        except:
            pass
        
        # Wait for product cards with multiple selectors
        selectors = [
            "div[data-component-type='s-search-result']",
            "div.s-result-item",
            "div[data-asin]",
            "div[class*='s-result-item']"
        ]
        
        for selector in selectors:
            if wait_for_element(driver, selector, 20):
                break
        
        # Scroll in a more natural way
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Additional wait for dynamic content
        time.sleep(random.uniform(2, 3))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find product cards with multiple selectors
        product_cards = []
        for selector in [
            lambda s: s.find_all('div', attrs={'data-component-type': 's-search-result'}),
            lambda s: s.find_all('div', class_='s-result-item'),
            lambda s: s.find_all('div', attrs={'data-asin': True}),
            lambda s: s.find_all('div', class_=lambda c: c and 's-result-item' in c)
        ]:
            product_cards = selector(soup)
            if product_cards:
                break
        
        for item in product_cards[:10]:
            try:
                name_elem = (
                    item.find('span', class_='a-text-normal') or
                    item.find('h2', class_='a-size-mini') or
                    item.find('h2', class_='a-size-medium') or
                    item.find(class_=lambda c: c and 'title' in c.lower())
                )
                
                price_elem = (
                    item.find('span', class_='a-price-whole') or
                    item.find('span', class_='a-offscreen') or
                    item.find(class_=lambda c: c and 'price' in c.lower())
                )
                
                image_elem = (
                    item.find('img', class_='s-image') or
                    item.find('img', class_=lambda c: c and 'image' in c.lower())
                )
                
                rating_elem = (
                    item.find('span', class_='a-icon-alt') or
                    item.find(class_=lambda c: c and 'rating' in c.lower())
                )
                
                # Find product link
                link_elem = item.find('a', class_='a-link-normal')
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.amazon.in{product_url}"
                
                if not name_elem or not price_elem:
                    continue
                
                name = name_elem.text.strip() if name_elem else 'N/A'
                price = price_elem.text.strip() if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                rating = rating_elem.text.strip() if rating_elem else 'N/A'
                
                normalized_price = normalize_price(price)
                
                if name != 'N/A' and normalized_price is not None:
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': 'N/A',
                        'rating': rating,
                        'site': 'Amazon',
                        'url': product_url
                    })
            except Exception as e:
                logger.error(f"Error parsing Amazon product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Amazon: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
    return products

def scrape_tatacliq(query):
    """Scrape product data from Tata CLiQ with improved error handling."""
    logger.info(f"Scraping Tata CLiQ for: {query}")
    driver = None
    products = []
    
    try:
        driver = setup_driver()
        search_url = f"https://www.tatacliq.com/search/?searchCategory=all&text={query}"
        driver.get(search_url)
        
        # Handle potential captcha or bot detection
        try:
            if "captcha" in driver.page_source.lower():
                logger.warning("Captcha detected on Tata CLiQ, waiting...")
                time.sleep(10)
                driver.refresh()
            
            if "robot" in driver.page_source.lower() or "verify" in driver.page_source.lower():
                logger.warning("Bot detection triggered on Tata CLiQ, waiting...")
                time.sleep(15)
                driver.refresh()
        except:
            pass
        
        # Wait for product cards with multiple selectors
        selectors = [
            "div.ProductList__GridCol",
            "div[class*='ProductList']",
            "div[class*='ProductCard']",
            "div[data-testid='product']"
        ]
        
        for selector in selectors:
            if wait_for_element(driver, selector, 20):
                break
        
        # Scroll in a more natural way
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Additional wait for dynamic content
        time.sleep(random.uniform(2, 3))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find product cards with multiple selectors
        product_cards = []
        for selector in [
            lambda s: s.find_all('div', class_='ProductList__GridCol'),
            lambda s: s.find_all('div', class_=lambda c: c and 'ProductList' in c),
            lambda s: s.find_all('div', class_=lambda c: c and 'ProductCard' in c),
            lambda s: s.find_all('div', attrs={'data-testid': 'product'})
        ]:
            product_cards = selector(soup)
            if product_cards:
                break
        
        for item in product_cards[:10]:
            try:
                name_elem = (
                    item.find('div', class_='ProductDescription__ProductName') or
                    item.find('div', class_=lambda c: c and 'ProductName' in c) or
                    item.find(class_=lambda c: c and 'name' in c.lower())
                )
                
                price_elem = (
                    item.find('div', class_='ProductDescription__Price') or
                    item.find('div', class_=lambda c: c and 'Price' in c) or
                    item.find(class_=lambda c: c and 'price' in c.lower())
                )
                
                image_elem = item.find('img', class_='ProductImage')
                
                # Find product link
                link_elem = item.find('a', href=True)
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = f"https://www.tatacliq.com{product_url}"
                
                if not name_elem or not price_elem:
                    continue
                
                name = name_elem.text.strip() if name_elem else 'N/A'
                price = price_elem.text.strip() if price_elem else 'N/A'
                image = image_elem['src'] if image_elem and 'src' in image_elem.attrs else 'N/A'
                
                normalized_price = normalize_price(price)
                
                if name != 'N/A' and normalized_price is not None:
                    products.append({
                        'name': name,
                        'price': normalized_price,
                        'price_display': price,
                        'image': image,
                        'material': 'N/A',
                        'rating': 'N/A',
                        'site': 'Tata CLiQ',
                        'url': product_url
                    })
            except Exception as e:
                logger.error(f"Error parsing Tata CLiQ product: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Tata CLiQ: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
    return products
