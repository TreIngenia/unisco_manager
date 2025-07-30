from flask import render_template, request, jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    """Registra tutti i gestori di errore"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Gestisce errori 404 - Pagina non trovata"""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'response': 'pagina_non_trovata',
                'title': 'Risorsa non trovata',
                'message': 'La risorsa richiesta non è stata trovata.'
            }), 404
        
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Gestisce errori 403 - Accesso negato"""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'response': 'accesso_negato',
                'title': 'Accesso negato',
                'message': 'Non hai i permessi per accedere a questa risorsa.'
            }), 403
        
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """Gestisce errori 500 - Errore interno del server"""
        # Log dell'errore (puoi aggiungere logging qui)
        print(f"❌ Errore 500: {error}")
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'response': 'errore_server',
                'title': 'Errore del server',
                'message': 'Si è verificato un errore interno del server.'
            }), 500
        
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Gestisce errori 400 - Richiesta non valida"""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'response': 'richiesta_non_valida',
                'title': 'Richiesta non valida',
                'message': 'La richiesta inviata non è valida.'
            }), 400
        
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Gestisce errori 401 - Non autorizzato"""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'response': 'non_autorizzato',
                'title': 'Accesso richiesto',
                'message': 'Devi effettuare l\'accesso per continuare.'
            }), 401
        
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Gestisce errori 405 - Metodo non consentito"""
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'response': 'metodo_non_consentito',
                'title': 'Metodo non consentito',
                'message': 'Il metodo HTTP utilizzato non è consentito per questa risorsa.'
            }), 405
        
        return render_template('errors/405.html'), 405
    
    @app.errorhandler(Exception)
    def generic_error(error):
        """Gestisce tutti gli altri errori generici"""
        # Log dell'errore
        print(f"❌ Errore generico: {error}")
        
        # Se è un HTTPException, usa il suo status code
        if isinstance(error, HTTPException):
            status_code = error.code
        else:
            status_code = 500
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'response': 'errore_generico',
                'title': 'Errore',
                'message': 'Si è verificato un errore inaspettato.'
            }), status_code
        
        return render_template('errors/generic.html', error=error), status_code