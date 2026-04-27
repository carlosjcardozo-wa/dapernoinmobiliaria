from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from database import db
from models import Propiedad, ImagenPropiedad
import os
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inmobiliaria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        import time
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(time.time())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        img = Image.open(file)
        img.thumbnail((1200, 1200))
        img.save(filepath, optimize=True, quality=85)
        
        return f'/static/uploads/{filename}'
    return None


def delete_image(filepath):
    if filepath and filepath.startswith('/static/uploads/'):
        full_path = filepath[1:]
        if os.path.exists(full_path):
            os.remove(full_path)


@app.route('/')
def index():
    propiedades = Propiedad.query.filter_by(activo=True).order_by(Propiedad.destacado.desc(), Propiedad.fecha_creacion.desc()).all()
    return render_template('index.html', propiedades=propiedades)


@app.route('/propiedad/<int:id>')
def propiedad_detail(id):
    propiedad = Propiedad.query.get_or_404(id)
    if not propiedad.activo:
        abort(404)
    return render_template('propiedad_detail.html', propiedad=propiedad)


@app.route('/api/propiedades')
def api_propiedades():
    propiedades = Propiedad.query.filter_by(activo=True).all()
    return jsonify([p.to_dict() for p in propiedades])


@app.route('/admin')
def admin_dashboard():
    propiedades = Propiedad.query.order_by(Propiedad.fecha_creacion.desc()).all()
    return render_template('admin/dashboard.html', propiedades=propiedades)


@app.route('/admin/nueva', methods=['GET', 'POST'])
def admin_nueva():
    if request.method == 'POST':
        propiedad = Propiedad(
            titulo=request.form.get('titulo'),
            operacion=request.form.get('operacion'),
            tipo=request.form.get('tipo'),
            precio=request.form.get('precio'),
            direccion=request.form.get('direccion'),
            barrio=request.form.get('barrio'),
            latitud=float(request.form.get('latitud', 0)),
            longitud=float(request.form.get('longitud', 0)),
            superficie=float(request.form.get('superficie', 0)),
            ambientes=int(request.form.get('ambientes', 0)),
            dormitorios=int(request.form.get('dormitorios', 0)),
            banos=int(request.form.get('banos', 0)),
            descripcion=request.form.get('descripcion'),
            destacado='destacado' in request.form,
            activo=True
        )
        db.session.add(propiedad)
        db.session.flush()
        
        fotos = request.files.getlist('fotos')
        for foto in fotos:
            if foto and foto.filename:
                path = save_image(foto)
                if path:
                    img = ImagenPropiedad(propiedad_id=propiedad.id, url=path)
                    db.session.add(img)
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/propiedad_form.html', propiedad=None)


@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
def admin_editar(id):
    propiedad = Propiedad.query.get_or_404(id)
    
    if request.method == 'POST':
        propiedad.titulo = request.form.get('titulo')
        propiedad.operacion = request.form.get('operacion')
        propiedad.tipo = request.form.get('tipo')
        propiedad.precio = request.form.get('precio')
        propiedad.direccion = request.form.get('direccion')
        propiedad.barrio = request.form.get('barrio')
        propiedad.latitud = float(request.form.get('latitud', 0))
        propiedad.longitud = float(request.form.get('longitud', 0))
        propiedad.superficie = float(request.form.get('superficie', 0))
        propiedad.ambientes = int(request.form.get('ambientes', 0))
        propiedad.dormitorios = int(request.form.get('dormitorios', 0))
        propiedad.banos = int(request.form.get('banos', 0))
        propiedad.descripcion = request.form.get('descripcion')
        propiedad.destacado = 'destacado' in request.form
        
        fotos = request.files.getlist('fotos')
        for foto in fotos:
            if foto and foto.filename:
                path = save_image(foto)
                if path:
                    img = ImagenPropiedad(propiedad_id=propiedad.id, url=path)
                    db.session.add(img)
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/propiedad_form.html', propiedad=propiedad)


@app.route('/admin/eliminar-imagen/<int:img_id>', methods=['POST'])
def admin_eliminar_imagen(img_id):
    imagen = ImagenPropiedad.query.get_or_404(img_id)
    delete_image(imagen.url)
    db.session.delete(imagen)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/toggle-destacado/<int:id>', methods=['POST'])
def admin_toggle_destacado(id):
    propiedad = Propiedad.query.get_or_404(id)
    propiedad.destacado = not propiedad.destacado
    db.session.commit()
    return jsonify({'destacado': propiedad.destacado})


@app.route('/admin/toggle-activo/<int:id>', methods=['POST'])
def admin_toggle_activo(id):
    propiedad = Propiedad.query.get_or_404(id)
    propiedad.activo = not propiedad.activo
    db.session.commit()
    return jsonify({'activo': propiedad.activo})


@app.route('/admin/eliminar/<int:id>', methods=['POST'])
def admin_eliminar(id):
    propiedad = Propiedad.query.get_or_404(id)
    for img in propiedad.imagenes:
        delete_image(img.url)
    db.session.delete(propiedad)
    db.session.commit()
    return jsonify({'success': True})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)