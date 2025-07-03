from typing import Dict, Any

N8N_NODE_LIBRARY = {
    "triggers": {
        "webhook": {
            "type": "n8n-nodes-base.webhook",
            "description": "Receives HTTP requests to trigger workflow",
            "common_params": {
                "httpMethod": "POST",
                "path": "",
                "options": {}
            }
        },
        "schedule": {
            "type": "n8n-nodes-base.cron",
            "description": "Runs workflow on a schedule",
            "common_params": {
                "triggerInterval": "minutes",
                "minutesInterval": 1
            }
        },
        "manual": {
            "type": "n8n-nodes-base.manualTrigger",
            "description": "Manual workflow execution",
            "common_params": {}
        }
    },
    "processors": {
        "code": {
            "type": "n8n-nodes-base.code",
            "description": "Execute custom JavaScript code",
            "common_params": {
                "mode": "runOnceForAllItems",
                "jsCode": ""
            }
        },
        "set": {
            "type": "n8n-nodes-base.set",
            "description": "Set/modify data values",
            "common_params": {
                "values": {}
            }
        },
        "if": {
            "type": "n8n-nodes-base.if",
            "description": "Conditional logic branching",
            "common_params": {
                "conditions": {
                    "string": []
                }
            }
        }
    },
    "actions": {
        "http": {
            "type": "n8n-nodes-base.httpRequest",
            "description": "Make HTTP requests to external APIs",
            "common_params": {
                "method": "GET",
                "url": "",
                "options": {}
            }
        },
        "respond": {
            "type": "n8n-nodes-base.respondToWebhook",
            "description": "Send response back to webhook caller",
            "common_params": {
                "options": {}
            }
        }
    }
}


def get_node_config(category: str, node_name: str) -> Dict[str, Any]:
    """Get configuration for a specific node type"""
    return N8N_NODE_LIBRARY.get(category, {}).get(node_name, {})


def get_all_node_types() -> Dict[str, str]:
    """Get all available node types"""
    node_types = {}
    for category, nodes in N8N_NODE_LIBRARY.items():
        for node_name, config in nodes.items():
            node_types[f"{category}.{node_name}"] = config["type"]
    return node_types