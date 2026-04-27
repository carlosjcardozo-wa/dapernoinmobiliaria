let map;
let markers = {};

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.filtro-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filtro = btn.dataset.filtro;
            filtrarPropiedades(filtro);
        });
    });
    
    if (document.getElementById('map')) {
        initMap();
    }
});

function filtrarPropiedades(filtro) {
    const cards = document.querySelectorAll('.propiedad-card');
    cards.forEach(card => {
        const op = card.dataset.op;
        if (filtro === 'all' || op === filtro) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function initMap() {
    map = L.map('map').setView([-31.4472, -60.9313], 13);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
    }).addTo(map);
    
    if (typeof propiedadesData !== 'undefined') {
        propiedadesData.forEach(prop => {
            if (prop.latitud && prop.longitud) {
                const marker = L.marker([prop.latitud, prop.longitud]).addTo(map);
                marker.bindPopup(`
                    <b>${prop.titulo}</b><br>
                    ${prop.direccion}<br>
                    <strong>${prop.precio}</strong><br>
                    <a href="/propiedad/${prop.id}">Ver detalles</a>
                `);
                markers[prop.id] = marker;
            }
        });
    }
}