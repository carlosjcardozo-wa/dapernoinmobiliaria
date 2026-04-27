import pdfplumber
import re
from database import db
from models import Propiedad
from app import app

def extraer_con_pdfplumber(ruta):
    with pdfplumber.open(ruta) as pdf:
        texto = ''
        for page in pdf.pages:
            texto += page.extract_text() + '\n'
    return texto

def procesar_pdf(ruta, operacion_default='venta', tipo_default='Casa'):
    texto = extraer_con_pdfplumber(ruta)
    lineas = texto.split('\n')
    propiedades = []
    actual = {}
    
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        
        # Detectar dirección (patrón: calle + número)
        if re.match(r'^[A-ZÁÉÍÓÚÑ\s]+ \d+', linea, re.IGNORECASE):
            if actual and 'precio' in actual:
                propiedades.append(actual)
            actual = {'operacion': operacion_default, 'tipo': tipo_default}
            # separar calle y número
            partes = linea.split()
            numero = partes[-1]
            calle = ' '.join(partes[:-1])
            actual['direccion'] = f"{calle} {numero}"
        
        # Precio (dólares o pesos)
        if 'PRECIO:' in linea or 'u$s' in linea.lower():
            precios = re.findall(r'[\d\.]+', linea)
            if precios:
                actual['precio'] = f"USD {precios[0]}"
        if 'ALQUILER:' in linea:
            precios = re.findall(r'[\d\.]+', linea)
            if precios:
                actual['precio'] = f"${precios[0]}/mes"
        
        # Barrio
        if 'BARRIO:' in linea:
            barrio = linea.split('BARRIO:')[-1].strip()
            actual['barrio'] = barrio
        
        # Superficie
        sup = re.search(r'SUPERFICIE CUBIERTA:? (\d+[\.,]?\d*)', linea)
        if sup:
            actual['superficie'] = float(sup.group(1).replace(',', '.'))
        
        # Dormitorios
        dorm = re.search(r'(\d+) DORMITORIOS?', linea)
        if dorm:
            actual['dormitorios'] = int(dorm.group(1))
        
        # Baños
        ban = re.search(r'(\d+) BAÑOS?', linea)
        if ban:
            actual['banos'] = int(ban.group(1))
    
    if actual and 'precio' in actual:
        propiedades.append(actual)
    return propiedades

def guardar_todo(propiedades):
    with app.app_context():
        for p in propiedades:
            # evitar duplicados por dirección
            if Propiedad.query.filter_by(direccion=p.get('direccion')).first():
                print(f"Saltando duplicado: {p.get('direccion')}")
                continue
            nueva = Propiedad(
                titulo=f"{p.get('tipo', 'Propiedad')} en {p.get('direccion', '')}",
                operacion=p.get('operacion', 'venta'),
                tipo=p.get('tipo', 'Casa'),
                precio=p.get('precio', 'Consultar'),
                direccion=p.get('direccion', ''),
                barrio=p.get('barrio', 'Esperanza'),
                superficie=p.get('superficie', 0),
                dormitorios=p.get('dormitorios', 0),
                banos=p.get('banos', 0),
                descripcion=p.get('descripcion', ''),
                activo=True
            )
            db.session.add(nueva)
            print(f"Agregada: {nueva.titulo} - {nueva.precio}")
        db.session.commit()

if __name__ == '__main__':
    archivos = [
        ('DEPARTAMENTOS.pdf', 'venta', 'Departamento'),
        ('CASAS.pdf', 'venta', 'Casa'),
        ('ALQUILERES.pdf', 'alquiler', 'Casa'),
        ('Alquileres LOCALES COMERCIALES.pdf', 'alquiler', 'Local comercial')
    ]
    todas = []
    for archivo, op, tipo in archivos:
        print(f"Procesando {archivo}...")
        props = procesar_pdf(archivo, op, tipo)
        todas.extend(props)
        print(f"  Encontradas: {len(props)}")
    guardar_todo(todas)