import asyncio
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from .utils import setup_driver, normalize_price, normalize_material
import time
from functools import wraps
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

class ClothingScraperAgent:
    def __init__(self):
        self.driver = None
        self.websites = {
            'meesho': {
                'url': 'https://www.meesho.com',
                'search_url': 'https://www.meesho.com/search?q={query}',
                'product_selector': '[class*="ProductList__GridCol"], [class*="ProductCard"], [data-testid*="product"]',
                'title_selector': 'p[class*="Text__StyledText"], div[class*="ProductName"], [class*="name"]',
                'price_selector': 'h5[class*="Text__StyledText"], [class*="price"], span[class*="rupee"]',
                'image_selector': 'img',
                'link_selector': 'a[href*="/p/"]',
                'size_selector': '[class*="size"], [class*="Size"]',
                'color_selector': '[class*="color"], [class*="Color"]',
                'gender_selector': '[class*="gender"], [class*="Gender"]'
            },
            'nykaa': {
                'url': 'https://www.nykaa.com',
                'search_url': 'https://www.nykaa.com/search/result/?q={query}',
                'product_selector': '[class*="product-card"], [class*="product-tile"]',
                'title_selector': '[class*="product-name"], [class*="title"]',
                'price_selector': '[class*="price"], [class*="amount"]',
                'image_selector': 'img[class*="product-image"]',
                'link_selector': 'a[href*="/p/"]',
                'size_selector': '[class*="size"], [class*="Size"]',
                'color_selector': '[class*="color"], [class*="Color"]',
                'gender_selector': '[class*="gender"], [class*="Gender"]'
            },
            'fabindia': {
                'url': 'https://www.fabindia.com',
                'search_url': 'https://www.fabindia.com/search?q={query}',
                'product_selector': '[class*="product-item"], [class*="product-card"]',
                'title_selector': '[class*="product-name"], [class*="title"]',
                'price_selector': '[class*="price"], [class*="amount"]',
                'image_selector': 'img[class*="product-image"]',
                'link_selector': 'a[href*="/product/"]',
                'size_selector': '[class*="size"], [class*="Size"]',
                'color_selector': '[class*="color"], [class*="Color"]',
                'gender_selector': '[class*="gender"], [class*="Gender"]'
            },
            'myntra': {
                'url': 'https://www.myntra.com',
                'search_url': 'https://www.myntra.com/{query}',
                'product_selector': '[class*="product-base"], [class*="product-card"]',
                'title_selector': '[class*="product-brand"], [class*="product-name"]',
                'price_selector': '[class*="product-price"], [class*="price"]',
                'image_selector': 'img[class*="product-image"]',
                'link_selector': 'a[href*="/p/"]',
                'size_selector': '[class*="size"], [class*="Size"]',
                'color_selector': '[class*="color"], [class*="Color"]',
                'gender_selector': '[class*="gender"], [class*="Gender"]'
            },
            'ajio': {
                'url': 'https://www.ajio.com',
                'search_url': 'https://www.ajio.com/search/?text={query}',
                'product_selector': '[class*="product-card"], [class*="product-tile"]',
                'title_selector': '[class*="name"], [class*="brand"]',
                'price_selector': '[class*="price"], [class*="amount"]',
                'image_selector': 'img[class*="product-image"]',
                'link_selector': 'a[href*="/p/"]',
                'size_selector': '[class*="size"], [class*="Size"]',
                'color_selector': '[class*="color"], [class*="Color"]',
                'gender_selector': '[class*="gender"], [class*="Gender"]'
            },
            'flipkart': {
                'url': 'https://www.flipkart.com',
                'search_url': 'https://www.flipkart.com/search?q={query}',
                'product_selector': 'div._1AtVbE',
                'title_selector': 'div._4rR01T',
                'price_selector': 'div._30jeq3',
                'image_selector': 'img._396cs4',
                'link_selector': 'a._1fQZEK'
            },
            'amazon': {
                'url': 'https://www.amazon.in',
                'search_url': 'https://www.amazon.in/s?k={query}',
                'product_selector': 'div[data-component-type="s-search-result"]',
                'title_selector': 'span.a-text-normal',
                'price_selector': 'span.a-price-whole',
                'image_selector': 'img.s-image',
                'link_selector': 'a.a-link-normal'
            },
            'tatacliq': {
                'url': 'https://www.tatacliq.com',
                'search_url': 'https://www.tatacliq.com/search/?searchCategory=all&text={query}',
                'product_selector': '[class*="product-card"], [class*="product-tile"]',
                'title_selector': '[class*="product-name"], [class*="title"]',
                'price_selector': '[class*="price"], [class*="amount"]',
                'image_selector': 'img[class*="product-image"]',
                'link_selector': 'a[href*="/p/"]',
                'size_selector': '[class*="size"], [class*="Size"]',
                'color_selector': '[class*="color"], [class*="Color"]',
                'gender_selector': '[class*="gender"], [class*="Gender"]'
            }
        }

    def initialize(self):
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
            self.driver.set_page_load_timeout(30)

    def apply_filters(self, product: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filters to a product"""
        if not filters:
            return True

        # Price filters
        if 'min_price' in filters and product.get('price', 0) < filters['min_price']:
            return False
        if 'max_price' in filters and product.get('price', float('inf')) > filters['max_price']:
            return False

        # Size filter
        if 'size' in filters and filters['size']:
            product_size = product.get('size', '').lower()
            filter_size = filters['size'].lower()
            if filter_size not in product_size:
                return False

        # Color filter
        if 'color' in filters and filters['color']:
            product_color = product.get('color', '').lower()
            filter_color = filters['color'].lower()
            if filter_color not in product_color:
                return False

        # Gender filter
        if 'gender' in filters and filters['gender']:
            product_gender = product.get('gender', '').lower()
            filter_gender = filters['gender'].lower()
            if filter_gender not in product_gender:
                return False

        return True

    @retry(max_attempts=3, delay=2)
    async def search_website(self, website: str, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search a specific website for clothing items"""
        if website not in self.websites:
            raise ValueError(f"Website {website} not supported")

        config = self.websites[website]
        results = []

        try:
            # Ensure driver is initialized
            await self.initialize()

            search_url = config['search_url'].format(query=query)
            logger.info(f"Searching {website} with URL: {search_url}")
            
            self.driver.get(search_url)
            
            try:
                # Wait for results with increased timeout
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config['product_selector']))
                )
            except TimeoutException:
                logger.warning(f"No results found on {website} for query: {query}")
                return []

            # Scroll to load more products
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                await asyncio.sleep(1)

            # Find all product elements
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, config['product_selector'])
            logger.info(f"Found {len(product_elements)} products on {website}")

            # Extract product information
            for element in product_elements[:20]:
                try:
                    product = self._extract_product_info(element, config, website)
                    if product and self.apply_filters(product, filters):
                        results.append(product)
                except Exception as e:
                    logger.warning(f"Error extracting product information from {website}: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Error searching {website}: {str(e)}")
            return []

    def _extract_product_info(self, element, config, website):
        """Extract product information from a web element"""
        try:
            # Extract title
            title_element = element.find_element(By.CSS_SELECTOR, config['title_selector'])
            title = title_element.text.strip()

            # Extract price
            price_element = element.find_element(By.CSS_SELECTOR, config['price_selector'])
            price = normalize_price(price_element.text.strip())

            # Extract image URL
            image_element = element.find_element(By.CSS_SELECTOR, config['image_selector'])
            image_url = image_element.get_attribute('src')

            # Extract product URL
            link_element = element.find_element(By.CSS_SELECTOR, config['link_selector'])
            product_url = link_element.get_attribute('href')

            # Extract optional fields
            size = self._get_optional_field(element, config['size_selector'])
            color = self._get_optional_field(element, config['color_selector'])
            gender = self._get_optional_field(element, config['gender_selector'])

            return {
                'source_website': website,
                'title': title,
                'price': price,
                'image_url': image_url,
                'product_url': product_url,
                'size': size,
                'color': color,
                'gender': gender
            }
        except Exception as e:
            logger.warning(f"Error extracting product info: {str(e)}")
            return None

    def _get_optional_field(self, element, selector):
        """Get optional field value from element"""
        try:
            field_element = element.find_element(By.CSS_SELECTOR, selector)
            return field_element.text.strip()
        except NoSuchElementException:
            return None
        except Exception as e:
            logger.warning(f"Error getting optional field: {str(e)}")
            return None

    async def search_all_websites(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search all supported websites for clothing items"""
        try:
            # Initialize web driver
            await self.initialize()

            # Create tasks for each website
            tasks = [
                self.search_website(website, query, filters)
                for website in self.websites.keys()
            ]

            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)

            # Flatten results
            all_results = [item for sublist in results for item in sublist]

            # Sort by price
            all_results.sort(key=lambda x: x.get('price', float('inf')))

            return all_results

        except Exception as e:
            logger.error(f"Error in search_all_websites: {str(e)}")
            return []
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Web driver cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up web driver: {str(e)}")
            # Don't raise the exception here to avoid masking other errors 