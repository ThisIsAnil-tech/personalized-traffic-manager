document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById('map')) {
        const map = L.map('map').setView([12.9716, 77.5946], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(map);
        let currentRouteLayer = null;
        let startMarker, endMarker; 
        document.getElementById('searchBtn').addEventListener('click', async () => {
            const from = document.getElementById('from').value;
            const to = document.getElementById('to').value;
            if (!from || !to) {
                alert('Please enter both From and To locations.');
                return;
            }
            if (currentRouteLayer) {
                map.removeLayer(currentRouteLayer);
                currentRouteLayer = null;
            }
            if (startMarker) {
                map.removeLayer(startMarker);
                startMarker = null;
            }
            if (endMarker) {
                map.removeLayer(endMarker);
                endMarker = null;
            }
            try {
                const response = await fetch('/route', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ from, to }),
                });
                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                    console.error('Route error:', data.error);
                    return;
                }
                if (data && data.features && data.features.length > 0 && data.features[0].geometry) {
                    const routeFeature = data.features[0];
                    const routeCoordinates = routeFeature.geometry.coordinates;
                    const leafletRouteCoords = routeCoordinates.map(coord => [coord[1], coord[0]]);
                    currentRouteLayer = L.geoJSON(routeFeature, {
                        style: {
                            color: '#007bff', 
                            weight: 5,
                            opacity: 0.8
                        }
                    }).addTo(map);
                    const startPoint = leafletRouteCoords[0];
                    const endPoint = leafletRouteCoords[leafletRouteCoords.length - 1];
                    startMarker = L.marker(startPoint)
                                    .addTo(map)
                                    .bindPopup("<b>Start Point</b>"); 
                    endMarker = L.marker(endPoint)
                                  .addTo(map)
                                  .bindPopup("<b>End Point</b>"); 
                    const bounds = currentRouteLayer.getBounds();
                    if (bounds.isValid()) {
                        map.fitBounds(bounds, { padding: [50, 50] });
                        console.log("🗺️ Map bounds fit to:", bounds);
                    } else {
                        console.warn("⚠️ Invalid bounds received from routeLayer.getBounds()");
                    }
                } else {
                    alert('No route found for the given locations.');
                }
            } catch (error) {
                console.error('Failed to fetch route:', error);
                alert('An error occurred while getting the route. Check console for details.');
            }
        });
    } 
}); 