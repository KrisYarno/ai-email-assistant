"""
Database models for the AI Email Response Assistant.
This file defines the SQLAlchemy models for templates and tags.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Association table for many-to-many relationship between templates and tags
template_tags = db.Table('template_tags',
    db.Column('template_id', db.Integer, db.ForeignKey('template.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Template(db.Model):
    """Model for email response templates"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with Tag model through association table
    tags = db.relationship('Tag', secondary=template_tags, 
                          backref=db.backref('templates', lazy='dynamic'))
    
    def to_dict(self):
        """Convert template to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': [tag.name for tag in self.tags]
        }

class Tag(db.Model):
    """Model for template tags"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    def to_dict(self):
        """Convert tag to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name
        }

def init_db(app):
    """Initialize the database with the app"""
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()