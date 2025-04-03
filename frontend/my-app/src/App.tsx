import { useState, useEffect } from 'react'
import './App.css'

interface Product {
  name: string;
  price: number;
  price_display: string;
  image: string;
  material: string;
  rating: string;
  site: string;
}

interface SearchResponse {
  query: string;
  total_results: number;
  results: Product[];
  execution_time: number;
  errors: string[] | null;
}

interface ErrorResponse {
  error: string;
  query: string;
  results: Product[];
}

function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [executionTime, setExecutionTime] = useState<number | null>(null)
  const [siteErrors, setSiteErrors] = useState<string[] | null>(null)
  const [filters, setFilters] = useState({
    source: 'all',
    minRating: '0',
    minPrice: '',
    maxPrice: ''
  })

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target
    setFilters(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const resetFilters = () => {
    setFilters({
      source: 'all',
      minRating: '0',
      minPrice: '',
      maxPrice: ''
    })
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    setError(null)
    setProducts([])
    setExecutionTime(null)
    setSiteErrors(null)

    try {
      // Build query parameters
      const params = new URLSearchParams({
        query: searchQuery
      })
      
      if (filters.source !== 'all') {
        params.append('sites', filters.source)
      }
      
      if (filters.minRating !== '0') {
        params.append('min_rating', filters.minRating)
      }
      
      if (filters.minPrice) {
        params.append('min_price', filters.minPrice)
      }
      
      if (filters.maxPrice) {
        params.append('max_price', filters.maxPrice)
      }

      const response = await fetch(`http://localhost:8000/api/search/?${params.toString()}`)
      const data = await response.json()

      if (!response.ok) {
        const errorData = data as ErrorResponse
        throw new Error(errorData.error || 'An error occurred while searching')
      }

      const searchData = data as SearchResponse
      setProducts(searchData.results)
      setExecutionTime(searchData.execution_time)
      setSiteErrors(searchData.errors)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while searching')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <header>
        <h1>
          ShopSphere
          <span className="clothing-animation">
            <span className="clothing-item">👕</span>
            <span className="clothing-item">👖</span>
            <span className="clothing-item">👗</span>
            <span className="clothing-item">🧥</span>
            <span className="clothing-item">👟</span>
          </span>
        </h1>
        <p>Your AI-Powered Clothing Search Engine</p>
      </header>

      <div className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter your search query (e.g., 'blue cotton shirt')"
            className="search-input"
          />
          <button type="submit" disabled={loading} className="search-button">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      <div className="filters-container">
        <h3>Filters</h3>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Source</label>
            <select 
              name="source" 
              value={filters.source} 
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="all">All Sources</option>
              <option value="myntra">Myntra</option>
              <option value="meesho">Meesho</option>
              <option value="nykaa">Nykaa Fashion</option>
              <option value="fabindia">FabIndia</option>
              <option value="ajio">AJIO</option>
              <option value="flipkart">Flipkart</option>
              <option value="amazon">Amazon</option>
              <option value="tatacliq">Tata CLiQ</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Min Rating</label>
            <select 
              name="minRating" 
              value={filters.minRating} 
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="0">Any Rating</option>
              <option value="3">3+ Stars</option>
              <option value="4">4+ Stars</option>
              <option value="4.5">4.5+ Stars</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Price Range</label>
            <div className="price-inputs">
              <input
                type="number"
                name="minPrice"
                value={filters.minPrice}
                onChange={handleFilterChange}
                placeholder="Min Price"
                className="price-input"
                min="0"
              />
              <input
                type="number"
                name="maxPrice"
                value={filters.maxPrice}
                onChange={handleFilterChange}
                placeholder="Max Price"
                className="price-input"
                min="0"
              />
            </div>
          </div>
          
          <div className="filter-group">
            <button onClick={resetFilters} className="reset-button">
              Reset Filters
            </button>
          </div>
        </div>
      </div>

      <div className="results-area">
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {siteErrors && siteErrors.length > 0 && (
          <div className="site-errors">
            <h3>Some sites returned errors:</h3>
            <ul>
              {siteErrors.map((err, index) => (
                <li key={index}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {executionTime && (
          <div className="execution-time">
            Search completed in {executionTime} seconds
          </div>
        )}

        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Searching across multiple stores...</p>
          </div>
        ) : products.length > 0 ? (
          <div className="results-container">
            <h2>Search Results ({products.length} items)</h2>
            <div className="products-grid">
              {products.map((product, index) => {
                const brand = product.name.includes('-') ? 
                  product.name.split('-')[0].trim() : '';
                
                const productName = product.name.includes('-') ? 
                  product.name.split('-').slice(1).join('-').trim() : product.name;
                
                return (
                  <div key={index} className="product-card">
                    <img 
                      src={product.image} 
                      alt={product.name} 
                      className="product-image"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = 'https://via.placeholder.com/150?text=No+Image';
                      }}
                    />
                    <div className="product-details">
                      {brand && <p className="product-brand">{brand}</p>}
                      <h3 className="product-name">{productName}</h3>
                      <p className="product-price">{product.price_display}</p>
                      {product.material && product.material !== 'N/A' && (
                        <p className="product-material">Material: {product.material}</p>
                      )}
                      {product.rating && product.rating !== 'N/A' && (
                        <p className="product-rating">
                          <span className="stars">★</span> {product.rating}
                        </p>
                      )}
                      <p className="product-site">
                        <span className={`site-badge site-${product.site.toLowerCase().replace(/\s+/g, '')}`}>
                          {product.site}
                        </span>
                      </p>
                      <div className="product-link">
                        <button className="view-button">View Product</button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : searchQuery && !loading && (
          <div className="no-results">
            <i className="no-results-icon">🔍</i>
            <h3>No results found for "{searchQuery}"</h3>
            <p>Try adjusting your search terms or filters</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
