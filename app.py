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
import re

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

IMPORTANT FORMATTING INSTRUCTION: Do not use em dash characters (—) in your response. Use hyphens (-) sparingly or other appropriate punctuation instead.
"""

REFINING_PROMPT = """
You are a customer service language expert for a peptide distribution company.
Your task is to reword technical responses to make them more customer-friendly while preserving the technical accuracy.
Keep the same information but make the tone warmer, more approachable, and easier to understand.
Maintain all the technical information and policies mentioned in the original response.
Remember that we sell lab-grade peptides strictly for research purposes and are NOT medical professionals.
We cannot provide dosage information, medical advice, or suggestions for human/animal consumption or use.

IMPORTANT: Provide ONLY the final reworded response with no introductory text like "Here's a reworded version" or "Certainly!"
Do not include any meta-commentary or prefatory remarks. Start directly with the customer service response.

IMPORTANT FORMATTING INSTRUCTION: Do not use em dash characters (—) in your response. Use hyphens (-) sparingly or other appropriate punctuation instead.
"""

# Get OpenAI API key from environment variables
openai_api_key = os.environ.get('OPENAI_API_KEY')

# Helper function to clean up responses
def clean_response(response):
    """Clean up the response by removing common prefatory text and em dashes"""
    # List of common prefatory patterns to remove
    prefatory_patterns = [
        r"^Certainly!.*?\n\n",
        r"^Sure!.*?\n\n",
        r"^Here's.*?(\n\n|\n---\n)",
        r"^I've.*?\n\n",
        r"^Here is.*?\n\n",
        r"^Below is.*?\n\n",
        r"^The following.*?\n\n"
    ]
    
    # Apply all patterns
    for pattern in prefatory_patterns:
        response = re.sub(pattern, "", response, flags=re.DOTALL)
    
    # Remove any "---" dividers at the beginning
    response = re.sub(r"^---\n", "", response)
    
    # Replace em dashes with regular hyphens or en dashes
    response = response.replace("—", "-")  # Replace em dash with hyphen
    response = response.replace("–", "-")  # Replace en dash with hyphen too
    
    return response.strip()

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
    """Handle POST requests to generate AI responses with model selection"""
    
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
        customer_notes = data.get('customer_notes', '')  # Get the customer notes
        
        # Get model selection and token limit
        model = data.get('model', 'gpt-4.1')  # Default to gpt-4.1 if not specified
        token_limit = int(data.get('token_limit', 1000))  # Default to 1000 if not specified
        
        # Log the received parameters
        print(f"Received request with model: {model}, token_limit: {token_limit}")
        
        # Check if technical hybrid mode is selected
        is_technical_mode = model == 'technical'
        
        # If technical mode, we'll use o4-mini first, then gpt-4.1
        if is_technical_mode:
            technical_first_model = 'o4-mini'  # Use correct model name without gpt- prefix
            technical_second_model = 'gpt-4.1'
            # Ensure higher token limit for technical mode
            token_limit = max(token_limit, 2000)
            print(f"Technical mode enabled. Using models: {technical_first_model} -> {technical_second_model}")
        
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

            if customer_notes:
                user_content += f"IMPORTANT NOTES: {customer_notes}\n\n"
            
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
                {"role": "user", "content": f"Original Important Notes:\n{customer_notes}"},
                {"role": "user", "content": f"Please modify the above response based on this request: {modification_request}"}
            ])
        
        # Generate the response
        if is_technical_mode:
            # Technical hybrid mode: first generate with o4-mini
            print(f"Step 1: Generating with {technical_first_model}")
            first_response = direct_openai_call(
                api_key=openai_api_key,
                messages=messages,
                model=technical_first_model,
                max_tokens=token_limit // 2  # Use half the tokens for the first step
            )
            
            print(f"Initial technical response length: {len(first_response)}")
            print(f"Initial response starts with: {first_response[:100]}...")
            
            # Then refine with gpt-4.1 for better customer service language
            print(f"Step 2: Refining with {technical_second_model}")
            refining_messages = [
                {"role": "system", "content": REFINING_PROMPT},
                {"role": "user", "content": f"Here is a technical response to a customer email:\n\n{first_response}\n\nReword this to be more customer-friendly while maintaining all the technical information. Start directly with the reworded response without any introduction or prefatory text."}
            ]
            
            ai_response = direct_openai_call(
                api_key=openai_api_key,
                messages=refining_messages,
                model=technical_second_model,
                max_tokens=token_limit // 2  # Use the remaining tokens for refinement
            )
        else:
            # Standard mode: use the selected model directly
            print(f"Using model: {model} with token limit: {token_limit}")
            ai_response = direct_openai_call(
                api_key=openai_api_key,
                messages=messages,
                model=model,
                max_tokens=token_limit
            )
        
        # Clean up the response to remove any prefatory text
        original_length = len(ai_response)
        ai_response = clean_response(ai_response)
        print(f"Response cleanup: {original_length} chars -> {len(ai_response)} chars")
        print(f"Final response starts with: {ai_response[:100]}...")
        
        # Return the AI-generated response
        return jsonify({"response": ai_response})
    
    except Exception as e:
        # Handle errors and return appropriate error messages
        print(f"Error generating response: {str(e)}")
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