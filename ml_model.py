"""
Machine Learning model for health risk prediction
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

from config import config

class RiskPredictionModel:
    """ML model for predicting health risks from environmental data"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'temperature', 'heat_index', 'humidity', 'uv_index',
            'aqi', 'pm2_5', 'age', 'outdoor_hours', 'has_health_conditions'
        ]
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize or load the ML model"""
        model_path = config['ML_MODEL'].get('MODEL_PATH', 'models/risk_model.pkl')
        
        if os.path.exists(model_path) and config['ML_MODEL']['USE_PRETRAINED']:
            try:
                self.model, self.scaler = joblib.load(model_path)
                print(f"✓ Loaded pretrained model from {model_path}")
            except:
                print("⚠ Could not load pretrained model, training new one...")
                self._train_model()
        else:
            self._train_model()
    
    def _train_model(self):
        """Train the model with synthetic data"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        # Features: temp, heat_index, humidity, uv, aqi, pm2.5, age, outdoor_hours, health_conditions
        X_train = np.random.rand(n_samples, 9)
        
        # Scale features to realistic ranges
        X_train[:, 0] = X_train[:, 0] * 25 + 20  # Temperature: 20-45°C
        X_train[:, 1] = X_train[:, 1] * 30 + 25  # Heat index: 25-55°C
        X_train[:, 2] = X_train[:, 2] * 60 + 20  # Humidity: 20-80%
        X_train[:, 3] = X_train[:, 3] * 11       # UV index: 0-11
        X_train[:, 4] = X_train[:, 4] * 400      # AQI: 0-400
        X_train[:, 5] = X_train[:, 5] * 200      # PM2.5: 0-200
        X_train[:, 6] = X_train[:, 6] * 60 + 18  # Age: 18-78
        X_train[:, 7] = X_train[:, 7] * 12       # Outdoor hours: 0-12
        X_train[:, 8] = np.random.randint(0, 2, n_samples)  # Health conditions: 0 or 1
        
        # Generate risk labels (0-10) based on conditions
        y_train = np.zeros(n_samples)
        for i in range(n_samples):
            risk = 0
            
            # Temperature contribution
            if X_train[i, 0] > 40:
                risk += 3
            elif X_train[i, 0] > 35:
                risk += 2
            elif X_train[i, 0] > 32:
                risk += 1
            
            # AQI contribution
            if X_train[i, 4] > 300:
                risk += 3
            elif X_train[i, 4] > 200:
                risk += 2
            elif X_train[i, 4] > 100:
                risk += 1
            
            # UV index contribution
            if X_train[i, 3] > 8:
                risk += 1
            
            # Age and health conditions
            if X_train[i, 6] > 60 or X_train[i, 8] == 1:
                risk += 1
            
            # Outdoor hours
            if X_train[i, 7] > 6:
                risk += 1
            
            y_train[i] = min(10, risk + np.random.randint(-1, 2))
        
        # Train Random Forest
        self.scaler.fit(X_train)
        X_scaled = self.scaler.transform(X_train)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_scaled, y_train)
        
        # Save the model
        model_dir = os.path.dirname(config['ML_MODEL']['MODEL_PATH'])
        if model_dir and not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        try:
            joblib.dump((self.model, self.scaler), config['ML_MODEL']['MODEL_PATH'])
            print(f"✓ Model trained and saved to {config['ML_MODEL']['MODEL_PATH']}")
        except Exception as e:
            print(f"⚠ Could not save model: {e}")
    
    def predict_risk(self, user_profile, weather_data, aqi_data):
        """
        Predict health risk score for a user
        
        Args:
            user_profile: User data (age, health_conditions, outdoor_hours)
            weather_data: Weather data (temperature, heat_index, humidity, uv_index)
            aqi_data: Air quality data (aqi, pm2_5)
        
        Returns:
            dict with risk_score, severity_level, recommendations
        """
        # Extract features
        features = [
            weather_data['temperature'],
            weather_data['heat_index'],
            weather_data['humidity'],
            weather_data['uv_index'],
            aqi_data['aqi'],
            aqi_data['pm2_5'],
            user_profile.get('age', 30),
            user_profile.get('outdoor_hours', 4),
            1 if user_profile.get('health_conditions') else 0
        ]
        
        # Predict
        X = np.array([features])
        X_scaled = self.scaler.transform(X)
        risk_score = self.model.predict(X_scaled)[0]
        
        # Get severity level
        severity = self._get_severity_level(risk_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_score, user_profile, weather_data, aqi_data
        )
        
        return {
            'risk_score': float(risk_score),
            'severity_level': severity,
            'recommendations': recommendations,
            'timestamp': weather_data['timestamp']
        }
    
    def _get_severity_level(self, risk_score):
        """Convert risk score to severity level"""
        if risk_score <= 2:
            return 'Low'
        elif risk_score <= 5:
            return 'Moderate'
        elif risk_score <= 7:
            return 'High'
        else:
            return 'Very High'
    
    def _generate_recommendations(self, risk_score, user_profile, weather_data, aqi_data):
        """Generate personalized health recommendations"""
        recommendations = []
        
        # Temperature-based recommendations
        temp = weather_data['temperature']
        if temp > 40:
            recommendations.append({
                'category': 'heat',
                'priority': 'high',
                'message': '🌡️ Extreme heat! Stay indoors during 11 AM - 4 PM',
                'action': 'Avoid outdoor activities'
            })
        elif temp > 35:
            recommendations.append({
                'category': 'heat',
                'priority': 'medium',
                'message': '☀️ Very hot weather. Limit outdoor exposure',
                'action': 'Stay in shade, wear light clothing'
            })
        
        # Hydration recommendations
        if temp > 32 or risk_score > 3:
            daily_water = 3.5 + (risk_score * 0.3)  # Liters
            recommendations.append({
                'category': 'hydration',
                'priority': 'high',
                'message': f'💧 Drink at least {daily_water:.1f}L water today',
                'action': f'Drink water every {int(12/daily_water)} hours'
            })
        
        # AQI-based recommendations
        aqi = aqi_data['aqi']
        if aqi > 200:
            recommendations.append({
                'category': 'air_quality',
                'priority': 'high',
                'message': '😷 Poor air quality! Wear N95 mask outdoors',
                'action': 'Use air purifier indoors, close windows'
            })
        elif aqi > 100:
            recommendations.append({
                'category': 'air_quality',
                'priority': 'medium',
                'message': '😷 Moderate pollution. Consider wearing mask',
                'action': 'Reduce outdoor exercise'
            })
        
        # UV protection
        if weather_data['uv_index'] > 7:
            recommendations.append({
                'category': 'uv_protection',
                'priority': 'medium',
                'message': '🕶️ High UV levels. Protect your skin',
                'action': 'Use sunscreen SPF 30+, wear sunglasses'
            })
        
        # Health condition specific
        if user_profile.get('health_conditions'):
            recommendations.append({
                'category': 'health',
                'priority': 'high',
                'message': '⚕️ Extra caution due to health conditions',
                'action': 'Monitor symptoms closely, stay cool'
            })
        
        # Age-specific for elderly
        if user_profile.get('age', 0) > 60:
            recommendations.append({
                'category': 'health',
                'priority': 'high',
                'message': '👴 Take extra care in extreme conditions',
                'action': 'Stay indoors, keep emergency contacts ready'
            })
        
        # General recommendations based on risk
        if risk_score > 7:
            recommendations.append({
                'category': 'general',
                'priority': 'critical',
                'message': '⚠️ VERY HIGH RISK! Minimize all outdoor activities',
                'action': 'Stay indoors, seek medical help if feeling unwell'
            })
        
        return recommendations

