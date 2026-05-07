// Interaktive Karte fuer die Anfahrtsseite.
// Koordinaten: DVS AG, Schanzenstraße 30, 51063 Koeln (Carlswerk).

var coordsPyCologne = [50.9685015, 7.0115021];

var map = L.map('map').setView(coordsPyCologne, 17);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data &copy; <a href="https://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 18,
}).addTo(map);

var marker = L.marker(coordsPyCologne).addTo(map);
marker.bindPopup("<strong>PyCologne</strong>").openPopup();
