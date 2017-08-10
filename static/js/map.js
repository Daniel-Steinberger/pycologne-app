// Diese Karte wurde auch benutzt, um das statische Bild /static/images/map.png
// zu erstellen. Wenn die Karte geaendert wird, ggf. daran denken, das Bild zu
// erneuern. (Screenshot, Bild sollte die Hoehe von 600px der Karte beibehalten,
// links und rechts die Steuerelemente der interaktiven Karte abschneiden.)

var coordsC4 = [50.950360, 6.912850];
var coordsHerbrands = [50.951450, 6.910400];

var map = L.map('map');

L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 18,
}).addTo(map);

var marker = L.marker(coordsC4).addTo(map);
marker.bindPopup("<strong>Chaos Computer Club</strong><br>Treffen von PyCologne").openPopup();
marker = L.marker(coordsHerbrands).addTo(map);
marker.bindPopup("<strong>Herbrand's</strong><br>").openPopup();

var path = L.polyline(
    [coordsC4, [50.950250, 6.913100], [50.951000, 6.914000],
     [50.951150, 6.915300], [50.952300, 6.913400], [50.951800, 6.912450],
     [50.952200, 6.911850], coordsHerbrands],
    {color: 'red'}).addTo(map);
map.fitBounds(path.getBounds());
