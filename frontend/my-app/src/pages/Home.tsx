import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Home.css';

interface User {
  id: string;
  username: string;
  email: string;
}

interface SearchResult {
  name: string;
  price: number;
  price_display?: string;
  image: string;
  url: string;
  site: string;
  rating?: string;
  material?: string;
}

const Home: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    } else {
      navigate('/login');
    }
  }, [navigate]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setError(null);
    setSearchResults([]);

    try {
      // Make the search request without requiring authentication
      const response = await fetch(`http://localhost:8000/api/search/?query=${encodeURIComponent(searchQuery)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Search results:', data);
      setSearchResults(data.results || []);

      // Save search to history if user is logged in
      const token = localStorage.getItem('token');
      if (token) {
        try {
          await fetch('http://localhost:8000/api/search/save/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ query: searchQuery }),
          });
        } catch (error) {
          console.error('Failed to save search history:', error);
        }
      }
    } catch (error) {
      console.error('Search failed:', error);
      setError('Failed to perform search. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="home-container">
      <div className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>Clothing Comparator</h2>
          <button 
            className="toggle-sidebar"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            {isSidebarOpen ? '←' : '→'}
          </button>
        </div>
        
        <div className="user-info">
          <h3>Welcome, {user?.username}</h3>
        </div>

        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search for clothing..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="search-button" disabled={isLoading}>
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </form>

        <nav className="sidebar-nav">
          <button onClick={() => navigate('/settings')} className="nav-button">
            Settings
          </button>
          <button onClick={handleLogout} className="nav-button logout">
            Logout
          </button>
        </nav>
      </div>

      <main className="main-content">
        {!searchQuery && !searchResults.length && (
          <div className="welcome-message">
            <h1>Welcome to Clothing Comparator</h1>
            <p>Start searching for your favorite clothing items!</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}

        {searchResults.length > 0 && (
          <div className="search-results">
            <h2>Search Results for "{searchQuery}"</h2>
            <div className="results-grid">
              {searchResults.map((item, index) => (
                <div key={index} className="result-card">
                  <img 
                    src={item.image !== 'N/A' ? item.image : '/placeholder-image.svg'} 
                    alt={item.name} 
                    className="result-image"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = '/placeholder-image.svg';
                    }}
                  />
                  <div className="result-details">
                    <h3>{item.name}</h3>
                    <p className="price">₹{item.price_display || item.price}</p>
                    {item.rating && item.rating !== 'N/A' && <p className="rating">Rating: {item.rating}</p>}
                    <p className="source">From: {item.site}</p>
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="view-button">
                      View Product
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Home; 