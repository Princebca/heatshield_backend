"""
HeatShield India - Flask REST API Server
Main application with all endpoints for the mobile app
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

from database import DatabaseManager
from data_fetcher import DataFetcher
from ml_model import RiskPredictionModel, SymptomAnalyzer

from config import config

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Android app

# Initialize components
db = DatabaseManager()
data_fetcher = DataFetcher()
risk_model = RiskPredictionModel()
symptom_analyzer = SymptomAnalyzer()

print("🛡️  HeatShield India API Server Initialized")
print(f"   Database: {config['DATABASE']['PATH']}")
print(f"   Mock Data: {'Enabled' if data_fetcher.use_mock else 'Disabled'}")
print(f"   ML Model: Ready")

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'HeatShield India API',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/user/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['phone', 'name', 'age', 'location', 'language']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        existing_user = db.get_user_by_phone(data['phone'])
        if existing_user:
            return jsonify({
                'message': 'User already registered',
                'user': existing_user
            }), 200
        
        # Create new user
        user = db.create_user(data)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile"""
    try:
        user = db.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user profile"""
    try:
        data = request.get_json()
        
        user = db.update_user(user_id, data)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENVIRONMENTAL DATA ENDPOINTS
# ============================================================================

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Get current weather data"""
    try:
        latitude = float(request.args.get('latitude', 22.2604))
        longitude = float(request.args.get('longitude', 84.8536))
        
        weather_data = data_fetcher.get_weather_data(latitude, longitude)
        
        return jsonify({
            'weather': weather_data,
            'success': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/aqi', methods=['GET'])
def get_aqi():
    """Get current air quality index data"""
    try:
        latitude = float(request.args.get('latitude', 22.2604))
        longitude = float(request.args.get('longitude', 84.8536))
        
        aqi_data = data_fetcher.get_aqi_data(latitude, longitude)
        
        return jsonify({
            'aqi_data': aqi_data,
            'success': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast', methods=['POST'])
def get_risk_forecast():
    """Get personalized health risk forecast"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Get user profile
        user = db.get_user(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get environmental data
        latitude = float(data.get('latitude', 22.2604))
        longitude = float(data.get('longitude', 84.8536))
        
        weather_data = data_fetcher.get_weather_data(latitude, longitude)
        aqi_data = data_fetcher.get_aqi_data(latitude, longitude)
        
        # Predict risk
        risk_prediction = risk_model.predict_risk(user, weather_data, aqi_data)
        
        return jsonify({
            'forecast': {
                'weather': weather_data,
                'aqi': aqi_data,
                'risk': risk_prediction
            },
            'success': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH TRACKING ENDPOINTS
# ============================================================================

@app.route('/api/symptoms', methods=['POST'])
def log_symptoms():
    """Log user symptoms"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'symptoms', 'severity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get user history for pattern detection
        user_history = db.get_user_symptoms(data['user_id'], limit=10)
        
        # Analyze symptoms
        analysis = symptom_analyzer.analyze_symptoms(
            data['symptoms'],
            data['severity'],
            user_history
        )
        
        # Save symptom log with AI analysis
        log_data = {
            'user_id': data['user_id'],
            'symptoms': data['symptoms'],
            'severity': data['severity'],
            'notes': data.get('notes', ''),
            'ai_analysis': analysis
        }
        
        symptom_log = db.create_symptom_log(log_data)
        
        return jsonify({
            'message': 'Symptoms logged successfully',
            'log': symptom_log,
            'analysis': analysis,
            'success': True
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/symptoms/<user_id>', methods=['GET'])
def get_symptom_history(user_id):
    """Get symptom history for a user"""
    try:
        limit = int(request.args.get('limit', 50))
        
        symptoms = db.get_user_symptoms(user_id, limit)
        
        return jsonify({
            'symptoms': symptoms,
            'count': len(symptoms),
            'success': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# COMMUNITY ENDPOINTS
# ============================================================================

@app.route('/api/community/posts', methods=['GET'])
def get_community_posts():
    """Get community posts"""
    try:
        limit = int(request.args.get('limit', 50))
        category = request.args.get('category', None)
        
        posts = db.get_posts(limit, category)
        
        # Add some sample posts if database is empty
        if len(posts) == 0:
            sample_posts = [
                {
                    'post_id': 'sample-1',
                    'user_id': 'system',
                    'author_name': 'HeatShield Team',
                    'content': 'Welcome to HeatShield India! Share your heat protection tips here.',
                    'category': 'general',
                    'likes': 25,
                    'created_at': datetime.utcnow().isoformat()
                },
                {
                    'post_id': 'sample-2',
                    'user_id': 'system',
                    'author_name': 'Health Expert',
                    'content': 'Remember: Drink water before you feel thirsty! Stay hydrated in this heat.',
                    'category': 'tips',
                    'likes': 42,
                    'created_at': datetime.utcnow().isoformat()
                }
            ]
            posts = sample_posts
        
        return jsonify({
            'posts': posts,
            'count': len(posts),
            'success': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/community/posts', methods=['POST'])
def create_community_post():
    """Create a new community post"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'author_name', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        post = db.create_post(data)
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post,
            'success': True
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/community/challenges', methods=['GET'])
def get_challenges():
    """Get active challenges"""
    try:
        challenges = db.get_active_challenges()
        
        # Add sample challenges if database is empty
        if len(challenges) == 0:
            sample_challenges = [
                {
                    'challenge_id': 'sample-1',
                    'title': '30-Day Hydration Challenge',
                    'description': 'Drink 3L+ water daily for 30 days',
                    'type': 'hydration',
                    'goal': 30,
                    'participants': 156,
                    'start_date': datetime.utcnow().isoformat(),
                    'end_date': None,
                    'is_active': True
                },
                {
                    'challenge_id': 'sample-2',
                    'title': 'Plant 10 Trees',
                    'description': 'Help cool your community by planting trees',
                    'type': 'tree_planting',
                    'goal': 10,
                    'participants': 89,
                    'start_date': datetime.utcnow().isoformat(),
                    'end_date': None,
                    'is_active': True
                }
            ]
            challenges = sample_challenges
        
        return jsonify({
            'challenges': challenges,
            'count': len(challenges),
            'success': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/community/challenges/<challenge_id>/join', methods=['POST'])
def join_challenge(challenge_id):
    """Join a challenge"""
    try:
        data = request.get_json()
        
        if 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Increment participant count
        challenge = db.increment_challenge_participants(challenge_id)
        
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        return jsonify({
            'message': 'Joined challenge successfully',
            'challenge': challenge,
            'success': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🛡️  HeatShield India API Server Starting...")
    print("="*60)
    print(f"Host: {config['SERVER']['HOST']}")
    print(f"Port: {config['SERVER']['PORT']}")
    print(f"Debug: {config['SERVER']['DEBUG']}")
    print("="*60)
    print("\n✓ Server ready for connections!\n")
    
    app.run(
        host=config['SERVER']['HOST'],
        port=config['SERVER']['PORT'],
        debug=config['SERVER']['DEBUG']
    )
