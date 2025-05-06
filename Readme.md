# AI Email Response Assistant

A web application that helps customer service teams draft consistent email responses for a peptide distribution company, with built-in guardrails to ensure compliance with company policies.

## Overview

This application allows customer service representatives to quickly generate professional email responses to customer inquiries while ensuring they adhere to important company constraints - particularly that the company sells lab-grade peptides strictly for research purposes and cannot provide medical advice or dosage information.

The tool uses OpenAI's API to generate contextually appropriate responses based on the customer's original email, with optional response templates as starting points. Users can also modify generated responses by providing simple instructions.

## Features

- **AI-Powered Email Drafting**: Generate professional email responses using OpenAI's API
- **Policy Compliance**: Built-in guardrails to ensure responses adhere to company policies about not providing medical advice
- **Response Templates**: Create, manage, and search reusable response templates with tagging capability
- **Template Categories**: Organize templates with tags for easy filtering and searching
- **Response Modifications**: Request changes to generated responses using simple natural language instructions
- **Authentication**: Basic username/password protection for internal company use
- **Clean, Simple Interface**: Easy-to-use web interface with a tabbed design

## Technology Stack

- **Backend**: Python with Flask framework
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Database**: SQLite with SQLAlchemy ORM
- **AI Integration**: OpenAI API (using direct API calls)
- **Authentication**: Flask session management with secure password hashing
- **Deployment**: Configured for deployment on Render

## Installation and Setup

### Prerequisites

- Python 3.x
- Git (optional, for version control)
- OpenAI API key

### Local Development Setup

1. **Clone the repository** (or download and extract the zip file):
   ```bash
   git clone https://github.com/KrisYarno/ai-email-assistant.git
   cd ai-email-assistant
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=a_secure_random_string_for_session_encryption
   APP_USERNAME=desired_username
   APP_PASSWORD=desired_password
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   Open your browser and go to http://127.0.0.1:5000/

## Usage Guide

### Authentication

1. Access the application through your browser
2. Enter the username and password configured in your `.env` file
3. After successful login, you'll be redirected to the main application

### Generating Email Responses

1. Navigate to the "Generate Response" tab (default)
2. (Optional) Select a template to use as a starting point
3. Paste the customer's email in the "Customer Email" field
4. Click "Generate Response"
5. Review the AI-generated response
6. (Optional) To modify the response, enter instructions in the "Modification request" field (e.g., "Make it shorter" or "Add details about shipping") and click "Modify Response"

### Managing Templates

1. Navigate to the "Manage Templates" tab
2. To create a new template:
   - Enter a title, content, and optional tags (comma-separated)
   - Click "Save Template"
3. To search templates:
   - Enter search terms or select a tag filter
   - Click "Search"
4. To edit or delete a template:
   - Click "Edit" or "Delete" in the templates list
   - For editing, make your changes and click "Save Template"

## Configuration Options

### OpenAI Model Selection

To change the OpenAI model used for generating responses, modify the model parameter in the `direct_openai_call` function in the `generate_response` route in `app.py`:

```python
ai_response = direct_openai_call(
    api_key=openai_api_key,
    messages=messages,
    model="gpt-4o-mini",  # Change to your preferred model
    temperature=0.7,
    max_tokens=500
)
```


### System Prompt Customization

The system prompt defines how the AI assistant should behave. You can modify it in the `app.py` file:

```python
SYSTEM_PROMPT = """
You are a helpful customer service assistant for [provide instructions].
...
"""
```

Adjust the content to reflect your company's specific policies and tone.

## Deployment to Render

1. **Create a GitHub repository** and push your code
2. **Sign up for Render** at render.com
3. **Create a new Web Service**:
   - Connect to your GitHub repository
   - Configure as a Python application
   - Set build command to `pip install -r requirements.txt`
   - Set start command to `gunicorn app:app`
4. **Add environment variables** in the Render dashboard:
   - OPENAI_API_KEY
   - SECRET_KEY
   - APP_USERNAME
   - APP_PASSWORD
5. **Deploy** the application

## Project Structure

```
email-assistant/
│
├── app.py                 # Main Flask application
├── models.py              # Database models
├── direct_api.py          # Direct OpenAI API integration
├── requirements.txt       # Python dependencies
├── Procfile               # For Render deployment
├── .env                   # Environment variables (not committed)
├── .gitignore             # Git ignore file
│
├── static/                # Static files
│   ├── style.css          # CSS styles
│   └── script.js          # Frontend JavaScript
│
└── templates/             # HTML templates
    ├── index.html         # Main application page
    └── login.html         # Login page
```

## Future Enhancements

Potential improvements for future development:

1. **Individual User Accounts**: Replace shared login with individual user management
2. **Response Analytics**: Track which responses and templates perform best
3. **Email Integration**: Direct integration with email systems
4. **Export/Import Templates**: Allow backup and sharing of template libraries
5. **Advanced Template Categories**: Hierarchical organization of templates
6. **Audit Logging**: Track all generated responses and modifications
7. **Response Rating System**: Allow users to rate AI responses for continuous improvement

## Troubleshooting

### Common Issues

**OpenAI API Connection Issues**
- Check that your API key is valid and properly set in the .env file
- Verify you have billing set up with OpenAI

**Database Issues**
- If templates aren't saving, check that the application has write permissions for the SQLite database file

**Authentication Problems**
- If you forget the login credentials, you can update them in your .env file

### Proxy-related Errors

If you encounter errors related to proxies when initializing the OpenAI client, the application is designed to use direct API calls instead of the OpenAI client library, which should bypass these issues.

## License

This project is intended for internal company use only.

## Support

For issues or questions, please contact the development team or create an issue in the GitHub repository.