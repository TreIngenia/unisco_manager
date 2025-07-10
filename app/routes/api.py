from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app import db

def register_api_routes(api_bp):
    
    @api_bp.route('/users', methods=['GET'])
    @jwt_required()
    def get_users():
        current_user_uid = get_jwt_identity()
        current_user = User.query.get(current_user_uid)
        
        if not current_user or not current_user.is_active:
            return jsonify({'error': 'Utente non autorizzato'}), 401
        
        users = User.query.filter_by(is_active=True).all()
        return jsonify([user.to_dict() for user in users])

    @api_bp.route('/users/<int:user_uid>', methods=['GET'])
    @jwt_required()
    def get_user(user_uid):
        current_user_uid = get_jwt_identity()
        current_user = User.query.get(current_user_uid)
        
        if not current_user or not current_user.is_active:
            return jsonify({'error': 'Utente non autorizzato'}), 401
        
        user = User.query.get(user_uid)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        return jsonify(user.to_dict())

    @api_bp.route('/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        current_user_uid = get_jwt_identity()
        user = User.query.get(current_user_uid)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        return jsonify(user.to_dict())

    @api_bp.route('/profile', methods=['PUT'])
    @jwt_required()
    def update_profile():
        current_user_uid = get_jwt_identity()
        user = User.query.get(current_user_uid)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        data = request.get_json()
        
        if data.get('email'):
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.uid:
                return jsonify({'error': 'Email già in uso'}), 409
            user.email = data['email']
        
        if data.get('username'):
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.uid:
                return jsonify({'error': 'Username già in uso'}), 409
            user.username = data['username']
        
        db.session.commit()
        
        return jsonify(user.to_dict())