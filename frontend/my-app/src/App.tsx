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

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    setError(null)
    setProducts([])
    setExecutionTime(null)
    setSiteErrors(null)

    try {
      const response = await fetch(`http://localhost:8000/api/search/?query=${encodeURIComponent(searchQuery)}`)
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
        <h1>AI-Powered Clothing Comparator</h1>
        <p>Compare prices across multiple e-commerce sites</p>
      </header>

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
          <p>Searching across multiple sites...</p>
        </div>
      ) : products.length > 0 ? (
        <div className="results-container">
          <h2>Search Results ({products.length} items)</h2>
          <div className="products-grid">
            {products.map((product, index) => (
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
                  <h3 className="product-name">{product.name}</h3>
                  <p className="product-price">{product.price_display}</p>
                  <p className="product-material">Material: {product.material}</p>
                  <p className="product-rating">Rating: {product.rating}</p>
                  <p className="product-site">Site: {product.site}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : searchQuery && !loading && (
        <div className="no-results">
          No results found for "{searchQuery}"
        </div>
      )}
    </div>
  )
}

export default App
