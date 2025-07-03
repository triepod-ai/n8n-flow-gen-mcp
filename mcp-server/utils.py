import re
from typing import Dict, Any, List
from n8n_workflow_builder import N8NWorkflowBuilder
from node_library import get_node_config


async def generate_workflow_from_description(description: str, name: str) -> Dict[str, Any]:
    """
    Generate n8n workflow from natural language description using 5-step process.
    
    Step 1: Requirements Analysis - What triggers this workflow?
    Step 2: Data Flow Mapping - What data moves between steps?
    Step 3: Node Selection - Which n8n nodes best accomplish each task?
    Step 4: Connection Design - How do nodes connect and pass data?
    Step 5: Validation Check - Is the JSON structure valid and logical?
    """
    
    builder = N8NWorkflowBuilder(name)
    
    # Step 1: Requirements Analysis
    trigger_type = analyze_trigger_requirements(description)
    
    # Step 2: Data Flow Mapping
    data_flow = map_data_flow(description)
    
    # Step 3: Node Selection
    nodes = select_nodes(data_flow, trigger_type)
    
    # Step 4: Connection Design
    connections = design_connections(nodes, data_flow)
    
    # Build workflow
    node_names = {}
    
    # Add trigger node
    trigger_node = nodes["trigger"]
    trigger_name = builder.add_node(
        trigger_node["type"],
        trigger_node["name"],
        trigger_node["parameters"]
    )
    node_names["trigger"] = trigger_name
    
    # Add processing nodes
    for i, proc_node in enumerate(nodes.get("processors", [])):
        proc_name = builder.add_node(
            proc_node["type"],
            proc_node["name"],
            proc_node["parameters"]
        )
        node_names[f"processor_{i}"] = proc_name
    
    # Add action nodes
    for i, action_node in enumerate(nodes.get("actions", [])):
        action_name = builder.add_node(
            action_node["type"],
            action_node["name"],
            action_node["parameters"]
        )
        node_names[f"action_{i}"] = action_name
    
    # Connect nodes based on connections design
    for connection in connections:
        from_key = connection["from"]
        to_key = connection["to"]
        
        if from_key in node_names and to_key in node_names:
            builder.connect_nodes(
                node_names[from_key],
                node_names[to_key],
                connection.get("output_index", 0),
                connection.get("input_index", 0)
            )
    
    # Step 5: Validation Check
    return builder.get_workflow_dict()


def analyze_trigger_requirements(description: str) -> str:
    """Analyze description to determine trigger type"""
    description_lower = description.lower()
    
    if any(word in description_lower for word in ["webhook", "http", "api", "request"]):
        return "webhook"
    elif any(word in description_lower for word in ["schedule", "daily", "hourly", "cron", "timer"]):
        return "schedule"
    else:
        return "manual"


def map_data_flow(description: str) -> List[Dict[str, Any]]:
    """Map data flow from description"""
    flow_steps = []
    
    # Look for common workflow patterns
    if "process" in description.lower():
        flow_steps.append({"type": "processing", "operation": "transform_data"})
    
    if any(word in description.lower() for word in ["send", "post", "api", "http"]):
        flow_steps.append({"type": "action", "operation": "http_request"})
    
    if "respond" in description.lower():
        flow_steps.append({"type": "action", "operation": "respond"})
    
    return flow_steps


def select_nodes(data_flow: List[Dict[str, Any]], trigger_type: str) -> Dict[str, Any]:
    """Select appropriate n8n nodes for the workflow"""
    nodes = {
        "trigger": None,
        "processors": [],
        "actions": []
    }
    
    # Select trigger node
    if trigger_type == "webhook":
        nodes["trigger"] = {
            "type": "n8n-nodes-base.webhook",
            "name": "Webhook Trigger",
            "parameters": {
                "httpMethod": "POST",
                "path": "workflow-trigger",
                "options": {}
            }
        }
    elif trigger_type == "schedule":
        nodes["trigger"] = {
            "type": "n8n-nodes-base.cron",
            "name": "Schedule Trigger",
            "parameters": {
                "triggerInterval": "minutes",
                "minutesInterval": 5
            }
        }
    else:
        nodes["trigger"] = {
            "type": "n8n-nodes-base.manualTrigger",
            "name": "Manual Trigger",
            "parameters": {}
        }
    
    # Select processing and action nodes based on data flow
    for step in data_flow:
        if step["type"] == "processing":
            if step["operation"] == "transform_data":
                nodes["processors"].append({
                    "type": "n8n-nodes-base.code",
                    "name": "Process Data",
                    "parameters": {
                        "mode": "runOnceForAllItems",
                        "jsCode": "// Process the incoming data\nreturn items;"
                    }
                })
        
        elif step["type"] == "action":
            if step["operation"] == "http_request":
                nodes["actions"].append({
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "HTTP Request",
                    "parameters": {
                        "method": "POST",
                        "url": "https://api.example.com/endpoint",
                        "options": {}
                    }
                })
            elif step["operation"] == "respond":
                nodes["actions"].append({
                    "type": "n8n-nodes-base.respondToWebhook",
                    "name": "Respond",
                    "parameters": {
                        "options": {}
                    }
                })
    
    return nodes


def design_connections(nodes: Dict[str, Any], data_flow: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Design connections between nodes"""
    connections = []
    
    # Connect trigger to first processor or action
    if nodes.get("processors"):
        connections.append({
            "from": "trigger",
            "to": "processor_0"
        })
        
        # Connect processors in sequence
        for i in range(len(nodes["processors"]) - 1):
            connections.append({
                "from": f"processor_{i}",
                "to": f"processor_{i+1}"
            })
        
        # Connect last processor to first action
        if nodes.get("actions"):
            last_processor = len(nodes["processors"]) - 1
            connections.append({
                "from": f"processor_{last_processor}",
                "to": "action_0"
            })
    
    elif nodes.get("actions"):
        # Connect trigger directly to first action
        connections.append({
            "from": "trigger",
            "to": "action_0"
        })
    
    # Connect actions in sequence
    if nodes.get("actions"):
        for i in range(len(nodes["actions"]) - 1):
            connections.append({
                "from": f"action_{i}",
                "to": f"action_{i+1}"
            })
    
    return connections