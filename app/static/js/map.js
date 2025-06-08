// Define Africa bounding box: [southWest, northEast]
const africaBounds = [
    [-35, -20], // Southwest (approx. Cape Town)
    [38, 55]    // Northeast (approx. Cairo)
];

// Initialize the map centered on Africa
const map = L.map('map', {
    maxBounds: africaBounds,
    maxBoundsViscosity: 1.0
}).setView([0, 20], 4);

// Use Esri World Imagery for high-res, 3D-like effect
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 18
}).addTo(map);

// Store country data and GeoJSON layers
let countriesData = {};
let countryLayers = {};

// Format numbers with commas
function formatNumber(num) {
    return num ? num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "N/A";
}

// Update country info sidebar
function updateCountryInfo(countryData) {
    const infoDiv = document.getElementById('country-info');
    
    // If no data, show default message
    if (!countryData || !countryData.country) {
        infoDiv.innerHTML = '<p>Select a country from the dropdown to see details</p>';
        return;
    }

    // Format GDP to billions with 2 decimal places
    const gdp = countryData.economy?.gdp 
        ? `$${(countryData.economy.gdp / 1000000000).toFixed(2)} billion`
        : 'N/A';

    // Format population with commas
    const population = countryData.demographics?.population
        ? formatNumber(countryData.demographics.population)
        : 'N/A';

    // Format GDP growth
    const gdpGrowth = countryData.economy?.gdp_growth
        ? `${countryData.economy.gdp_growth.toFixed(1)}%`
        : 'N/A';

    // Get flag URL
    const flagUrl = countryData.country.code
        ? `https://flagcdn.com/64x48/${countryData.country.code.toLowerCase()}.png`
        : '';

    // Generate sectors HTML if available
    const sectorsHtml = countryData.economy?.key_sectors
        ? `<div class="sectors-list mt-3">
            <h5>Key Economic Sectors:</h5>
            ${countryData.economy.key_sectors.map(sector => `
                <div class="sector-item mb-2">
                    <div><strong>${sector.name}</strong></div>
                    <div class="sector-bar">
                        <div class="sector-fill" style="width: ${sector.contribution}%"></div>
                    </div>
                    <small>$${sector.value} billion (${sector.contribution}% of GDP)</small>
                </div>
            `).join('')}
        </div>`
        : '';

    // Update the info div with all country information
    infoDiv.innerHTML = `
        <div class="country-details">
            ${flagUrl ? `<img src="${flagUrl}" alt="Flag of ${countryData.country.name}" 
                style="float:right;margin:0 0 10px 10px;border:1px solid #ddd;">` : ''}
            <h4>${countryData.country.name}</h4>
            <p><strong>Capital:</strong> ${countryData.country.capital}</p>
            <p><strong>Region:</strong> ${countryData.country.region}</p>
            <p><strong>Population:</strong> ${population}</p>
            <p><strong>Population Growth:</strong> ${countryData.demographics.growth_rate.toFixed(1)}%</p>
            <p><strong>Median Age:</strong> ${countryData.demographics.median_age} years</p>
            <p><strong>GDP:</strong> ${gdp}</p>
            <p><strong>GDP Growth:</strong> ${gdpGrowth}</p>
            <p><strong>Currency:</strong> ${countryData.economy.currency}</p>
            ${sectorsHtml}
        </div>
    `;
}

// Add a base URL constant at the top of your file
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Fetch and display country profile
function fetchCountryProfile(countryCode) {
    // Always fetch fresh data to ensure up-to-date info
    fetch(`${API_BASE_URL}/country-profile/${countryCode}`)
        .then(resp => resp.json())
        .then(profile => {
            countriesData[countryCode] = profile;
            updateCountryInfo(profile);
        })
        .catch(error => {
            console.error('Error fetching country profile:', error);
            updateCountryInfo(null);
        });
}

// Fetch map data and initialize countries layers
function fetchMapData() {
    fetch(`${API_BASE_URL}/map-data`)
        .then(response => response.json())
        .then(data => {
            L.geoJSON(data, {
                onEachFeature: (feature, layer) => {
                    const iso2 = feature.properties.ISO_A2;
                    if (!iso2) return;
                    
                    const countryCode = iso2.toUpperCase();
                    countryLayers[countryCode] = layer;
                    
                    // Show country name as tooltip
                    const countryName = feature.properties.NAME;
                    layer.bindTooltip(`<strong>${countryName}</strong>`, {
                        direction: 'center',
                        permanent: true,
                        className: 'country-label'
                    });
                    
                    // Add flag marker at centroid
                    const centroid = layer.getBounds().getCenter();
                    const flagUrl = `https://flagcdn.com/32x24/${countryCode.toLowerCase()}.png`;
                    const flagIcon = L.icon({
                        iconUrl: flagUrl,
                        iconSize: [32, 24],
                        iconAnchor: [16, 12],
                        popupAnchor: [0, -12]
                    });
                    L.marker(centroid, {icon: flagIcon, title: countryName, interactive: false}).addTo(map);
                }
            }).addTo(map);
            
            // Populate select after map is loaded
            populateCountrySelect();
        })
        .catch(error => {
            console.error('Error fetching map data:', error);
        });
}

// Populate country select dropdown
function populateCountrySelect() {
    const select = document.getElementById('country-select');
    // Clear existing options
    select.innerHTML = '<option value="">Select a country...</option>';
    
    // Sort countries by name
    const entries = Object.entries(countryLayers).sort((a, b) => {
        const nameA = a[1].feature.properties.NAME || '';
        const nameB = b[1].feature.properties.NAME || '';
        return nameA.localeCompare(nameB);
    });

    // Add country options
    for (const [code, layer] of entries) {
        const name = layer.feature.properties.NAME;
        const option = document.createElement('option');
        option.value = code;
        option.textContent = name;
        select.appendChild(option);
    }
}

// Initialize on document ready
document.addEventListener('DOMContentLoaded', function() {
    fetchMapData();

    const countrySelect = document.getElementById('country-select');
    if (countrySelect) {
        countrySelect.addEventListener('change', function() {
            const selectedCode = this.value;
            if (!selectedCode) {
                updateCountryInfo(null);
                return;
            }
            if (countryLayers[selectedCode]) {
                // Zoom to country
                map.fitBounds(countryLayers[selectedCode].getBounds());
                // Fetch and display country data
                fetch(`/api/v1/country-profile/${selectedCode}`)
                    .then(response => response.json())
                    .then(profile => {
                        countriesData[selectedCode] = profile;
                        updateCountryInfo(profile);
                        // Highlight selected country
                        Object.values(countryLayers).forEach(layer => {
                            layer.setStyle({ weight: 1, color: '#666' });
                        });
                        countryLayers[selectedCode].setStyle({
                            weight: 2,
                            color: '#ff7800'
                        });
                    });
            }
        });
    }
});