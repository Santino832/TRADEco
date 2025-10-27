from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import os

# Importar configuración
from config import Config

# Importar modelos
from models.user import User
from models.product import Product
from models.transaction import Transaction

# Importar rutas
from routes.auth import init_routes as init_auth_routes
from routes.products import init_routes as init_products_routes
from routes.users import init_routes as init_users_routes
from routes.transactions import init_routes as init_transactions_routes

# Crear aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Inicializar carpetas
Config.init_app()

# Carpeta del frontend (ahora está fuera de backend)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

# Mostrar información de debug
print(f"📁 Directorio de trabajo: {os.getcwd()}")
print(f"📁 Carpeta de backend: {os.path.dirname(__file__)}")
print(f"📁 Carpeta de frontend: {FRONTEND_DIR}")
print(f"📁 Frontend existe: {os.path.exists(FRONTEND_DIR)}")
print(f"📁 Carpeta de uploads: {os.path.abspath(Config.UPLOAD_FOLDER)}")
print(f"📁 Uploads existe: {os.path.exists(Config.UPLOAD_FOLDER)}")
print("")

# Conectar a MongoDB
try:
    client = MongoClient(Config.MONGODB_URI)
    db = client[Config.DB_NAME]
    
    # Verificar conexión
    client.admin.command('ping')
    print(f"✅ Conectado a MongoDB: {Config.DB_NAME}")
    
except Exception as e:
    print(f"❌ Error al conectar a MongoDB: {e}")
    exit(1)

# Inicializar modelos
user_model = User(db)
product_model = Product(db)
transaction_model = Transaction(db)

# Registrar blueprints (rutas)
auth_bp = init_auth_routes(db, user_model)
products_bp = init_products_routes(db, product_model, user_model)
users_bp = init_users_routes(db, user_model)
transactions_bp = init_transactions_routes(db, transaction_model, product_model, user_model)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(transactions_bp, url_prefix='/api/transactions')

# Ruta para servir archivos estáticos (imágenes)
@app.route('/uploads/products/<filename>')
def serve_uploads(filename):
    """Servir archivos subidos"""
    upload_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    print(f"📁 Intentando servir: {filename}")
    print(f"📁 Desde carpeta: {upload_dir}")
    print(f"📁 Archivo completo: {os.path.join(upload_dir, filename)}")
    print(f"📁 Existe: {os.path.exists(os.path.join(upload_dir, filename))}")
    
    try:
        return send_from_directory(upload_dir, filename)
    except Exception as e:
        print(f"❌ Error al servir archivo: {e}")
        return jsonify({'error': 'Archivo no encontrado'}), 404

# Servir frontend (HTML, CSS, JS) - RUTA CORREGIDA
@app.route('/')
def index():
    """Servir página principal"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    """Servir archivos del frontend"""
    try:
        # Verificar si el archivo existe en frontend
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.exists(file_path):
            return send_from_directory(FRONTEND_DIR, path)
        else:
            # Si no existe, devolver 404
            return jsonify({
                'success': False,
                'message': 'Archivo no encontrado'
            }), 404
    except Exception as e:
        print(f"❌ Error al servir frontend: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al servir archivo'
        }), 500

# Ruta de prueba
@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar que la API está funcionando"""
    return jsonify({
        'success': True,
        'message': 'API TRADEco funcionando correctamente',
        'version': '2.0.0',
        'frontend_path': FRONTEND_DIR,
        'frontend_exists': os.path.exists(FRONTEND_DIR)
    }), 200

# Manejador de errores 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Ruta no encontrada'
    }), 404

# Manejador de errores 500
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Error interno del servidor'
    }), 500

# Ejecutar aplicación
if __name__ == '__main__':
    print(f"🚀 Servidor iniciando en http://localhost:{Config.PORT}")
    print(f"📁 Sirviendo frontend desde: {FRONTEND_DIR}")
    print(f"📁 Carpeta de uploads: {Config.UPLOAD_FOLDER}")
    print(f"🔐 JWT expira en: {Config.JWT_EXPIRATION_HOURS} horas")
    print("\n📚 Endpoints disponibles:")
    print("  === AUTENTICACIÓN ===")
    print("  POST   /api/auth/register")
    print("  POST   /api/auth/login")
    print("\n  === PRODUCTOS ===")
    print("  GET    /api/products/")
    print("  POST   /api/products/")
    print("  GET    /api/products/<id>")
    print("  PUT    /api/products/<id>")
    print("  DELETE /api/products/<id>")
    print("\n  === USUARIOS ===")
    print("  GET    /api/users/profile")
    print("  PUT    /api/users/profile")
    print("  GET    /api/users/<id>")
    print("\n  === TRANSACCIONES ===")
    print("  POST   /api/transactions/reserve")
    print("  GET    /api/transactions/<id>")
    print("  GET    /api/transactions/code/<code>")
    print("  GET    /api/transactions/my-purchases")
    print("  GET    /api/transactions/my-sales")
    print("  POST   /api/transactions/<id>/seller-confirm")
    print("  POST   /api/transactions/<id>/buyer-confirm-payment")
    print("  POST   /api/transactions/<id>/complete")
    print("  POST   /api/transactions/<id>/cancel")
    print("  POST   /api/transactions/<id>/note")
    print("\n")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )