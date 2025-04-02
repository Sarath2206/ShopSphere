// Main application script for Clothing Comparator

// API endpoint configuration
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchQueryInput = document.getElementById('search-query');
const meeshoCheck = document.getElementById('meesho-check');
const nykaaCheck = document.getElementById('nykaa-check');
const fabindiaCheck = document.getElementById('fabindia-check');
const loadingIndicator = document.getElementById('loading');
const resultsContainer = document.getElementById('results-container');
const resultsTable = document.getElementById('results-table');
const noResultsMessage = document.getElementById('no-results');
const errorMessage = document.getElementById('error-message');
const sortOptions = document.querySelectorAll('.sort-option');

// Store the current results for sorting
let currentResults = [];

// Initialize the application
function init() {
    // Add event listeners
    searchForm.addEventListener('submit', handleSearch);
    sortOptions.forEach(option => {
        option.addEventListener('click', handleSort);
    });
}

// Handle form submission
async function handleSearch(event) {
    event.preventDefault();
    
    // Get search query
    const query = searchQueryInput.value.trim();
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    // Get selected sites
    const selectedSites = [];
    if (meeshoCheck.checked) selectedSites.push('meesho');
    if (nykaaCheck.checked) selectedSites.push('nykaa');
    if (fabindiaCheck.checked) selectedSites.push('fabindia');
    
    if (selectedSites.length === 0) {
        alert('Please select at least one site to search');
        return;
    }
    
    // Show loading indicator
    showLoading();
    
    try {
        // Fetch results from API
        const results = await fetchResults(query, selectedSites);
        
        // Update UI with results
        updateResults(results);
    } catch (error) {
        console.error('Error fetching results:', error);
        showError(error.message || 'An error occurred while fetching results');
    }
}

// Fetch results from the API
async function fetchResults(query, sites) {
    // Construct the API URL with query parameters
    const sitesParam = sites.join(',');
    const url = `${API_BASE_URL}/search/?query=${encodeURIComponent(query)}&sites=${encodeURIComponent(sitesParam)}`;
    
    // Make the API request
    const response = await fetch(url);
    
    // Check if the request was successful
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `API request failed with status ${response.status}`);
    }
    
    // Parse and return the response data
    const data = await response.json();
    return data;
}

// Update the UI with search results
function updateResults(data) {
    // Hide loading indicator
    hideLoading();
    
    // Store the current results for sorting
    currentResults = data.results || [];
    
    // Check if there are any results
    if (currentResults.length === 0) {
        showNoResults();
        return;
    }
    
    // Clear previous results
    resultsTable.innerHTML = '';
    
    // Add each result to the table
    currentResults.forEach(product => {
        const row = document.createElement('tr');
        
        // Image cell
        const imageCell = document.createElement('td');
        if (product.image && product.image !== 'N/A') {
            const img = document.createElement('img');
            img.src = product.image;
            img.alt = product.name;
            img.onerror = () => { img.src = 'https://via.placeholder.com/80?text=No+Image'; };
            imageCell.appendChild(img);
        } else {
            imageCell.textContent = 'No image';
        }
        row.appendChild(imageCell);
        
        // Name cell
        const nameCell = document.createElement('td');
        nameCell.textContent = product.name;
        row.appendChild(nameCell);
        
        // Price cell
        const priceCell = document.createElement('td');
        priceCell.textContent = product.price_display || 'N/A';
        row.appendChild(priceCell);
        
        // Material cell
        const materialCell = document.createElement('td');
        materialCell.textContent = product.material || 'N/A';
        row.appendChild(materialCell);
        
        // Rating cell
        const ratingCell = document.createElement('td');
        ratingCell.textContent = product.rating || 'N/A';
        row.appendChild(ratingCell);
        
        // Site cell
        const siteCell = document.createElement('td');
        const siteBadge = document.createElement('span');
        siteBadge.classList.add('site-badge');
        
        // Add site-specific class for styling
        if (product.site === 'Meesho') {
            siteBadge.classList.add('site-meesho');
        } else if (product.site === 'Nykaa Fashion') {
            siteBadge.classList.add('site-nykaa');
        } else if (product.site === 'FabIndia') {
            siteBadge.classList.add('site-fabindia');
        }
        
        siteBadge.textContent = product.site;
        siteCell.appendChild(siteBadge);
        row.appendChild(siteCell);
        
        // Add the row to the table
        resultsTable.appendChild(row);
    });
    
    // Show the results container
    resultsContainer.classList.remove('d-none');
    noResultsMessage.classList.add('d-none');
    errorMessage.classList.add('d-none');
}

// Handle sorting of results
function handleSort(event) {
    event.preventDefault();
    
    const sortType = event.target.getAttribute('data-sort');
    
    if (sortType === 'price-asc') {
        currentResults.sort((a, b) => {
            return (a.price || Infinity) - (b.price || Infinity);
        });
    } else if (sortType === 'price-desc') {
        currentResults.sort((a, b) => {
            return (b.price || -Infinity) - (a.price || -Infinity);
        });
    } else if (sortType === 'rating-desc') {
        currentResults.sort((a, b) => {
            const ratingA = parseFloat(a.rating) || 0;
            const ratingB = parseFloat(b.rating) || 0;
            return ratingB - ratingA;
        });
    }
    
    // Update the UI with the sorted results
    updateResults({ results: currentResults });
}

// Show loading indicator
function showLoading() {
    loadingIndicator.classList.remove('d-none');
    resultsContainer.classList.add('d-none');
    noResultsMessage.classList.add('d-none');
    errorMessage.classList.add('d-none');
}

// Hide loading indicator
function hideLoading() {
    loadingIndicator.classList.add('d-none');
}

// Show no results message
function showNoResults() {
    noResultsMessage.classList.remove('d-none');
    resultsContainer.classList.add('d-none');
    errorMessage.classList.add('d-none');
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('d-none');
    loadingIndicator.classList.add('d-none');
    resultsContainer.classList.add('d-none');
    noResultsMessage.classList.add('d-none');
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);
