# ShopSphere - AI-Powered Clothing Comparator

A cross-platform web application that scrapes clothing data from multiple e-commerce sites, normalizes the data, and presents it in a unified interface for comparison.

## Features

- **Multi-site Scraping**: Searches across Meesho, Nykaa Fashion, and FabIndia
- **Real-time Results**: Live scraping of product data
- **Data Normalization**: Standardizes fields across sites for better comparison
- **Sortable Results**: Sort by price (low to high, high to low) or rating
- **Responsive UI**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Django (Python) for API and scraping orchestration
- **Frontend**: HTML, CSS, JavaScript with Bootstrap for UI
- **Scraping**: Selenium (browser automation) + BeautifulSoup (HTML parsing)
- **Database**: SQLite for simple data storage

## Project Structure

```
clothing/
├── backend/             # Django backend
│   ├── api/             # API app
|   ├── custom_auth/     # authentication
│   ├── scraper/         # Scraping functionality
│   ├── backend/         # Django project settings
│   ├── templates/       
│   ├── db.sqlite3       # database
│   ├── requirements.txt # Python dependencies
│   └── manage.py        # Manage all migrations
├── frontend/            # Frontend files
│   ├── public/          # Public HTML files
│   ├── my-app/          # App frontend
│   ├── node_modules/    # modules
│   └── src/             # JavaScript and CSS
└── run.sh               # Script to run the application
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Chrome or Chromium browser (for Selenium)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd clothing
   ```

2. Run the application:
   ```
   ./run.sh
   ```

   This script will:
   - Install required Python packages
   - Start the Django backend server
   - Serve the frontend files
   - Open the application in your browser

3. Access the application at:
   ```
   http://localhost:3000/
   ```

## Usage

1. Enter your search query (e.g., "black shirt, medium size")
2. Select the sites you want to search
3. Click "Compare Products"
4. View and sort the results

## Edge Cases and Error Handling

- If a site blocks scraping, the application will continue with other sites
- Missing data fields are marked as "N/A"
- Timeout after 30 seconds for slow sites
- Error messages for failed requests

## Future Enhancements

- Add more e-commerce sites
- Implement user accounts to save searches
- Add advanced filtering options
- Implement image similarity comparison
- Add price history tracking

## License

MIT
