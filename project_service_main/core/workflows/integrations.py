# Curated list of integrations for the AI Call Center platform.
# These map our simplified frontend UI to actual n8n node types and parameters.

CURATED_INTEGRATIONS = [
    {
        "id": "telegram",
        "name": "Telegram",
        "icon": "fab fa-telegram",
        "color": "text-primary",
        "description": "Send messages via Telegram Bot",
        "n8n_node_type": "n8n-nodes-base.telegram",
        "fields": [
            {"name": "chatId", "label": "Chat ID", "type": "string", "placeholder": "@channel or 12345678"},
            {"name": "text", "label": "Message Text", "type": "text", "placeholder": "Hello from AI!"}
        ],
        "n8n_mapping": {
            "operation": "sendMessage",
            "resource": "message",
            "chatId": "{{data.chatId}}",
            "text": "{{data.text}}",
            "additionalFields": {}
        }
    },
    {
        "id": "slack",
        "name": "Slack",
        "icon": "fab fa-slack",
        "color": "text-warning",
        "description": "Post messages to Slack channels",
        "n8n_node_type": "n8n-nodes-base.slack",
        "fields": [
            {"name": "channel", "label": "Channel", "type": "string", "placeholder": "#general"},
            {"name": "text", "label": "Message", "type": "text", "placeholder": "Workflow executed."}
        ],
        "n8n_mapping": {
            "resource": "message",
            "operation": "post",
            "channel": "{{data.channel}}",
            "text": "{{data.text}}",
            "otherOptions": {}
        }
    },
    {
        "id": "http",
        "name": "HTTP Request",
        "icon": "fas fa-globe",
        "color": "text-info",
        "description": "Make custom API calls",
        "n8n_node_type": "n8n-nodes-base.httpRequest",
        "fields": [
            {"name": "method", "label": "Method", "type": "select", "options": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "url", "label": "URL", "type": "string", "placeholder": "https://api.example.com/data"},
            {"name": "body", "label": "JSON Body", "type": "text", "placeholder": '{"key": "value"}'}
        ],
        "n8n_mapping": {
            "method": "{{data.method}}",
            "url": "{{data.url}}",
            "sendBody": True,
            "bodyParameters": {
                "parameters": [
                    {"name": "custom_body", "value": "{{data.body}}"}
                ]
            },
            "options": {}
        }
    },
    {
        "id": "hubspot",
        "name": "HubSpot",
        "icon": "fab fa-hubspot",
        "color": "text-danger",
        "description": "Create or update a contact",
        "n8n_node_type": "n8n-nodes-base.hubspot",
        "fields": [
            {"name": "email", "label": "Contact Email", "type": "string", "placeholder": "user@example.com"},
            {"name": "firstName", "label": "First Name", "type": "string", "placeholder": "John"}
        ],
        "n8n_mapping": {
            "resource": "contact",
            "operation": "create",
            "email": "{{data.email}}",
            "additionalFields": {
                "firstName": "{{data.firstName}}"
            }
        }
    },
    {
        "id": "salesforce",
        "name": "Salesforce",
        "icon": "fab fa-salesforce",
        "color": "text-primary",
        "description": "Create a Lead in Salesforce",
        "n8n_node_type": "n8n-nodes-base.salesforce",
        "fields": [
            {"name": "lastName", "label": "Last Name", "type": "string", "placeholder": "Doe"},
            {"name": "company", "label": "Company", "type": "string", "placeholder": "Acme Corp"}
        ],
        "n8n_mapping": {
            "resource": "lead",
            "operation": "create",
            "lastName": "{{data.lastName}}",
            "company": "{{data.company}}",
            "additionalFields": {}
        }
    },
    {
        "id": "google_sheets",
        "name": "Google Sheets",
        "icon": "fas fa-table",
        "color": "text-success",
        "description": "Append a row to a spreadsheet",
        "n8n_node_type": "n8n-nodes-base.googleSheets",
        "fields": [
            {"name": "sheetId", "label": "Spreadsheet ID", "type": "string", "placeholder": "1BxiMVs0XRY..."},
            {"name": "range", "label": "Range", "type": "string", "placeholder": "Sheet1!A:D"},
            {"name": "values", "label": "Values (Comma separated)", "type": "string", "placeholder": "Value1, Value2"}
        ],
        "n8n_mapping": {
            "operation": "append",
            "sheetId": "{{data.sheetId}}",
            "range": "{{data.range}}",
            "options": {}
        }
    },
    {
        "id": "zendesk",
        "name": "Zendesk",
        "icon": "fas fa-headset",
        "color": "text-success",
        "description": "Create a Support Ticket",
        "n8n_node_type": "n8n-nodes-base.zendesk",
        "fields": [
            {"name": "subject", "label": "Ticket Subject", "type": "string", "placeholder": "Issue with login"},
            {"name": "description", "label": "Ticket Description", "type": "text", "placeholder": "Customer is unable to login..."}
        ],
        "n8n_mapping": {
            "resource": "ticket",
            "operation": "create",
            "subject": "{{data.subject}}",
            "description": "{{data.description}}",
            "additionalFields": {}
        }
    }
]
