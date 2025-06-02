// Initialize the map centered on Africa
const map = L.map('map').setView([0, 20], 3);

// Add OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Store country data and GeoJSON layers
let countriesData = {};
let countryLayers = {};

// Format numbers with commas
function formatNumber(num) {
    return num ? num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "N/A";
}

// Create popup content from template
function createPopupContent(country) {
    const template = document.getElementById('popup-template').innerHTML;
    const sectorTemplate = document.getElementById('sector-template').innerHTML;
    
    // Format sectors HTML
    let sectorsHtml = '';
    if (country.economy && country.economy.key_sectors) {
        country.economy.key_sectors.forEach(sector => {
            sectorsHtml += sectorTemplate
                .replace('{name}', sector.name)
                .replace('{value}', sector.value)
                .replace('{percentage}', sector.contribution);
        });
    }
    
    // Format GDP
    const gdp = country.economy && country.economy.gdp 
        ? (country.economy.gdp / 1000000000).toFixed(2) 
        : 'N/A';
    
    // Format population
    const population = country.demographics && country.demographics.population 
        ? formatNumber(country.demographics.population) 
        : 'N/A';
    
    // Replace template placeholders
    return template
        .replace('{country}', country.country.name)
        .replace('{capital}', country.country.capital)
        .replace('{population}', population)
        .replace('{gdp}', gdp)
        .replace('{sectors}', sectorsHtml);
}

// Update country info sidebar
function updateCountryInfo(country) {
    const infoDiv = document.getElementById('country-info');
    
    if (!country) {
        infoDiv.innerHTML = '<p>Click on a country to see details</p>';
        return;
    }
    
    // Format GDP
    const gdp = country.economy && country.economy.gdp 
        ? (country.economy.gdp / 1000000000).toFixed(2) 
        : 'N/A';
    
    // Format population
    const population = country.demographics && country.demographics.population 
        ? formatNumber(country.demographics.population) 
        : 'N/A';
    
    let html = `
        <h5>${country.country.name}</h5>
        <p><strong>Capital:</strong> ${country.country.capital}</p>
        <p><strong>Region:</strong> ${country.country.region || 'N/A'}</p>
        <p><strong>Population:</strong> ${population}</p>
        <p><strong>GDP:</strong> $${gdp} billion</p>
    `;
    
    if (country.economy && country.economy.key_sectors) {
        html += '<h6>Key Economic Sectors:</h6><ul>';
        country.economy.key_sectors.forEach(sector => {
            html += `<li>${sector.name}: ${sector.contribution}% ($${sector.value} billion)</li>`;
        });
        html += '</ul>';
    }
    
    infoDiv.innerHTML = html;
}

// Fetch GeoJSON data for all African countries
async function fetchMapData() {
    try {
        const response = await fetch('/api/v1/map-data');
        const geojsonData = await response.json();
        
        // Add GeoJSON layer to map
        const geojsonLayer = L.geoJSON(geojsonData, {
            style: {
                weight: 1,
                opacity: 1,
                color: '#666',
                fillOpacity: 0.3,
                fillColor: '#4CAF50'
            },
            onEachFeature: function(feature, layer) {
                const countryCode = feature.properties.ISO_A2;
                countryLayers[countryCode] = layer;
                
                // Add hover effect
                layer.on({
                    mouseover: function(e) {
                        layer.setStyle({
                            weight: 2,
                            fillOpacity: 0.5
                        });
                    },
                    mouseout: function(e) {
                        geojsonLayer.resetStyle(layer);
                    },
                    click: function(e) {
                        fetchCountryProfile(countryCode);
                    }
                });
            }
        }).addTo(map);
        
    } catch (error) {
        console.error('Error fetching map data:', error);
        alert('Failed to load map data. Please try again later.');
    }
}

// Fetch country profile data
async function fetchCountryProfile(countryCode) {
    try {
        const response = await fetch(`/api/v1/country-profile/${countryCode}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const countryData = await response.json();
        countriesData[countryCode] = countryData;
        
        // Update country info sidebar
        updateCountryInfo(countryData);
        
        // Add popup to country
        if (countryLayers[countryCode]) {
            countryLayers[countryCode].bindPopup(
                createPopupContent(countryData),
                { maxWidth: 300 }
            ).openPopup();
        }
        
    } catch (error) {
        console.error(`Error fetching country profile for ${countryCode}:`, error);
    }
}

// Search for a country
document.getElementById('search-btn').addEventListener('click', function() {
    const searchTerm = document.getElementById('country-search').value.trim().toLowerCase();
    const resultsDiv = document.getElementById('search-results');
    
    if (!searchTerm) {
        resultsDiv.innerHTML = '<p>Please enter a country name</p>';
        return;
    }
    
    // Simple search through country layers
    let found = false;
    for (const code in countryLayers) {
        const layer = countryLayers[code];
        const countryName = layer.feature.properties.NAME.toLowerCase();
        
        if (countryName.includes(searchTerm)) {
            // Zoom to country
            map.fitBounds(layer.getBounds());
            // Fetch and show country data
            fetchCountryProfile(code);
            found = true;
            break;
        }
    }
    
    if (!found) {
        resultsDiv.innerHTML = '<p>Country not found. Try another name.</p>';
    } else {
        resultsDiv.innerHTML = '';
    }
});

// Initialize map on page load
document.addEventListener('DOMContentLoaded', function() {
    fetchMapData();
});