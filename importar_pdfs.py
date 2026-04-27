import os
import re
from pypdf import PdfReader
from database import db
from models import Propiedad
from app import app

def extraer_datos_pdf(ruta_archivo):
    """Extrae propiedades de un PDF (formato texto de Daperno)"""
    reader = PdfReader(ruta_archivo)
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text()
    
    # Lista de propiedades encontradas
    propiedades = []
    
    # Dividir por líneas
    lineas = texto_completo.split('\n')
    
    # Variables temporales para cada propiedad
    prop_actual = {}
    
    # Patrones para cada campo
    patron_precio_venta = r"PRECIO:\s*u?s?\$?\s*([\d\.]+)"
    patron_precio_alquiler = r"ALQUILER:\s*\$?\s*([\d\.]+)"
    patron_direccion = r"^([A-ZÑÁÉÍÓÚ\s]+)\s+(\d+)"
    patron_barrio = r"BARRIO:\s*([A-ZÑÁÉÍÓÚ\s]+)"
    patron_superficie = r"SUPERFICIE CUBIERTA:\s*([\d\.,]+)\s*Mts"
    patron_dormitorios = r"(\d+)\s*DORMITORIOS?"
    patron_banos = r"(\d+)\s*BAÑOS?"
    patron_ambientes = r"(\d+)\s*AMBIENTES?"
    
    for i, linea in enumerate(lineas):
        linea_limpia = linea.strip()
        if not linea_limpia:
            continue
        
        # Detectar inicio de propiedad (línea con dirección)
        if re.search(patron_direccion, linea_limpia) and "PRECIO" not in linea_limpia and "ALQUILER" not in linea_limpia:
            if prop_actual and ('precio' in prop_actual or 'precio_alquiler' in prop_actual):
                # Guardar propiedad anterior
                propiedades.append(prop_actual)
            prop_actual = {}
            # Extraer dirección y número
            dir_match = re.search(patron_direccion, linea_limpia)
            if dir_match:
                prop_actual['direccion'] = f"{dir_match.group(1)} {dir_match.group(2)}"
            else:
                prop_actual['direccion'] = linea_limpia
        
        # Determinar operación por contexto del archivo
        if "DEPARTAMENTOS EN VENTA" in texto_completo or "CASAS EN VENTA" in texto_completo:
            prop_actual['operacion'] = 'venta'
        elif "CASAS/DEPTOS. EN ALQUILER" in texto_completo:
            prop_actual['operacion'] = 'alquiler'
        elif "LOCALES COMERCIALES EN ALQUILER" in texto_completo:
            prop_actual['operacion'] = 'alquiler'
            prop_actual['tipo'] = 'Local comercial'
        
        # Barrio
        barrio_match = re.search(patron_barrio, linea_limpia, re.IGNORECASE)
        if barrio_match:
            prop_actual['barrio'] = barrio_match.group(1).strip()
        
        # Superficie
        sup_match = re.search(patron_superficie, linea_limpia, re.IGNORECASE)
        if sup_match:
            sup_str = sup_match.group(1).replace(',', '.')
            prop_actual['superficie'] = float(sup_str)
        
        # Precio de venta
        precio_match = re.search(patron_precio_venta, linea_limpia)
        if precio_match:
            precio_limpio = precio_match.group(1).replace('.', '').replace(',', '')
            prop_actual['precio'] = f"USD {precio_limpio}.-"
        
        # Precio de alquiler
        alq_match = re.search(patron_precio_alquiler, linea_limpia)
        if alq_match:
            precio_limpio = alq_match.group(1).replace('.', '').replace(',', '')
            prop_actual['precio'] = f"${precio_limpio}/mes"
        
        # Dormitorios
        dorm_match = re.search(patron_dormitorios, linea_limpia)
        if dorm_match:
            prop_actual['dormitorios'] = int(dorm_match.group(1))
        
        # Baños
        bano_match = re.search(patron_banos, linea_limpia)
        if bano_match:
            prop_actual['banos'] = int(bano_match.group(1))
        
        # Ambientes (si aparece)
        amb_match = re.search(patron_ambientes, linea_limpia)
        if amb_match:
            prop_actual['ambientes'] = int(amb_match.group(1))
    
    # Agregar la última propiedad
    if prop_actual and ('precio' in prop_actual or 'precio_alquiler' in prop_actual):
        propiedades.append(prop_actual)
    
    return propiedades

def limpiar_texto(texto):
    """Limpia nombres de calles, barrios, etc."""
    texto = texto.replace('  ', ' ').strip()
    # Capitalizar primeras letras
    return ' '.join(palabra.capitalize() for palabra in texto.split())

def guardar_propiedades(propiedades_lista):
    """Guarda las propiedades en la base de datos (evita duplicados por dirección)"""
    with app.app_context():
        for prop in propiedades_lista:
            # Verificar si ya existe una propiedad con esa dirección
            direccion = prop.get('direccion', '')
            if not direccion:
                continue
            existente = Propiedad.query.filter_by(direccion=direccion).first()
            if existente:
                print(f"Ya existe: {direccion}")
                continue
            
            # Determinar tipo (Casa, Departamento, Local comercial) según el archivo o palabras clave
            tipo = 'Casa'
            if 'DEPARTAMENTO' in str(prop) or 'DPTO' in str(prop):
                tipo = 'Departamento'
            elif 'LOCAL' in str(prop):
                tipo = 'Local comercial'
            elif 'TERRENO' in str(prop):
                tipo = 'Terreno'
            
            # Construir título automático
            titulo = f"{tipo} en {direccion.split(',')[0]}"
            
            nueva = Propiedad(
                titulo=titulo,
                operacion=prop.get('operacion', 'venta'),
                tipo=tipo,
                precio=prop.get('precio', 'Consultar'),
                direccion=direccion,
                barrio=prop.get('barrio', 'Esperanza'),
                latitud=-31.4472,   # coordenada por defecto, luego el usuario ajusta
                longitud=-60.9313,
                superficie=prop.get('superficie', 0),
                ambientes=prop.get('ambientes', 0),
                dormitorios=prop.get('dormitorios', 0),
                banos=prop.get('banos', 0),
                descripcion=f"Propiedad ubicada en {direccion}. Más información disponible.",
                destacado=False,
                activo=True
            )
            db.session.add(nueva)
            print(f"Agregada: {titulo} - {prop.get('precio')}")
        
        db.session.commit()
        print("¡Importación completada!")

if __name__ == "__main__":
    # Rutas de los PDFs (ajustá si están en otra carpeta)
    pdfs = [
        "DEPARTAMENTOS.pdf",
        "CASAS.pdf",
        "ALQUILERES.pdf",
        "Alquileres LOCALES COMERCIALES.pdf"
    ]
    
    todas_las_propiedades = []
    for pdf in pdfs:
        if os.path.exists(pdf):
            print(f"Procesando {pdf}...")
            props = extraer_datos_pdf(pdf)
            todas_las_propiedades.extend(props)
            print(f"  Encontradas {len(props)} propiedades.")
        else:
            print(f"Archivo no encontrado: {pdf}")
    
    # Guardar en la base de datos
    guardar_propiedades(todas_las_propiedades)