class SymptomAnalyzer:
    """Analyze symptom logs for health alerts"""
    
    SEVERE_SYMPTOMS = [
        'chest_pain', 'severe_headache', 'difficulty_breathing',
        'confusion', 'loss_of_consciousness', 'severe_nausea'
    ]
    
    def analyze_symptoms(self, symptoms, severity, user_history=None):
        """
        Analyze symptoms and generate alerts
        
        Args:
            symptoms: List of symptom names
            severity: Severity score (1-10)
            user_history: Optional list of previous symptom logs
        
        Returns:
            dict with analysis, alerts, and recommendations
        """
        alerts = []
        is_urgent = False
        
        # Check for severe symptoms
        severe_found = [s for s in symptoms if s in self.SEVERE_SYMPTOMS]
        if severe_found:
            is_urgent = True
            alerts.append({
                'level': 'critical',
                'message': f'🚨 URGENT: {", ".join(severe_found)} detected',
                'action': 'Seek immediate medical attention'
            })
        
        # High severity alert
        if severity >= 8:
            is_urgent = True
            alerts.append({
                'level': 'high',
                'message': '⚠️ High severity symptoms reported',
                'action': 'Contact doctor or visit hospital'
            })
        elif severity >= 6:
            alerts.append({
                'level': 'medium',
                'message': '⚠️ Moderate symptoms detected',
                'action': 'Rest and monitor. Consult doctor if worsens'
            })
        
        # Pattern detection in history
        if user_history and len(user_history) >= 3:
            recent_severities = [log.get('severity', 0) for log in user_history[:3]]
            if all(s >= 5 for s in recent_severities):
                alerts.append({
                    'level': 'high',
                    'message': '📊 Persistent symptoms detected',
                    'action': 'Schedule medical checkup'
                })
        
        # Recommendations
        recommendations = self._get_symptom_recommendations(symptoms, severity)
        
        return {
            'is_urgent': is_urgent,
            'alerts': alerts,
            'recommendations': recommendations,
            'analysis_timestamp': None
        }
    
    def _get_symptom_recommendations(self, symptoms, severity):
        """Generate recommendations based on symptoms"""
        recommendations = []
        
        if 'headache' in symptoms:
            recommendations.append('Rest in cool, dark room. Stay hydrated')
        
        if 'fatigue' in symptoms or 'dizziness' in symptoms:
            recommendations.append('Drink water and electrolyte solution. Avoid exertion')
        
        if 'breathing_difficulty' in symptoms:
            recommendations.append('Stay in air-conditioned space. Avoid polluted areas')
        
        if 'nausea' in symptoms:
            recommendations.append('Sip water slowly. Eat light foods. Rest')
        
        if severity >= 5:
            recommendations.append('Monitor temperature. Take rest. Stay cool')
        
        return recommendations

# Test the model
if __name__ == '__main__':
    print("Testing Risk Prediction Model...")
    
    model = RiskPredictionModel()
    
    # Test prediction
    user = {'age': 35, 'outdoor_hours': 6, 'health_conditions': ['asthma']}
    weather = {
        'temperature': 42,
        'heat_index': 48,
        'humidity': 70,
        'uv_index': 9,
        'timestamp': '2024-01-01T12:00:00'
    }
    aqi = {'aqi': 220, 'pm2_5': 95}
    
    result = model.predict_risk(user, weather, aqi)
    print(f"\nRisk Score: {result['risk_score']}")
    print(f"Severity: {result['severity_level']}")
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  [{rec['priority']}] {rec['message']}")
    
    # Test symptom analyzer
    print("\n\nTesting Symptom Analyzer...")
    analyzer = SymptomAnalyzer()
    analysis = analyzer.analyze_symptoms(
        ['headache', 'fatigue', 'dizziness'],
        severity=7
    )
    print(f"Urgent: {analysis['is_urgent']}")
    print("Alerts:")
    for alert in analysis['alerts']:
        print(f"  [{alert['level']}] {alert['message']}")
