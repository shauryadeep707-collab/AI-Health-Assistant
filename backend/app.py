"""
Flask Application Factory for AI Health Assistant.
WHY factory pattern: allows creating the app with different configs for testing.
"""

import os
import secrets
from flask import Flask, session, request, jsonify, send_from_directory, g
from backend.config import config
from backend import db as database


def create_app():
    """Create and configure the Flask application."""
    
    # WHY static_folder=None: we serve frontend files manually for more control
    app = Flask(__name__, static_folder=None)
    
    # Load configuration
    app.secret_key = config.SECRET_KEY
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Project root for resolving frontend paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    frontend_dir = os.path.join(project_root, 'frontend')
    
    # --- Database connection per request ---
    @app.before_request
    def before_request():
        """Open a DB connection and store in Flask's g object."""
        g.db = database.get_connection()
    
    @app.teardown_appcontext
    def teardown_db(exception):
        """Close the DB connection after each request."""
        db_conn = g.pop('db', None)
        if db_conn is not None:
            database.close_connection(db_conn)
    
    # --- CSRF Protection ---
    @app.before_request
    def csrf_protect():
        """Check CSRF token on state-changing requests.
        WHY: prevents cross-site request forgery attacks.
        """
        # In automated tests, CSRF checking is bypassed
        if app.config.get('TESTING'):
            return

        # Ensure session has a CSRF token
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        
        # Only check on state-changing methods to API routes
        if request.method in ('POST', 'PUT', 'DELETE') and request.path.startswith('/api/'):
            # Exempt auth endpoints that need to work before the user has a token
            exempt = [
                '/api/auth/login', '/api/auth/register', '/api/auth/csrf',
                '/api/medicines/ask', '/api/facial/checkup', '/api/system/storage-info'
            ]
            if request.path in exempt:
                return
            
            token = request.headers.get('X-CSRF-Token', '')
            if token != session.get('csrf_token'):
                return jsonify({'ok': False, 'error': 'Invalid CSRF token'}), 403
    
    # --- Security Headers ---
    @app.after_request
    def add_security_headers(response):
        """Add security headers to every response.
        WHY: defense-in-depth against XSS, clickjacking, MIME sniffing.
        """
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # CSP allows Leaflet tiles, Google Fonts, and inline styles for the chat UI
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
            "connect-src 'self' https://*.tile.openstreetmap.org"
        )
        response.headers['Content-Security-Policy'] = csp
        return response
    
    # --- Register Route Blueprints ---
    # WHY try/except: allows the app to start even if some routes aren't built yet
    route_modules = [
        ('backend.routes.auth', 'auth_bp'),
        ('backend.routes.assessments', 'assessments_bp'),
        ('backend.routes.doctors', 'doctors_bp'),
        ('backend.routes.consultations', 'consultations_bp'),
        ('backend.routes.notifications', 'notifications_bp'),
        ('backend.routes.health', 'health_bp'),
    ]
    
    for module_path, bp_name in route_modules:
        try:
            module = __import__(module_path, fromlist=[bp_name])
            blueprint = getattr(module, bp_name)
            app.register_blueprint(blueprint)
        except (ImportError, AttributeError) as e:
            print(f'  Note: Route {module_path} not yet available: {e}')
    
    # --- Frontend File Serving ---
    # WHY serve manually: single command runs everything, no separate static server
    
    @app.route('/')
    def serve_index():
        """Serve the landing page."""
        return send_from_directory(frontend_dir, 'index.html')
    
    @app.route('/sw.js')
    def serve_sw():
        """Service worker must be served from root for scope."""
        response = send_from_directory(frontend_dir, 'sw.js')
        response.headers['Service-Worker-Allowed'] = '/'
        return response
    
    @app.route('/manifest.json')
    def serve_manifest():
        return send_from_directory(frontend_dir, 'manifest.json')
    
    @app.route('/pages/<path:filename>')
    def serve_pages(filename):
        return send_from_directory(os.path.join(frontend_dir, 'pages'), filename)
    
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory(os.path.join(frontend_dir, 'css'), filename)
    
    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory(os.path.join(frontend_dir, 'js'), filename)
    
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(os.path.join(frontend_dir, 'assets'), filename)
    
    # --- CSRF Token Endpoint ---
    @app.route('/api/auth/csrf')
    def get_csrf():
        """Return the current CSRF token for JavaScript to use."""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return jsonify({'ok': True, 'data': {'csrf_token': session['csrf_token']}})
    
    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'ok': False, 'error': 'Not found'}), 404
        return send_from_directory(frontend_dir, 'index.html')
    
    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'ok': False, 'error': 'Internal server error'}), 500
        return '<h1>500 Internal Server Error</h1>', 500
    
    return app
