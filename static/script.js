/**
 * Frontend JavaScript for the AI Email Response Assistant
 * This script handles user interactions, API requests, and template management
 */

// Wait for the DOM to be fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', function() {
    // ========== ELEMENT REFERENCES ==========
    
    // Email generation elements
    const customerEmailInput = document.getElementById('customerEmail');
    const aiResponseOutput = document.getElementById('aiResponse');
    const modificationRequestInput = document.getElementById('modificationRequest');
    const generateButton = document.getElementById('generateBtn');
    const modifyButton = document.getElementById('modifyBtn');
    const statusElement = document.getElementById('status');
    
    // Template selection elements
    const templateSelector = document.getElementById('templateSelector');
    const templateSearchInput = document.getElementById('templateSearchInput');
    const tagFilter = document.getElementById('tagFilter');
    const searchTemplatesBtn = document.getElementById('searchTemplatesBtn');
    const templatePreview = document.getElementById('templatePreview');
    
    // Template management elements
    const templateIdInput = document.getElementById('templateId');
    const templateTitleInput = document.getElementById('templateTitle');
    const templateContentInput = document.getElementById('templateContent');
    const templateTagsInput = document.getElementById('templateTags');
    const saveTemplateBtn = document.getElementById('saveTemplateBtn');
    const clearTemplateBtn = document.getElementById('clearTemplateBtn');
    const templateStatus = document.getElementById('templateStatus');
    
    // Template list elements
    const templatesTable = document.getElementById('templatesTable').getElementsByTagName('tbody')[0];
    const templateListSearch = document.getElementById('templateListSearch');
    const templateListTagFilter = document.getElementById('templateListTagFilter');
    const searchTemplateListBtn = document.getElementById('searchTemplateListBtn');
    
    // Tab navigation elements
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // ========== TAB NAVIGATION ==========
    
    // Add click event listeners to tab buttons
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Show corresponding content
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            // Load data for the active tab
            if (tabId === 'templates-tab') {
                loadAllTags();
                loadTemplates();
            } else if (tabId === 'response-tab') {
                loadAllTags(tagFilter);
                loadTemplatesForSelector();
            }
        });
    });
    
    // ========== EMAIL GENERATION FUNCTIONS ==========
    
    // Function to handle the initial generation of an AI response
    function handleGenerateResponse() {
        // Get the customer email text
        const customerEmail = customerEmailInput.value.trim();
        
        // Validate that the customer email field is not empty
        if (!customerEmail) {
            setStatus('Please paste the customer email first.', 'status-error');
            return;
        }
        
        // Show loading status and disable buttons
        setStatus('Generating response...', 'status-loading');
        setButtonsEnabled(false);
        
        // Get selected template id (if any)
        const selectedTemplateId = templateSelector.value !== '' ? templateSelector.value : null;
        
        // Create the data object to send to the server
        const data = {
            customer_email: customerEmail,
            template_id: selectedTemplateId
        };
        
        // Send the API request
        fetch('/generate_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            // First check if the response is OK (status 200-299)
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || 'Unknown error occurred');
                });
            }
            // If response is OK, parse the JSON
            return response.json();
        })
        .then(data => {
            // Display the generated response
            aiResponseOutput.value = data.response;
            setStatus('Response generated successfully!', 'status-success');
        })
        .catch(error => {
            // Handle any errors that occurred during the fetch
            console.error('Error:', error);
            setStatus(`Error: ${error.message}`, 'status-error');
        })
        .finally(() => {
            // Re-enable buttons whether the request succeeded or failed
            setButtonsEnabled(true);
        });
    }

    // Function to handle modification of an existing AI response
    function handleModifyResponse() {
        // Get the values from all relevant fields
        const customerEmail = customerEmailInput.value.trim();
        const previousResponse = aiResponseOutput.value.trim();
        const modificationRequest = modificationRequestInput.value.trim();
        
        // Validate all required fields
        if (!customerEmail) {
            setStatus('Please paste the customer email first.', 'status-error');
            return;
        }
        
        if (!previousResponse) {
            setStatus('No response to modify. Please generate a response first.', 'status-error');
            return;
        }
        
        if (!modificationRequest) {
            setStatus('Please enter a modification request.', 'status-error');
            return;
        }
        
        // Show loading status and disable buttons
        setStatus('Modifying response...', 'status-loading');
        setButtonsEnabled(false);
        
        // Create the data object to send to the server
        const data = {
            customer_email: customerEmail,
            previous_response: previousResponse,
            modification_request: modificationRequest
        };
        
        // Send the API request
        fetch('/generate_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            // Check if the response is OK
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || 'Unknown error occurred');
                });
            }
            return response.json();
        })
        .then(data => {
            // Display the modified response
            aiResponseOutput.value = data.response;
            // Clear the modification request input
            modificationRequestInput.value = '';
            setStatus('Response modified successfully!', 'status-success');
        })
        .catch(error => {
            // Handle any errors
            console.error('Error:', error);
            setStatus(`Error: ${error.message}`, 'status-error');
        })
        .finally(() => {
            // Re-enable buttons
            setButtonsEnabled(true);
        });
    }
    
    // ========== TEMPLATE SELECTOR FUNCTIONS ==========
    
    // Function to load templates for the selector dropdown
    function loadTemplatesForSelector() {
        // Clear existing options except the first one (no template)
        while (templateSelector.options.length > 1) {
            templateSelector.remove(1);
        }
        
        // Get search term and tag filter if any
        const searchTerm = templateSearchInput.value.trim();
        const tagFilterValue = tagFilter.value;
        
        // Construct query string
        let url = '/api/templates';
        const queryParams = [];
        
        if (searchTerm) {
            queryParams.push(`search=${encodeURIComponent(searchTerm)}`);
        }
        
        if (tagFilterValue) {
            queryParams.push(`tag=${encodeURIComponent(tagFilterValue)}`);
        }
        
        if (queryParams.length > 0) {
            url += '?' + queryParams.join('&');
        }
        
        // Fetch templates from the server
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load templates');
                }
                return response.json();
            })
            .then(templates => {
                // Add each template as an option in the selector
                templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.title;
                    templateSelector.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading templates:', error);
                setStatus('Failed to load templates', 'status-error');
            });
    }
    
    // Function to preview the selected template
    function previewTemplate() {
        const selectedTemplateId = templateSelector.value;
        
        // If no template is selected, show the "no preview" message
        if (!selectedTemplateId) {
            templatePreview.innerHTML = '<p class="no-preview">Select a template to see preview</p>';
            return;
        }
        
        // Fetch the selected template
        fetch(`/api/templates/${selectedTemplateId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load template preview');
                }
                return response.json();
            })
            .then(template => {
                // Display the template content
                templatePreview.textContent = template.content;
            })
            .catch(error => {
                console.error('Error loading template preview:', error);
                templatePreview.innerHTML = '<p class="no-preview">Error loading preview</p>';
            });
    }
    
    // ========== TEMPLATE MANAGEMENT FUNCTIONS ==========
    
    // Function to save a template (create or update)
    function saveTemplate() {
        // Get form values
        const templateId = templateIdInput.value.trim();
        const title = templateTitleInput.value.trim();
        const content = templateContentInput.value.trim();
        const tagsString = templateTagsInput.value.trim();
        
        // Validate required fields
        if (!title) {
            setTemplateStatus('Title is required', 'status-error');
            return;
        }
        
        if (!content) {
            setTemplateStatus('Content is required', 'status-error');
            return;
        }
        
        // Parse tags
        const tags = tagsString ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        // Create data object
        const data = {
            title,
            content,
            tags
        };
        
        // Determine if creating or updating
        const method = templateId ? 'PUT' : 'POST';
        const url = templateId ? `/api/templates/${templateId}` : '/api/templates';
        
        // Show loading status
        setTemplateStatus('Saving template...', 'status-loading');
        
        // Send API request
        fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || 'Failed to save template');
                });
            }
            return response.json();
        })
        .then(template => {
            // Show success message
            setTemplateStatus(`Template "${template.title}" saved successfully`, 'status-success');
            
            // Clear the form
            clearTemplateForm();
            
            // Reload the templates list
            loadTemplates();
            
            // Also reload templates in the selector
            loadTemplatesForSelector();
        })
        .catch(error => {
            console.error('Error saving template:', error);
            setTemplateStatus(`Error: ${error.message}`, 'status-error');
        });
    }
    
    // Function to load all templates for the management table
    function loadTemplates() {
        // Clear existing table rows
        templatesTable.innerHTML = '';
        
        // Get search term and tag filter if any
        const searchTerm = templateListSearch.value.trim();
        const tagFilterValue = templateListTagFilter.value;
        
        // Construct query string
        let url = '/api/templates';
        const queryParams = [];
        
        if (searchTerm) {
            queryParams.push(`search=${encodeURIComponent(searchTerm)}`);
        }
        
        if (tagFilterValue) {
            queryParams.push(`tag=${encodeURIComponent(tagFilterValue)}`);
        }
        
        if (queryParams.length > 0) {
            url += '?' + queryParams.join('&');
        }
        
        // Fetch templates from the server
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load templates');
                }
                return response.json();
            })
            .then(templates => {
                if (templates.length === 0) {
                    // No templates found
                    const row = templatesTable.insertRow();
                    const cell = row.insertCell(0);
                    cell.colSpan = 3;
                    cell.textContent = 'No templates found';
                    cell.style.textAlign = 'center';
                    cell.style.padding = '20px';
                    return;
                }
                
                // Add each template as a row in the table
                templates.forEach(template => {
                    const row = templatesTable.insertRow();
                    
                    // Title cell
                    const titleCell = row.insertCell(0);
                    titleCell.textContent = template.title;
                    
                    // Tags cell
                    const tagsCell = row.insertCell(1);
                    if (template.tags && template.tags.length > 0) {
                        template.tags.forEach(tag => {
                            const tagSpan = document.createElement('span');
                            tagSpan.className = 'template-tag';
                            tagSpan.textContent = tag;
                            tagsCell.appendChild(tagSpan);
                        });
                    } else {
                        tagsCell.textContent = 'No tags';
                    }
                    
                    // Actions cell
                    const actionsCell = row.insertCell(2);
                    actionsCell.className = 'template-actions-cell';
                    
                    // Edit button
                    const editBtn = document.createElement('button');
                    editBtn.className = 'edit-btn';
                    editBtn.textContent = 'Edit';
                    editBtn.addEventListener('click', () => editTemplate(template.id));
                    
                    // Delete button
                    const deleteBtn = document.createElement('button');
                    deleteBtn.className = 'delete-btn';
                    deleteBtn.textContent = 'Delete';
                    deleteBtn.addEventListener('click', () => deleteTemplate(template.id, template.title));
                    
                    actionsCell.appendChild(editBtn);
                    actionsCell.appendChild(deleteBtn);
                });
            })
            .catch(error => {
                console.error('Error loading templates:', error);
                setTemplateStatus('Failed to load templates', 'status-error');
            });
    }
    
    // Function to load a template for editing
    function editTemplate(templateId) {
        fetch(`/api/templates/${templateId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load template');
                }
                return response.json();
            })
            .then(template => {
                // Fill the form with template data
                templateIdInput.value = template.id;
                templateTitleInput.value = template.title;
                templateContentInput.value = template.content;
                templateTagsInput.value = template.tags.join(', ');
                
                // Switch to templates tab if not already there
                const templatesTabBtn = document.querySelector('.tab-btn[data-tab="templates-tab"]');
                templatesTabBtn.click();
                
                // Scroll to the form
                document.querySelector('.template-form-section').scrollIntoView({ behavior: 'smooth' });
                
                // Update form title to indicate editing
                document.querySelector('.template-form-section h2').textContent = 'Edit Template';
                
                // Focus on the title input
                templateTitleInput.focus();
            })
            .catch(error => {
                console.error('Error loading template for editing:', error);
                setTemplateStatus(`Error: ${error.message}`, 'status-error');
            });
    }
    
    // Function to delete a template
    function deleteTemplate(templateId, templateTitle) {
        // Confirm deletion
        if (!confirm(`Are you sure you want to delete the template "${templateTitle}"?`)) {
            return;
        }
        
        fetch(`/api/templates/${templateId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete template');
            }
            return response.json();
        })
        .then(data => {
            setTemplateStatus(`Template "${templateTitle}" deleted successfully`, 'status-success');
            
            // Reload the templates list
            loadTemplates();
            
            // Also reload templates in the selector
            loadTemplatesForSelector();
        })
        .catch(error => {
            console.error('Error deleting template:', error);
            setTemplateStatus(`Error: ${error.message}`, 'status-error');
        });
    }
    
    // Function to clear the template form
    function clearTemplateForm() {
        templateIdInput.value = '';
        templateTitleInput.value = '';
        templateContentInput.value = '';
        templateTagsInput.value = '';
        
        // Reset form title
        document.querySelector('.template-form-section h2').textContent = 'Create/Edit Template';
    }
    
    // Function to load all tags for the filter dropdowns
    function loadAllTags(dropdownElement = null) {
        // If no specific dropdown is provided, load for both
        const dropdowns = dropdownElement ? [dropdownElement] : [tagFilter, templateListTagFilter];
        
        fetch('/api/tags')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load tags');
                }
                return response.json();
            })
            .then(tags => {
                // For each dropdown, clear existing options except the first one
                dropdowns.forEach(dropdown => {
                    while (dropdown.options.length > 1) {
                        dropdown.remove(1);
                    }
                    
                    // Add each tag as an option
                    tags.forEach(tag => {
                        const option = document.createElement('option');
                        option.value = tag.name;
                        option.textContent = tag.name;
                        dropdown.appendChild(option);
                    });
                });
            })
            .catch(error => {
                console.error('Error loading tags:', error);
            });
    }
    
    // ========== UTILITY FUNCTIONS ==========
    
    // Utility function to set the status message and class
    function setStatus(message, className) {
        statusElement.textContent = message;
        
        // Remove all status classes
        statusElement.classList.remove('status-success', 'status-error', 'status-loading');
        
        // Add the specific class if provided
        if (className) {
            statusElement.classList.add(className);
        }
    }
    
    // Utility function to set the template status message and class
    function setTemplateStatus(message, className) {
        templateStatus.textContent = message;
        
        // Remove all status classes
        templateStatus.classList.remove('status-success', 'status-error', 'status-loading');
        
        // Add the specific class if provided
        if (className) {
            templateStatus.classList.add(className);
        }
    }

    // Utility function to enable or disable buttons
    function setButtonsEnabled(enabled) {
        generateButton.disabled = !enabled;
        modifyButton.disabled = !enabled;
    }
    
    // ========== EVENT LISTENERS ==========
    
    // Email generation buttons
    generateButton.addEventListener('click', handleGenerateResponse);
    modifyButton.addEventListener('click', handleModifyResponse);
    
    // Template selector events
    templateSelector.addEventListener('change', previewTemplate);
    searchTemplatesBtn.addEventListener('click', loadTemplatesForSelector);
    
    // Template management buttons
    saveTemplateBtn.addEventListener('click', saveTemplate);
    clearTemplateBtn.addEventListener('click', clearTemplateForm);
    searchTemplateListBtn.addEventListener('click', loadTemplates);
    
    // Clear the status when the user starts typing in any field
    [customerEmailInput, modificationRequestInput].forEach(element => {
        element.addEventListener('input', function() {
            statusElement.textContent = '';
            statusElement.classList.remove('status-success', 'status-error', 'status-loading');
        });
    });
    
    // Clear the template status when the user starts typing in any template field
    [templateTitleInput, templateContentInput, templateTagsInput].forEach(element => {
        element.addEventListener('input', function() {
            templateStatus.textContent = '';
            templateStatus.classList.remove('status-success', 'status-error', 'status-loading');
        });
    });
    
    // Enter key search functionality for template searches
    templateSearchInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            loadTemplatesForSelector();
        }
    });
    
    templateListSearch.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            loadTemplates();
        }
    });
    
    // ========== INITIALIZATION ==========
    
    // Initial loading of templates and tags for the first tab
    loadAllTags(tagFilter);
    loadTemplatesForSelector();
});