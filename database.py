"""
Database models and manager for HeatShield India backend
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

Base = declarative_base()

from config import config

class User(Base):
    """User profile model"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(15), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    location = Column(String(200))
    language = Column(String(20), default='English')
    occupation = Column(String(100))
    outdoor_hours = Column(Float, default=4.0)  # Average hours spent outdoors daily
    health_conditions = Column(JSON, default=list)  # List of health conditions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'user_id': self.id,
            'phone': self.phone,
            'name': self.name,
            'age': self.age,
            'location': self.location,
            'language': self.language,
            'occupation': self.occupation,
            'outdoor_hours': self.outdoor_hours,
            'health_conditions': self.health_conditions or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SymptomLog(Base):
    """Symptom tracking model"""
    __tablename__ = 'symptom_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    symptoms = Column(JSON, nullable=False)  # List of symptom names
    severity = Column(Integer, nullable=False)  # 1-10 scale
    notes = Column(Text)
    ai_analysis = Column(JSON)  # AI-generated analysis and alerts
    logged_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'log_id': self.id,
            'user_id': self.user_id,
            'symptoms': self.symptoms or [],
            'severity': self.severity,
            'notes': self.notes,
            'ai_analysis': self.ai_analysis,
            'logged_at': self.logged_at.isoformat() if self.logged_at else None
        }

class CommunityPost(Base):
    """Community forum post model"""
    __tablename__ = 'community_posts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    author_name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default='general')  # general, tips, alert, success
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'post_id': self.id,
            'user_id': self.user_id,
            'author_name': self.author_name,
            'content': self.content,
            'category': self.category,
            'likes': self.likes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Challenge(Base):
    """Health challenge model"""
    __tablename__ = 'challenges'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    challenge_type = Column(String(50))  # hydration, tree_planting, awareness
    goal = Column(Integer)  # Target quantity
    participants = Column(Integer, default=0)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            'challenge_id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.challenge_type,
            'goal': self.goal,
            'participants': self.participants,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active
        }

class DatabaseManager:
    """Database connection and operations manager"""
    
    def __init__(self):
        db_config = config['DATABASE']
        if db_config['TYPE'] == 'sqlite':
            db_url = f"sqlite:///{db_config['PATH']}"
        else:
            # For PostgreSQL or other databases
            db_url = db_config.get('URL', f"sqlite:///{db_config['PATH']}")
        
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    # User operations
    def create_user(self, user_data):
        """Create a new user"""
        user = User(**user_data)
        self.session.add(user)
        self.session.commit()
        return user.to_dict()
    
    def get_user(self, user_id):
        """Get user by ID"""
        user = self.session.query(User).filter_by(id=user_id).first()
        return user.to_dict() if user else None
    
    def get_user_by_phone(self, phone):
        """Get user by phone number"""
        user = self.session.query(User).filter_by(phone=phone).first()
        return user.to_dict() if user else None
    
    def update_user(self, user_id, update_data):
        """Update user profile"""
        user = self.session.query(User).filter_by(id=user_id).first()
        if user:
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.session.commit()
            return user.to_dict()
        return None
    
    # Symptom log operations
    def create_symptom_log(self, log_data):
        """Create a symptom log entry"""
        symptom_log = SymptomLog(**log_data)
        self.session.add(symptom_log)
        self.session.commit()
        return symptom_log.to_dict()
    
    def get_user_symptoms(self, user_id, limit=50):
        """Get symptom history for a user"""
        logs = self.session.query(SymptomLog)\
            .filter_by(user_id=user_id)\
            .order_by(SymptomLog.logged_at.desc())\
            .limit(limit)\
            .all()
        return [log.to_dict() for log in logs]
    
    # Community operations
    def create_post(self, post_data):
        """Create a community post"""
        post = CommunityPost(**post_data)
        self.session.add(post)
        self.session.commit()
        return post.to_dict()
    
    def get_posts(self, limit=50, category=None):
        """Get community posts"""
        query = self.session.query(CommunityPost)
        if category:
            query = query.filter_by(category=category)
        posts = query.order_by(CommunityPost.created_at.desc()).limit(limit).all()
        return [post.to_dict() for post in posts]
    
    # Challenge operations
    def create_challenge(self, challenge_data):
        """Create a new challenge"""
        challenge = Challenge(**challenge_data)
        self.session.add(challenge)
        self.session.commit()
        return challenge.to_dict()
    
    def get_active_challenges(self):
        """Get all active challenges"""
        challenges = self.session.query(Challenge)\
            .filter_by(is_active=True)\
            .order_by(Challenge.start_date.desc())\
            .all()
        return [challenge.to_dict() for challenge in challenges]
    
    def increment_challenge_participants(self, challenge_id):
        """Increment participant count for a challenge"""
        challenge = self.session.query(Challenge).filter_by(id=challenge_id).first()
        if challenge:
            challenge.participants += 1
            self.session.commit()
            return challenge.to_dict()
        return None
    
    def close(self):
        """Close database connection"""
        self.session.close()

# Initialize database on module import
if __name__ == '__main__':
    print("Initializing HeatShield India database...")
    db = DatabaseManager()
    print("[OK] Database initialized successfully!")
    print(f"[OK] Database file: {config['DATABASE']['PATH']}")
    db.close()
