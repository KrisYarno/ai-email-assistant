"""
Flask application for the AI Email Response Assistant.
This script handles both serving the web interface and processing API requests.
Also includes template management functionality and basic authentication.
"""

# Import necessary libraries
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import os
import json
from dotenv import load_dotenv
from models import db, init_db, Template, Tag
from werkzeug.security import generate_password_hash, check_password_hash
import functools

# Import our direct API module
from direct_api import direct_openai_call

# Load environment variables from .env file (for local development)
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Set a secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-key-change-in-production')

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
init_db(app)

# Authentication credentials (in a real app, this would be in a database)
# The password is hashed for security
USERNAME = os.environ.get('APP_USERNAME', 'admin')
# Default password is 'peptideservice' - you should change this in your .env file
PASSWORD_HASH = generate_password_hash(os.environ.get('APP_PASSWORD', 'peptideservice'))

# System prompt for the AI (instructions on how to respond)
SYSTEM_PROMPT = """
You are a helpful customer service assistant for a peptide distribution company.
Our company sells lab-grade peptides strictly for research purposes. We are NOT medical professionals.
You MUST NOT provide any dosage information, medical advice, or suggestions for human/animal consumption or use. If asked directly about these topics, politely state that you cannot provide that type of information, and pivot to offering allowed information like product specifications (purity, sequence if available), storage guidelines, or order/shipping status if relevant to the query.
Your tone should be professional, helpful, and polite.
Do not explicitly state *why* you cannot provide medical advice (e.g., don't say 'Due to regulations...' or 'We cannot legally...'). Simply decline to provide the restricted information politely as described above.
Focus on answering the customer's query accurately within the allowed boundaries (e.g., product information, availability, purity, storage, order status, general research context where appropriate).
"""

# Get OpenAI API key from environment variables
openai_api_key = os.environ.get('OPENAI_API_KEY')

# Login required decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Route to serve the main HTML page - now protected
@app.route('/')
@login_required
def index():
    """Serve the main index.html page"""
    return render_template('index.html', username=session.get('username'))

# API endpoint to generate email responses - now protected
@app.route('/generate_response', methods=['POST'])
@login_required
def generate_response():
    """Handle POST requests to generate AI responses"""
    
    # Check if OpenAI API key is configured
    if not openai_api_key:
        return jsonify({"error": "OpenAI API key is not configured. Please check your environment variables."}), 500
    
    try:
        # Get JSON data from the request
        data = request.json
        
        # Extract data from the request
        customer_email = data.get('customer_email', '')
        previous_response = data.get('previous_response', '')  # Will be empty for initial request
        modification_request = data.get('modification_request', '')  # Will be empty for initial request
        template_id = data.get('template_id')  # Optional template ID
        
        # Validate customer email is provided
        if not customer_email:
            return jsonify({"error": "Customer email is required"}), 400
        
        # Initialize messages list with the system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Get template if provided
        template_content = ""
        if template_id:
            try:
                template = Template.query.get(template_id)
                if template:
                    template_content = template.content
            except Exception as e:
                print(f"Error retrieving template: {e}")
                # Continue without the template
        
        # Construct messages for the API call based on whether it's an initial request or a modification
        if not previous_response:
            # Initial request
            user_content = f"Customer Email:\n{customer_email}\n\n"
            
            # Add template if available
            if template_content:
                user_content += f"Please use the following template as a starting point for your response:\n\n---TEMPLATE START---\n{template_content}\n---TEMPLATE END---\n\n"
            
            user_content += "Draft a suitable response:"
            
            messages.append({
                "role": "user", 
                "content": user_content
            })
        else:
            # Modification request
            messages.extend([
                {"role": "user", "content": f"Original Customer Email:\n{customer_email}"},
                {"role": "assistant", "content": previous_response},
                {"role": "user", "content": f"Please modify the above response based on this request: {modification_request}"}
            ])
        
        # Use our direct API call function instead of the OpenAI client
        ai_response = direct_openai_call(
            api_key=openai_api_key,
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500
        )
        
        # Return the AI-generated response
        return jsonify({"response": ai_response})
    
    except Exception as e:
        # Handle errors and return appropriate error messages
        return jsonify({"error": f"Error generating response: {str(e)}"}), 500

# API endpoints for template management - now protected

@app.route('/api/templates', methods=['GET'])
@login_required
def get_templates():
    """Get all templates or search for templates"""
    search_term = request.args.get('search', '')
    tag_filter = request.args.get('tag', '')
    
    # Start with all templates
    query = Template.query
    
    # Apply search filter if provided
    if search_term:
        query = query.filter(
            # Search in title or content
            (Template.title.ilike(f'%{search_term}%') | 
             Template.content.ilike(f'%{search_term}%'))
        )
    
    # Apply tag filter if provided
    if tag_filter:
        tag = Tag.query.filter_by(name=tag_filter).first()
        if tag:
            query = query.filter(Template.tags.contains(tag))
    
    # Execute query and convert results to dictionaries
    templates = [template.to_dict() for template in query.all()]
    
    return jsonify(templates)

@app.route('/api/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """Get a specific template by ID"""
    template = Template.query.get_or_404(template_id)
    return jsonify(template.to_dict())

@app.route('/api/templates', methods=['POST'])
@login_required
def create_template():
    """Create a new template"""
    data = request.json
    
    # Validate required fields
    if not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content are required'}), 400
    
    # Create new template
    template = Template(
        title=data['title'],
        content=data['content']
    )
    
    # Process tags
    tag_names = data.get('tags', [])
    for tag_name in tag_names:
        # Find existing tag or create new one
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        template.tags.append(tag)
    
    # Save to database
    db.session.add(template)
    db.session.commit()
    
    return jsonify(template.to_dict()), 201

@app.route('/api/templates/<int:template_id>', methods=['PUT'])
@login_required
def update_template(template_id):
    """Update an existing template"""
    template = Template.query.get_or_404(template_id)
    data = request.json
    
    # Update fields if provided
    if 'title' in data:
        template.title = data['title']
    if 'content' in data:
        template.content = data['content']
    
    # Update tags if provided
    if 'tags' in data:
        # Remove all existing tags
        template.tags = []
        
        # Add new tags
        tag_names = data['tags']
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            template.tags.append(tag)
    
    # Save changes
    db.session.commit()
    
    return jsonify(template.to_dict())

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    """Delete a template"""
    template = Template.query.get_or_404(template_id)
    
    # Remove template from database
    db.session.delete(template)
    db.session.commit()
    
    return jsonify({'message': 'Template deleted successfully'})

@app.route('/api/tags', methods=['GET'])
@login_required
def get_tags():
    """Get all available tags"""
    tags = [tag.to_dict() for tag in Tag.query.all()]
    return jsonify(tags)

# Run the app if this file is executed directly
if __name__ == '__main__':
    # Use environment variable for port if available (for deployment), otherwise use 5000
    port = int(os.environ.get('PORT', 5000))
    # In development mode, set debug=True for auto-reloading when code changes
    app.run(host='0.0.0.0', port=port, debug=True)