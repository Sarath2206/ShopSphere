// Search page component
function initSearchPage() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <header class="py-4 mb-4 border-bottom">
            <h1 class="text-center">ShopSphere</h1>
            <nav class="text-center">
                <a href="/index.html" class="btn btn-outline-primary">Back to Home</a>
            </nav>
        </header>
        
        <div class="row">
            <div class="col-md-12">
                <div class="card mb-4">
                    <div class="card-header">
                        <h2>Search for Clothing</h2>
                    </div>
                    <div class="card-body">
                        <form id="search-form">
                            <div class="mb-3">
                                <label for="search-query" class="form-label">What are you looking for?</label>
                                <input type="text" class="form-control" id="search-query" 
                                    placeholder="e.g., black shirt, medium size" required>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Select Sites to Compare:</label>
                                <div class="filter-container">
                                    <div class="filter-group">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" value="meesho" id="meesho-check" checked>
                                            <label class="form-check-label" for="meesho-check">
                                                Meesho
                                            </label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" value="nykaa" id="nykaa-check" checked>
                                            <label class="form-check-label" for="nykaa-check">
                                                Nykaa Fashion
                                            </label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" value="fabindia" id="fabindia-check" checked>
                                            <label class="form-check-label" for="fabindia-check">
                                                FabIndia
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <button type="submit" class="btn btn-primary">Compare Products</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12">
                <div class="card mb-4">
                    <div class="card-header">
                        <h2>Filters</h2>
                    </div>
                    <div class="card-body">
                        <div class="filters-grid">
                            <div class="filter-item">
                                <label class="form-label">Source</label>
                                <select class="form-select" id="source-filter">
                                    <option value="all">All Sources</option>
                                    <option value="meesho">Meesho</option>
                                    <option value="nykaa">Nykaa Fashion</option>
                                    <option value="fabindia">FabIndia</option>
                                </select>
                            </div>
                            
                            <div class="filter-item">
                                <label class="form-label">Min Rating</label>
                                <select class="form-select" id="rating-filter">
                                    <option value="any">Any Rating</option>
                                    <option value="4">4+ Stars</option>
                                    <option value="3">3+ Stars</option>
                                    <option value="2">2+ Stars</option>
                                </select>
                            </div>
                            
                            <div class="filter-item price-range">
                                <label class="form-label">Price Range</label>
                                <div class="price-inputs">
                                    <input type="number" class="form-control" id="min-price" placeholder="Min Price">
                                    <input type="number" class="form-control" id="max-price" placeholder="Max Price">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="loading" class="text-center d-none">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Searching across sites... This may take a moment.</p>
        </div>
        
        <div id="results-container" class="d-none">
            <div class="row mb-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h2>Results</h2>
                            <div class="dropdown">
                                <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" id="sortDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                                    Sort by
                                </button>
                                <ul class="dropdown-menu" aria-labelledby="sortDropdown">
                                    <li><a class="dropdown-item sort-option" data-sort="price-asc" href="#">Price: Low to High</a></li>
                                    <li><a class="dropdown-item sort-option" data-sort="price-desc" href="#">Price: High to Low</a></li>
                                    <li><a class="dropdown-item sort-option" data-sort="rating-desc" href="#">Rating: High to Low</a></li>
                                </ul>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Image</th>
                                            <th>Product</th>
                                            <th>Price</th>
                                            <th>Material</th>
                                            <th>Rating</th>
                                            <th>Site</th>
                                        </tr>
                                    </thead>
                                    <tbody id="results-table">
                                        <!-- Results will be inserted here -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="no-results" class="alert alert-info d-none" role="alert">
            No products found matching your search criteria.
        </div>
        
        <div id="error-message" class="alert alert-danger d-none" role="alert">
            An error occurred while fetching results.
        </div>
    `;
}

// Initialize the search page
document.addEventListener('DOMContentLoaded', () => {
    initSearchPage();
    // Initialize the search functionality
    init();
}); 