from database import db
from datetime import datetime


class Propiedad(db.Model):
    __tablename__ = 'propiedades'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    operacion = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    barrio = db.Column(db.String(100), nullable=False)
    latitud = db.Column(db.Float, default=0)
    longitud = db.Column(db.Float, default=0)
    superficie = db.Column(db.Float, default=0)
    ambientes = db.Column(db.Integer, default=0)
    dormitorios = db.Column(db.Integer, default=0)
    banos = db.Column(db.Integer, default=0)
    descripcion = db.Column(db.Text, default='')
    destacado = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    imagenes = db.relationship('ImagenPropiedad', backref='propiedad', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'op': self.operacion,
            'tipo': self.tipo,
            'precio': self.precio,
            'dir': self.direccion,          # ← cambia direccion a dir
            'barrio': self.barrio,
            'lat': self.latitud,            # ← cambia latitud a lat
            'lng': self.longitud,           # ← cambia longitud a lng
            'sup': self.superficie,
            'amb': self.ambientes,
            'dorm': self.dormitorios,
            'ban': self.banos,
            'desc': self.descripcion,
            'destacado': self.destacado,
            'ico': self.get_icono(),        # esto debería ser un str emoji
            'fotos': [img.url for img in self.imagenes]  # ← cambia imagenes a fotos
    }
    
    def get_icono(self):
        iconos = {
            'Casa': '🏠',
            'Departamento': '🏢',
            'Local comercial': '🏪',
            'Oficina': '💼',
            'Terreno': '📐',
            'Campo': '🌾',
            'PH': '🏘️'
        }
        return iconos.get(self.tipo, '🏠')


class ImagenPropiedad(db.Model):
    __tablename__ = 'imagenes_propiedad'
    
    id = db.Column(db.Integer, primary_key=True)
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedades.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    orden = db.Column(db.Integer, default=0)