// Diese Karte wurde auch benutzt, um das statische Bild /static/images/map.png
// zu erstellen. Wenn die Karte geaendert wird, ggf. daran denken, das Bild zu
// erneuern. (Screenshot, Bild sollte die Hoehe von 600px der Karte beibehalten,
// links und rechts die Steuerelemente der interaktiven Karte abschneiden.)

var coordsPyCologne = [50.94850, 6.98636];

var map = L.map('map');

L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 18,
}).addTo(map);

var marker = L.marker(coordsPyCologne).addTo(map);
marker.bindPopup("<strong>PyCologne</strong>").openPopup();

// var path = L.polyline(
//     [coordsC4, [50.950250, 6.913100], [50.951000, 6.914000],
//      [50.951150, 6.915300], [50.952300, 6.913400], [50.951800, 6.912450],
//      [50.952200, 6.911850], coordsHerbrands],
//     {color: 'red'}).addTo(map);
var path = L.polyline([coordsPyCologne, {color: 'red'}).addTo(map);
map.fitBounds(path.getBounds());
