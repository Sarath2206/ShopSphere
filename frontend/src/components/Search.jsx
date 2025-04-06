import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLocation } from 'react-router-dom';

const Search = () => {
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const initialQuery = queryParams.get('q') || '';
    
    const [searchQuery, setSearchQuery] = useState(initialQuery);
    const [searchResults, setSearchResults] = useState([]);
    const [searchHistory, setSearchHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedSites, setSelectedSites] = useState([]);
    const [minPrice, setMinPrice] = useState('');
    const [maxPrice, setMaxPrice] = useState('');
    const [minRating, setMinRating] = useState('');
    
    const availableSites = [
        { id: 'myntra', name: 'Myntra' },
        { id: 'ajio', name: 'AJIO' },
        { id: 'flipkart', name: 'Flipkart' },
        { id: 'amazon', name: 'Amazon' },
        { id: 'meesho', name: 'Meesho' },
        { id: 'nykaa', name: 'Nykaa Fashion' },
        { id: 'fabindia', name: 'Fabindia' },
        { id: 'tatacliq', name: 'Tata CLiQ' }
    ];

    useEffect(() => {
        fetchSearchHistory();
        if (initialQuery) {
            handleSearch(null, initialQuery);
        }
    }, [initialQuery]);

    const fetchSearchHistory = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get('http://localhost:8000/api/search-history/', {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            setSearchHistory(response.data);
        } catch (error) {
            console.error('Error fetching search history:', error);
        }
    };

    const handleSearch = async (e, query = searchQuery) => {
        if (e) e.preventDefault();
        if (!query.trim()) return;
        
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            
            // Build the search URL with filters
            let searchUrl = `http://localhost:8000/api/search/?query=${encodeURIComponent(query)}`;
            
            if (selectedSites.length > 0) {
                searchUrl += `&sites=${selectedSites.join(',')}`;
            }
            
            if (minPrice) searchUrl += `&min_price=${minPrice}`;
            if (maxPrice) searchUrl += `&max_price=${maxPrice}`;
            if (minRating) searchUrl += `&min_rating=${minRating}`;
            
            // Save search to history
            await axios.post(
                'http://localhost:8000/api/search-history/',
                { 
                    query: query,
                    filters: {
                        sites: selectedSites,
                        minPrice,
                        maxPrice,
                        minRating
                    }
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            // Perform the actual search
            const response = await axios.get(searchUrl);
            setSearchResults(response.data.results || []);
            fetchSearchHistory(); // Refresh search history
        } catch (error) {
            console.error('Error performing search:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleSite = (siteId) => {
        if (selectedSites.includes(siteId)) {
            setSelectedSites(selectedSites.filter(id => id !== siteId));
        } else {
            setSelectedSites([...selectedSites, siteId]);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-7xl mx-auto">
                <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
                    <form onSubmit={handleSearch} className="space-y-4">
                        <div className="flex gap-4">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search for clothing..."
                                className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            <button
                                type="submit"
                                disabled={loading}
                                className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                            >
                                {loading ? 'Searching...' : 'Search'}
                            </button>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Sites</label>
                                <div className="flex flex-wrap gap-2">
                                    {availableSites.map(site => (
                                        <button
                                            key={site.id}
                                            type="button"
                                            onClick={() => toggleSite(site.id)}
                                            className={`px-3 py-1 rounded-full text-sm ${
                                                selectedSites.includes(site.id)
                                                    ? 'bg-indigo-600 text-white'
                                                    : 'bg-gray-200 text-gray-800'
                                            }`}
                                        >
                                            {site.name}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Price Range</label>
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        placeholder="Min"
                                        value={minPrice}
                                        onChange={(e) => setMinPrice(e.target.value)}
                                        className="w-1/2 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    />
                                    <input
                                        type="number"
                                        placeholder="Max"
                                        value={maxPrice}
                                        onChange={(e) => setMaxPrice(e.target.value)}
                                        className="w-1/2 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    />
                                </div>
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Minimum Rating</label>
                                <input
                                    type="number"
                                    min="0"
                                    max="5"
                                    step="0.1"
                                    placeholder="Min Rating"
                                    value={minRating}
                                    onChange={(e) => setMinRating(e.target.value)}
                                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                />
                            </div>
                        </div>
                    </form>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="md:col-span-2">
                        <h2 className="text-2xl font-bold mb-4">Search Results</h2>
                        {loading ? (
                            <div className="text-center py-8">
                                <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-600"></div>
                                <p className="mt-2 text-gray-600">Searching across {selectedSites.length || 'all'} sites...</p>
                            </div>
                        ) : searchResults.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {searchResults.map((result, index) => (
                                    <div key={index} className="bg-white rounded-lg shadow p-4">
                                        <div className="aspect-w-1 aspect-h-1 mb-2">
                                            <img 
                                                src={result.image_url || 'https://via.placeholder.com/300x300?text=No+Image'} 
                                                alt={result.title}
                                                className="object-cover rounded-md w-full h-48"
                                            />
                                        </div>
                                        <h3 className="font-semibold text-lg">{result.title}</h3>
                                        <p className="text-indigo-600 font-bold">₹{result.price}</p>
                                        <p className="text-sm text-gray-500 mb-2">{result.source_website}</p>
                                        <a
                                            href={result.product_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                                        >
                                            View on {result.source_website}
                                        </a>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 bg-white rounded-lg shadow">
                                <p className="text-gray-600">No results found. Try a different search term or adjust your filters.</p>
                            </div>
                        )}
                    </div>

                    <div>
                        <h2 className="text-2xl font-bold mb-4">Search History</h2>
                        <div className="bg-white rounded-lg shadow p-4">
                            {searchHistory.length > 0 ? (
                                <ul className="space-y-2">
                                    {searchHistory.map((history, index) => (
                                        <li
                                            key={index}
                                            className="p-2 hover:bg-gray-50 rounded cursor-pointer"
                                            onClick={() => {
                                                setSearchQuery(history.query);
                                                if (history.filters) {
                                                    setSelectedSites(history.filters.sites || []);
                                                    setMinPrice(history.filters.minPrice || '');
                                                    setMaxPrice(history.filters.maxPrice || '');
                                                    setMinRating(history.filters.minRating || '');
                                                }
                                                handleSearch(null, history.query);
                                            }}
                                        >
                                            <div className="font-medium">{history.query}</div>
                                            <div className="text-sm text-gray-500">
                                                {new Date(history.created_at).toLocaleString()}
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="text-gray-500 text-center py-4">No search history yet</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Search; 