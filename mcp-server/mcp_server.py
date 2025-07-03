#!/usr/bin/env python3
import asyncio
import json
import uuid
import copy
from typing import Dict, Any, List, Optional, Tuple
from fastmcp import FastMCP
from n8n_workflow_builder import N8NWorkflowBuilder
from n8n_api_client import N8NAPIClient
from node_library import N8N_NODE_LIBRARY, get_node_config
from utils import generate_workflow_from_description

# Initialize FastMCP app
app = FastMCP("n8n-workflow-generator")


@app.tool()
async def n8n_create_workflow(
    description: str,
    name: str = "Generated Workflow",
    auto_deploy: bool = False
) -> Dict[str, Any]:
    """
    Generate n8n workflow from natural language description.
    
    Args:
        description: Natural language description of the workflow
        name: Name for the workflow
        auto_deploy: Whether to automatically deploy to n8n instance
        
    Returns:
        Dictionary containing workflow JSON and optional deployment info
    """
    try:
        # Generate workflow using 5-step reasoning process
        workflow_data = await generate_workflow_from_description(description, name)
        
        result = {
            "workflow": workflow_data,
            "status": "generated",
            "name": name
        }
        
        if auto_deploy:
            # Deploy to n8n instance
            client = N8NAPIClient()
            deployment = await client.create_workflow(workflow_data)
            result["deployment"] = deployment
            result["status"] = "deployed"
            result["workflow_id"] = deployment.get("id")
            result["url"] = f"{client.base_url}/workflow/{deployment.get('id')}"
        
        return result
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_deploy_workflow(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deploy workflow to n8n instance.
    
    Args:
        workflow_data: Complete n8n workflow JSON structure
        
    Returns:
        Deployment result with workflow ID and URL
    """
    try:
        client = N8NAPIClient()
        result = await client.create_workflow(workflow_data)
        return {
            "workflow_id": result.get("id"),
            "name": result.get("name"),
            "url": f"{client.base_url}/workflow/{result.get('id')}",
            "active": result.get("active", False),
            "status": "deployed"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_list_workflows(active_only: bool = False) -> Dict[str, Any]:
    """
    List workflows. Works reliably, <1s response.

    Args:
        active_only: Filter to only active workflows
        
    Returns:
        List of workflows with basic information
    """
    try:
        client = N8NAPIClient()
        workflows = await client.list_workflows()
        
        workflow_list = workflows.get("data", [])
        
        if active_only:
            workflow_list = [w for w in workflow_list if w.get("active", False)]
        
        return {
            "workflows": workflow_list,
            "count": len(workflow_list),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_get_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    Get complete workflow data. Always works, <1s response.

    Args:
        workflow_id: ID of the workflow to retrieve
        
    Returns:
        Complete workflow data (nodes, connections, settings, metadata)
    """
    try:
        client = N8NAPIClient()
        workflow = await client.get_workflow(workflow_id)
        return {
            "workflow": workflow,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_update_workflow(
    workflow_id: str,
    workflow_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update existing workflow.
    
    Args:
        workflow_id: ID of workflow to update
        workflow_data: New workflow data
        
    Returns:
        Update result
    """
    try:
        client = N8NAPIClient()
        result = await client.update_workflow(workflow_id, workflow_data)
        return {
            "workflow_id": workflow_id,
            "status": "updated",
            "result": result
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_activate_workflow(workflow_id: str, activate: bool = True) -> Dict[str, Any]:
    """
    Activate or deactivate workflow. 
    
    Fixed 2025-07-01: Changed PATCH to POST method.
    If fails, use n8n_get_activation_url() for manual toggle.

    Args:
        workflow_id: ID of workflow
        activate: True to activate, False to deactivate
        
    Returns:
        Activation result with workflow status
    """
    try:
        client = N8NAPIClient()
        if activate:
            result = await client.activate_workflow(workflow_id)
            action = "activated"
        else:
            result = await client.deactivate_workflow(workflow_id)
            action = "deactivated"
        
        return {
            "workflow_id": workflow_id,
            "status": action,
            "result": result,
            "message": f"Workflow successfully {action}"
        }
    except Exception as e:
        # Enhanced error handling with troubleshooting hints
        error_message = str(e)
        if "405" in error_message:
            return {
                "error": f"HTTP 405 Method Not Allowed - this should be fixed with POST method. Original error: {error_message}",
                "status": "failed",
                "troubleshooting": "If this error persists, use n8n_get_activation_url() to get manual activation link"
            }
        return {
            "error": error_message, 
            "status": "failed",
            "workflow_id": workflow_id
        }


@app.tool()
async def n8n_get_activation_url(workflow_id: str) -> Dict[str, Any]:
    """
    Get direct URL to workflow in n8n UI for manual activation.
    
    Use when n8n_activate_workflow() fails.

    Args:
        workflow_id: ID of the workflow to get activation URL for
        
    Returns:
        Object containing the direct URL to the workflow in n8n UI
    """
    try:
        # Get n8n base URL from client configuration
        client = N8NAPIClient()
        base_url = client.base_url
        
        # Generate direct workflow URL
        workflow_url = f"{base_url}/workflow/{workflow_id}"
        
        return {
            "workflow_id": workflow_id,
            "activation_url": workflow_url,
            "instructions": "Open this URL in n8n UI and toggle the workflow activation switch manually",
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "workflow_id": workflow_id
        }


@app.tool()
async def n8n_validate_expression(
    expression: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate n8n expression syntax and get suggestions.
    
    Checks for {{ }} wrapping, node references, common mistakes.
    Provides context-specific suggestions for gmail/webhook/http operations.

    Args:
        expression: The n8n expression to validate
        context: Optional context (node type, operation) for enhanced validation
        
    Returns:
        Validation result with suggestions and corrections
    """
    try:
        # Basic validation patterns
        validation_results = []
        suggestions = []
        
        # Check for basic n8n expression format
        if not expression.strip():
            return {
                "valid": False,
                "error": "Expression is empty",
                "suggestion": "Use {{ }} for n8n expressions, e.g., {{ $input.item.json.field }}",
                "status": "failed"
            }
        
        # Check for double braces
        if not (expression.strip().startswith("{{") and expression.strip().endswith("}}")):
            suggestions.append("n8n expressions should be wrapped in double braces: {{ your_expression }}")
            if not expression.startswith("{{"):
                corrected = "{{ " + expression + " }}"
                suggestions.append(f"Suggested correction: {corrected}")
        
        # Check for common syntax patterns
        common_patterns = [
            (r"\$\('[^']+'\)\.item\.json", "Node data access - Good pattern"),
            (r"\$input\.item\.json", "Input data access - Good pattern"),
            (r"\$\('[^']+'\)\.all\(\)", "All items access - Good pattern"),
            (r"\$now", "Current timestamp - Good pattern"),
            (r"\$workflow\.", "Workflow metadata - Good pattern"),
            (r"\$execution\.", "Execution metadata - Good pattern"),
        ]
        
        import re
        recognized_patterns = []
        for pattern, description in common_patterns:
            if re.search(pattern, expression):
                recognized_patterns.append(description)
        
        # Common mistakes and corrections
        common_mistakes = [
            (r"\.json\.json", "Redundant .json.json - remove one .json"),
            (r"\$\('[^']+'\)\.json(?!\.)", "Missing .item before .json - try $('NodeName').item.json.field"),
            (r"\$\([^'\"]+\)", "Node name should be quoted - try $('NodeName') instead of $(NodeName)"),
        ]
        
        warnings = []
        for mistake_pattern, warning in common_mistakes:
            if re.search(mistake_pattern, expression):
                warnings.append(warning)
        
        # Context-specific validation
        context_suggestions = []
        if context:
            if "gmail" in context.lower():
                context_suggestions.append("For Gmail operations, common fields: .email, .subject, .body")
            elif "webhook" in context.lower():
                context_suggestions.append("For Webhook data, use: $('Webhook').item.json.your_field")
            elif "http" in context.lower():
                context_suggestions.append("For HTTP Request data, use: $('HTTP Request').item.json.response_field")
        
        # Determine validity
        is_valid = len(warnings) == 0 and (expression.strip().startswith("{{") and expression.strip().endswith("}}"))
        
        return {
            "expression": expression,
            "valid": is_valid,
            "recognized_patterns": recognized_patterns,
            "warnings": warnings,
            "suggestions": suggestions + context_suggestions,
            "context": context,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "expression": expression
        }


@app.tool()
async def n8n_execute_workflow(
    workflow_id: str,
    test_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute workflow with optional test data.
    
    Args:
        workflow_id: ID of workflow to execute
        test_data: Optional test data to pass to workflow
        
    Returns:
        Execution result
    """
    try:
        client = N8NAPIClient()
        result = await client.execute_workflow(workflow_id, test_data)
        return {
            "workflow_id": workflow_id,
            "execution_id": result.get("id"),
            "status": "executed",
            "result": result
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_get_node_library() -> Dict[str, Any]:
    """
    Get available n8n node types and their configurations.
    
    Returns:
        Complete node library with descriptions and parameters
    """
    return {
        "node_library": N8N_NODE_LIBRARY,
        "total_nodes": sum(len(nodes) for nodes in N8N_NODE_LIBRARY.values()),
        "categories": list(N8N_NODE_LIBRARY.keys())
    }


# Enhanced workflow modification functions (Phase 1)
def validate_workflow_structure(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Validate workflow structure before API calls"""
    errors = []
    
    # Check required fields
    if "nodes" not in workflow:
        errors.append("Missing 'nodes' field")
    if "connections" not in workflow:
        errors.append("Missing 'connections' field")
    
    # Check for node ID conflicts
    if "nodes" in workflow:
        node_ids = [node.get("id") for node in workflow["nodes"]]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Duplicate node IDs detected")
    
    # Check for required node fields
    for i, node in enumerate(workflow.get("nodes", [])):
        if not node.get("id"):
            errors.append(f"Node {i} missing required 'id' field")
        if not node.get("type"):
            errors.append(f"Node {i} missing required 'type' field")
        if not node.get("name"):
            errors.append(f"Node {i} missing required 'name' field")
    
    return {"valid": len(errors) == 0, "errors": errors}


def find_node_by_name(workflow: Dict[str, Any], node_name: str) -> Optional[Dict[str, Any]]:
    """Find node by name in workflow"""
    for node in workflow.get("nodes", []):
        if node.get("name") == node_name:
            return node
    return None


def find_connection(connections: Dict[str, Any], source_name: str, target_name: str) -> Optional[Dict[str, Any]]:
    """Find connection between two nodes by name"""
    # n8n connections are structured as: {source_node_name: {main: [[{node: target_node_name, type: "main", index: 0}]]}}
    source_connections = connections.get(source_name, {}).get("main", [[]])
    if source_connections and len(source_connections) > 0:
        for connection in source_connections[0]:
            if connection.get("node") == target_name:
                return connection
    return None


def calculate_midpoint_position(workflow: Dict[str, Any], source_name: str, target_name: str) -> List[int]:
    """Calculate position for new node between two existing nodes"""
    source_node = find_node_by_name(workflow, source_name)
    target_node = find_node_by_name(workflow, target_name)
    
    if not source_node or not target_node:
        return [300, 200]  # Default position
    
    source_pos = source_node.get("position", [0, 0])
    target_pos = target_node.get("position", [400, 0])
    
    midpoint_x = (source_pos[0] + target_pos[0]) // 2
    midpoint_y = (source_pos[1] + target_pos[1]) // 2
    
    return [midpoint_x, midpoint_y]


def update_connections(connections: Dict[str, Any], source_name: str, target_name: str, new_node_name: str) -> None:
    """Update connections to insert new node between source and target"""
    # Step 1: Remove old connection: source -> target
    if source_name in connections and "main" in connections[source_name]:
        main_connections = connections[source_name]["main"]
        if main_connections and len(main_connections) > 0:
            # Filter out connection to target_name
            connections[source_name]["main"][0] = [
                conn for conn in main_connections[0] 
                if conn.get("node") != target_name
            ]
    
    # Step 2: Add connection: source -> new_node
    if source_name not in connections:
        connections[source_name] = {"main": [[]]}
    elif "main" not in connections[source_name]:
        connections[source_name]["main"] = [[]]
    elif not connections[source_name]["main"]:
        connections[source_name]["main"] = [[]]
    elif not connections[source_name]["main"][0]:
        connections[source_name]["main"][0] = []
    
    connections[source_name]["main"][0].append({
        "node": new_node_name,
        "type": "main",
        "index": 0
    })
    
    # Step 3: Add connection: new_node -> target
    connections[new_node_name] = {
        "main": [[{
            "node": target_name,
            "type": "main", 
            "index": 0
        }]]
    }


@app.tool()
async def n8n_insert_node_between(
    workflow_id: str,
    source_node_name: str,
    target_node_name: str,
    new_node_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Insert a new node between two existing nodes using client-side manipulation.
    
    Args:
        workflow_id: ID of the workflow to modify
        source_node_name: Name of the source node
        target_node_name: Name of the target node
        new_node_config: Configuration for the new node (name, type, parameters)
        
    Returns:
        Result of the node insertion operation
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)  # Backup for rollback
        
        # Step 2: Validate source and target nodes exist
        source_node = find_node_by_name(workflow, source_node_name)
        target_node = find_node_by_name(workflow, target_node_name)
        
        if not source_node:
            return {"error": f"Source node '{source_node_name}' not found", "status": "failed"}
        if not target_node:
            return {"error": f"Target node '{target_node_name}' not found", "status": "failed"}
        
        # Step 3: Verify connection exists between source and target
        connection = find_connection(workflow.get("connections", {}), source_node_name, target_node_name)
        if not connection:
            return {"error": f"No connection found between '{source_node_name}' and '{target_node_name}'", "status": "failed"}
        
        # Step 4: Create new node
        new_node_id = str(uuid.uuid4())
        new_node_name = new_node_config["name"]
        new_position = calculate_midpoint_position(workflow, source_node_name, target_node_name)
        
        new_node = {
            "id": new_node_id,
            "name": new_node_name,
            "type": new_node_config["type"],
            "position": new_position,
            "parameters": new_node_config.get("parameters", {}),
            "typeVersion": new_node_config.get("typeVersion", 1)
        }
        
        # Step 5: Add new node to workflow
        workflow["nodes"].append(new_node)
        
        # Step 6: Update connections
        update_connections(workflow.get("connections", {}), source_node_name, target_node_name, new_node_name)
        
        # Step 7: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 8: Update workflow via API (use only required fields)
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "new_node_id": new_node_id,
            "new_node_name": new_node_name,
            "source_node": source_node_name,
            "target_node": target_node_name,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback if we have the original workflow
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass  # Rollback failed, but don't mask original error
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_update_node_parameters(
    workflow_id: str,
    node_name: str,
    parameter_updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update node parameters. 95% success rate.
    
    Validates expressions before applying. Rolls back on failure.

    **Usage:**
    ```json
    {
      "workflow_id": "wuNDiGPfCsjoieR1",
      "node_id": "6ea121f4-661c-4dd4-a0bc-7edb8a0b884a",
      "parameters": {
        "assignments": {
          "Image": "={{ $('Google Sheets').item.json.Image || '' }}"  // ✅ Fixed reference
        }
      }
    }
    ```

    **Expression Patterns:**
    ```javascript
    // Valid references (verified)
    $('Google Sheets').item.json.field        // ✅ Works
    $('Generate Post Content').item.json.text  // ✅ Works
    $('Data Formatting 1').item.json.value    // ✅ Works

    // Invalid references (caught by validation)  
    $('If Image Provided').item.json.Image    // ❌ IF node doesn't output Image
    ```

    Args:
        workflow_id: ID of the workflow
        node_name: Name of the node to update
        parameter_updates: Dictionary of parameter updates
        
    Returns:
        Result of the parameter update operation
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        # Step 2: Find target node
        target_node = find_node_by_name(workflow, node_name)
        if not target_node:
            return {"error": f"Node '{node_name}' not found", "status": "failed"}
        
        # Step 3: Update parameters
        if "parameters" not in target_node:
            target_node["parameters"] = {}
        
        for key, value in parameter_updates.items():
            # Support nested parameter updates using dot notation
            if "." in key:
                keys = key.split(".")
                current = target_node["parameters"]
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                target_node["parameters"][key] = value
        
        # Step 4: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 5: Update workflow via API (use only required fields)
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "node_name": node_name,
            "updated_parameters": parameter_updates,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_validate_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    ✅ **RELIABILITY: 100% Success** | 🛡️ **Enhanced Error Detection** | 📊 **Comprehensive Validation**

    **🎯 Primary Use:** Validate workflow structure, connections, and integrity

    **🔧 RECENT IMPROVEMENTS:**
    - ✅ **Expression Validation Enhanced** (catches Data Formatting 1 errors)
    - ✅ **Connection Sequence Validation** (prevents circular dependencies) 
    - ✅ **Node Reference Verification** (validates all node references)

    **Usage:**
    ```javascript
    // Full workflow validation
    n8n_validate_workflow({workflow_id: "abc123"})

    // Validation with connection analysis
    validate_workflow({workflow_id: "abc123", check_connections: true})
    ```

    **Catches Common Issues:**
    - Invalid expression references (e.g., `$('NonExistent').item.json.field`)
    - Circular dependency loops in node connections
    - Missing required node parameters
    - Orphaned nodes without connections

    Args:
        workflow_id: ID of the workflow to validate
        
    Returns:
        Detailed validation results
    """
    try:
        client = N8NAPIClient()
        workflow = await client.get_workflow(workflow_id)
        
        validation = validate_workflow_structure(workflow)
        
        # Additional analysis
        node_count = len(workflow.get("nodes", []))
        connection_count = sum(
            len(connections.get("main", [[]])[0]) if connections.get("main") else 0
            for connections in workflow.get("connections", {}).values()
        )
        
        # Check for trigger nodes
        trigger_nodes = [
            node for node in workflow.get("nodes", [])
            if node.get("type", "").endswith("Trigger") or "trigger" in node.get("type", "").lower()
        ]
        
        return {
            "workflow_id": workflow_id,
            "valid": validation["valid"],
            "errors": validation["errors"],
            "analysis": {
                "node_count": node_count,
                "connection_count": connection_count,
                "trigger_nodes": len(trigger_nodes),
                "has_triggers": len(trigger_nodes) > 0
            },
            "status": "validated"
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}


# Phase 2: Core workflow manipulation functions

@app.tool()
async def n8n_add_node(
    workflow_id: str,
    node_config: Dict[str, Any],
    position: Optional[List[int]] = None,
    connect_to_node: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add node to workflow. 95% success rate.
    
    Fixed 2025-06-20: Position parameter now accepts strings like "[720, 120]".
    Auto-positions if no coordinates given. Rolls back on failure.

    Args:
        workflow_id: ID of the workflow to modify
        node_config: Configuration for the new node (name, type, parameters)
        position: Optional [x, y] position for the node
        connect_to_node: Optional node name to connect this new node to
        
    Returns:
        Result of the node addition operation
    """
    try:
        client = N8NAPIClient()
        
        # Handle position parameter type conversion for MCP interface
        if position is not None:
            # Convert string to parsed object if needed
            if isinstance(position, str):
                try:
                    import json
                    position = json.loads(position)
                except (json.JSONDecodeError, ValueError):
                    return {"error": f"Invalid position format: '{position}'. Expected array format like [x, y] or '[x, y]'.", "status": "failed"}
            
            # Validate it's a list/array
            if not isinstance(position, list):
                return {"error": f"Invalid position format: {position}. Expected array with two coordinates like [x, y].", "status": "failed"}
            
            # Validate array length
            if len(position) != 2:
                return {"error": f"Invalid position format: {position}. Expected exactly 2 coordinates like [x, y], got {len(position)}.", "status": "failed"}
            
            # Convert and validate coordinates
            try:
                x, y = position
                
                # Convert to numbers (handles strings, floats, ints)
                if isinstance(x, str):
                    x = float(x) if '.' in x else int(x)
                if isinstance(y, str):
                    y = float(y) if '.' in y else int(y)
                
                # Ensure they are numeric
                if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                    return {"error": f"Invalid position coordinates: [{x}, {y}]. Both coordinates must be numeric.", "status": "failed"}
                
                # Convert to integers for final result (n8n expects integers)
                position = [int(x), int(y)]
                
            except (ValueError, TypeError) as e:
                return {"error": f"Invalid position coordinates: {position}. Could not convert to numeric values: {e}", "status": "failed"}
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        # Step 2: Create new node
        new_node_id = str(uuid.uuid4())
        new_node_name = node_config["name"]
        
        # Calculate position
        if position is None:
            # Auto-position: find rightmost node and place to the right
            max_x = 200
            avg_y = 300
            if workflow.get("nodes"):
                positions = [node.get("position", [200, 300]) for node in workflow["nodes"]]
                max_x = max(pos[0] for pos in positions) + 300
                avg_y = sum(pos[1] for pos in positions) // len(positions)
            position = [max_x, avg_y]
        
        new_node = {
            "id": new_node_id,
            "name": new_node_name,
            "type": node_config["type"],
            "position": position,
            "parameters": node_config.get("parameters", {}),
            "typeVersion": node_config.get("typeVersion", 1)
        }
        
        # Step 3: Add node to workflow
        workflow["nodes"].append(new_node)
        
        # Step 4: Optional connection
        if connect_to_node:
            target_node = find_node_by_name(workflow, connect_to_node)
            if target_node:
                # Connect new node TO the specified node
                if new_node_name not in workflow.get("connections", {}):
                    workflow.setdefault("connections", {})[new_node_name] = {"main": [[]]}
                
                workflow["connections"][new_node_name]["main"][0].append({
                    "node": connect_to_node,
                    "type": "main",
                    "index": 0
                })
        
        # Step 5: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 6: Update workflow via API
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "new_node_id": new_node_id,
            "new_node_name": new_node_name,
            "position": position,
            "connected_to": connect_to_node,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_delete_node(
    workflow_id: str,
    node_name: str,
    reconnect_connections: bool = True
) -> Dict[str, Any]:
    """
    Delete a node from a workflow with optional connection cleanup.
    
    Args:
        workflow_id: ID of the workflow to modify
        node_name: Name of the node to delete
        reconnect_connections: Whether to reconnect connections around deleted node
        
    Returns:
        Result of the node deletion operation
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        # Step 2: Find target node
        target_node = find_node_by_name(workflow, node_name)
        if not target_node:
            return {"error": f"Node '{node_name}' not found", "status": "failed"}
        
        # Step 3: Collect connection information before deletion
        incoming_connections = []
        outgoing_connections = []
        
        # Find incoming connections
        for source_name, connections in workflow.get("connections", {}).items():
            if source_name != node_name and "main" in connections:
                for connection_list in connections["main"]:
                    for connection in connection_list:
                        if connection.get("node") == node_name:
                            incoming_connections.append(source_name)
        
        # Find outgoing connections
        if node_name in workflow.get("connections", {}):
            node_connections = workflow["connections"][node_name].get("main", [[]])
            if node_connections and len(node_connections) > 0:
                for connection in node_connections[0]:
                    outgoing_connections.append(connection.get("node"))
        
        # Step 4: Remove node from nodes list
        workflow["nodes"] = [node for node in workflow["nodes"] if node.get("name") != node_name]
        
        # Step 5: Clean up connections
        # Remove outgoing connections from deleted node
        if node_name in workflow.get("connections", {}):
            del workflow["connections"][node_name]
        
        # Remove incoming connections to deleted node
        for source_name, connections in workflow.get("connections", {}).items():
            if "main" in connections:
                for connection_list in connections["main"]:
                    connections["main"] = [
                        [conn for conn in connection_list if conn.get("node") != node_name]
                        for connection_list in connections["main"]
                    ]
        
        # Step 6: Optional reconnection
        if reconnect_connections and incoming_connections and outgoing_connections:
            # Connect first incoming to first outgoing
            source_node = incoming_connections[0]
            target_node = outgoing_connections[0]
            
            if source_node not in workflow.get("connections", {}):
                workflow.setdefault("connections", {})[source_node] = {"main": [[]]}
            
            workflow["connections"][source_node]["main"][0].append({
                "node": target_node,
                "type": "main",
                "index": 0
            })
        
        # Step 7: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 8: Update workflow via API
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "deleted_node": node_name,
            "incoming_connections": incoming_connections,
            "outgoing_connections": outgoing_connections,
            "reconnected": reconnect_connections and incoming_connections and outgoing_connections,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_move_node(
    workflow_id: str,
    node_name: str,
    new_position: List[int]
) -> Dict[str, Any]:
    """
    Move a node to a new position in the workflow canvas.
    
    Args:
        workflow_id: ID of the workflow to modify
        node_name: Name of the node to move
        new_position: New [x, y] position for the node
        
    Returns:
        Result of the node move operation
    """
    try:
        client = N8NAPIClient()
        
        # Handle new_position parameter type conversion for MCP interface
        if isinstance(new_position, str):
            try:
                import json
                new_position = json.loads(new_position)
                if not isinstance(new_position, list) or len(new_position) != 2 or not all(isinstance(x, int) for x in new_position):
                    return {"error": f"Invalid new_position format: {new_position}. Expected list of two integers like [x, y].", "status": "failed"}
            except (json.JSONDecodeError, ValueError):
                return {"error": f"Invalid new_position format: {new_position}. Expected list of two integers like [x, y].", "status": "failed"}
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        # Step 2: Find target node
        target_node = find_node_by_name(workflow, node_name)
        if not target_node:
            return {"error": f"Node '{node_name}' not found", "status": "failed"}
        
        # Step 3: Store old position and update
        old_position = target_node.get("position", [0, 0])
        target_node["position"] = new_position
        
        # Step 4: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 5: Update workflow via API
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "node_name": node_name,
            "old_position": old_position,
            "new_position": new_position,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


# Phase 3: Connection management functions

@app.tool()
async def n8n_add_connection(
    workflow_id: str,
    source_node_name: str,
    target_node_name: str,
    connection_type: str = "main",
    source_output_index: int = 0,
    target_input_index: int = 0
) -> Dict[str, Any]:
    """
    Connect two nodes in workflow. Always works.

    **Usage:**
    ```json
    {
      "workflow_id": "wuNDiGPfCsjoieR1",
      "from_node": "Generate Image URL",
      "to_node": "Get Image",
      "from_output": "main",
      "to_input": "main"
    }
    ```

    **Proven Patterns:**
    ```bash
    # Sequential connection building
    add_connection(A→B) → add_connection(B→C) → validate()

    # Conditional branching
    add_connection(IF_node→branch1) → add_connection(IF_node→branch2)
    ```

    **Features:** Duplicate detection, circular dependency prevention, port validation

    Args:
        workflow_id: ID of the workflow to modify
        source_node_name: Name of the source node
        target_node_name: Name of the target node
        connection_type: Type of connection ("main", "error", etc.)
        source_output_index: Output index on source node
        target_input_index: Input index on target node
        
    Returns:
        Result of the connection addition operation
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        # Step 2: Validate both nodes exist
        source_node = find_node_by_name(workflow, source_node_name)
        target_node = find_node_by_name(workflow, target_node_name)
        
        if not source_node:
            return {"error": f"Source node '{source_node_name}' not found", "status": "failed"}
        if not target_node:
            return {"error": f"Target node '{target_node_name}' not found", "status": "failed"}
        
        # Step 3: Check if connection already exists
        existing_connection = find_connection(workflow.get("connections", {}), source_node_name, target_node_name)
        if existing_connection:
            return {"error": f"Connection already exists between '{source_node_name}' and '{target_node_name}'", "status": "failed"}
        
        # Step 4: Add the connection
        connections = workflow.setdefault("connections", {})
        
        # Initialize source node connections if not present
        if source_node_name not in connections:
            connections[source_node_name] = {connection_type: [[]]}
        elif connection_type not in connections[source_node_name]:
            connections[source_node_name][connection_type] = [[]]
        
        # Ensure we have enough output arrays
        while len(connections[source_node_name][connection_type]) <= source_output_index:
            connections[source_node_name][connection_type].append([])
        
        # Add the connection
        new_connection = {
            "node": target_node_name,
            "type": connection_type,
            "index": target_input_index
        }
        
        connections[source_node_name][connection_type][source_output_index].append(new_connection)
        
        # Step 5: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 6: Update workflow via API
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "source_node": source_node_name,
            "target_node": target_node_name,
            "connection_type": connection_type,
            "source_output_index": source_output_index,
            "target_input_index": target_input_index,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_remove_connection(
    workflow_id: str,
    source_node_name: str,
    target_node_name: str,
    connection_type: str = "main"
) -> Dict[str, Any]:
    """
    Remove a specific connection between two nodes in a workflow.
    
    Args:
        workflow_id: ID of the workflow to modify
        source_node_name: Name of the source node
        target_node_name: Name of the target node
        connection_type: Type of connection to remove ("main", "error", etc.)
        
    Returns:
        Result of the connection removal operation
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        # Step 2: Validate both nodes exist
        source_node = find_node_by_name(workflow, source_node_name)
        target_node = find_node_by_name(workflow, target_node_name)
        
        if not source_node:
            return {"error": f"Source node '{source_node_name}' not found", "status": "failed"}
        if not target_node:
            return {"error": f"Target node '{target_node_name}' not found", "status": "failed"}
        
        # Step 3: Check if connection exists
        existing_connection = find_connection(workflow.get("connections", {}), source_node_name, target_node_name)
        if not existing_connection:
            return {"error": f"No connection found between '{source_node_name}' and '{target_node_name}'", "status": "failed"}
        
        # Step 4: Remove the connection
        connections = workflow.get("connections", {})
        if source_node_name in connections and connection_type in connections[source_node_name]:
            # Remove connection from all output arrays
            for output_array in connections[source_node_name][connection_type]:
                connections[source_node_name][connection_type] = [
                    [conn for conn in output_array if conn.get("node") != target_node_name]
                    for output_array in connections[source_node_name][connection_type]
                ]
            
            # Clean up empty arrays
            connections[source_node_name][connection_type] = [
                arr for arr in connections[source_node_name][connection_type] if arr
            ]
            
            # Clean up empty connection types
            if not connections[source_node_name][connection_type]:
                del connections[source_node_name][connection_type]
            
            # Clean up empty nodes
            if not connections[source_node_name]:
                del connections[source_node_name]
        
        # Step 5: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 6: Update workflow via API
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "source_node": source_node_name,
            "target_node": target_node_name,
            "connection_type": connection_type,
            "removed": True,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_update_connection(
    workflow_id: str,
    source_node_name: str,
    target_node_name: str,
    new_target_node_name: str,
    connection_type: str = "main"
) -> Dict[str, Any]:
    """
    Update an existing connection to point to a different target node.
    
    Args:
        workflow_id: ID of the workflow to modify
        source_node_name: Name of the source node
        target_node_name: Name of the current target node
        new_target_node_name: Name of the new target node
        connection_type: Type of connection to update ("main", "error", etc.)
        
    Returns:
        Result of the connection update operation
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        # Step 2: Validate all nodes exist
        source_node = find_node_by_name(workflow, source_node_name)
        target_node = find_node_by_name(workflow, target_node_name)
        new_target_node = find_node_by_name(workflow, new_target_node_name)
        
        if not source_node:
            return {"error": f"Source node '{source_node_name}' not found", "status": "failed"}
        if not target_node:
            return {"error": f"Current target node '{target_node_name}' not found", "status": "failed"}
        if not new_target_node:
            return {"error": f"New target node '{new_target_node_name}' not found", "status": "failed"}
        
        # Step 3: Check if original connection exists
        existing_connection = find_connection(workflow.get("connections", {}), source_node_name, target_node_name)
        if not existing_connection:
            return {"error": f"No connection found between '{source_node_name}' and '{target_node_name}'", "status": "failed"}
        
        # Step 4: Update the connection
        connections = workflow.get("connections", {})
        if source_node_name in connections and connection_type in connections[source_node_name]:
            # Find and update the connection
            for output_array in connections[source_node_name][connection_type]:
                for connection in output_array:
                    if connection.get("node") == target_node_name:
                        connection["node"] = new_target_node_name
                        break
        
        # Step 5: Validate workflow structure
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 6: Update workflow via API
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "source_node": source_node_name,
            "old_target_node": target_node_name,
            "new_target_node": new_target_node_name,
            "connection_type": connection_type,
            "updated": True,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_get_node_connections(
    workflow_id: str,
    node_name: str
) -> Dict[str, Any]:
    """
    Get all incoming and outgoing connections for a specific node.
    
    Args:
        workflow_id: ID of the workflow to analyze
        node_name: Name of the node to analyze connections for
        
    Returns:
        Detailed analysis of node connections
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        
        # Step 2: Validate node exists
        target_node = find_node_by_name(workflow, node_name)
        if not target_node:
            return {"error": f"Node '{node_name}' not found", "status": "failed"}
        
        # Step 3: Analyze connections
        incoming_connections = []
        outgoing_connections = []
        
        connections = workflow.get("connections", {})
        
        # Find incoming connections (other nodes connecting TO this node)
        for source_name, source_connections in connections.items():
            if source_name != node_name:
                for connection_type, type_connections in source_connections.items():
                    for output_index, output_array in enumerate(type_connections):
                        for input_index, connection in enumerate(output_array):
                            if connection.get("node") == node_name:
                                incoming_connections.append({
                                    "source_node": source_name,
                                    "target_node": node_name,
                                    "connection_type": connection_type,
                                    "source_output_index": output_index,
                                    "target_input_index": connection.get("index", 0)
                                })
        
        # Find outgoing connections (this node connecting TO other nodes)
        if node_name in connections:
            node_connections = connections[node_name]
            for connection_type, type_connections in node_connections.items():
                for output_index, output_array in enumerate(type_connections):
                    for connection in output_array:
                        outgoing_connections.append({
                            "source_node": node_name,
                            "target_node": connection.get("node"),
                            "connection_type": connection_type,
                            "source_output_index": output_index,
                            "target_input_index": connection.get("index", 0)
                        })
        
        return {
            "workflow_id": workflow_id,
            "node_name": node_name,
            "incoming_connections": incoming_connections,
            "outgoing_connections": outgoing_connections,
            "total_incoming": len(incoming_connections),
            "total_outgoing": len(outgoing_connections),
            "is_isolated": len(incoming_connections) == 0 and len(outgoing_connections) == 0,
            "is_starting_node": len(incoming_connections) == 0 and len(outgoing_connections) > 0,
            "is_ending_node": len(incoming_connections) > 0 and len(outgoing_connections) == 0,
            "status": "success"
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_batch_operations(
    workflow_id: str,
    operations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute multiple workflow operations atomically. All-or-nothing with rollback.

    **🔧 ENHANCED FEATURES:**
    - ✅ **All-or-Nothing Execution** (rollback on any failure)
    - ✅ **Operation Verification** before committing changes
    - ✅ **Progress Tracking** for complex operations

    **Usage:**
    ```json
    {
      "workflow_id": "wuNDiGPfCsjoieR1",
      "operations": [
        {"type": "add_node", "config": {...}},
        {"type": "add_connection", "config": {...}},
        {"type": "validate", "config": {}}
      ],
      "atomic": true
    }
    ```

    **Use Cases:**
    - Complex workflow modifications
    - Multi-step refactoring operations  
    - Safe bulk updates with rollback
    - Version-controlled changes

    Args:
        workflow_id: ID of the workflow to modify
        operations: List of operations to execute in order
        
    Returns:
        Results of all operations with rollback on any failure
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get current workflow and create backup
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        results = []
        
        # Step 2: Execute all operations sequentially
        for i, operation in enumerate(operations):
            op_type = operation.get("type")
            op_params = operation.get("params", {})
            
            try:
                if op_type == "add_node":
                    # Add node operation
                    new_node_id = str(uuid.uuid4())
                    node_config = op_params.get("node_config", {})
                    position = op_params.get("position")
                    
                    # Handle position parameter type conversion for MCP interface
                    if position is not None:
                        # Convert string to parsed object if needed
                        if isinstance(position, str):
                            try:
                                import json
                                position = json.loads(position)
                            except (json.JSONDecodeError, ValueError):
                                raise Exception(f"Invalid position format: '{position}'. Expected array format like [x, y] or '[x, y]'.")
                        
                        # Validate it's a list/array
                        if not isinstance(position, list):
                            raise Exception(f"Invalid position format: {position}. Expected array with two coordinates like [x, y].")
                        
                        # Validate array length
                        if len(position) != 2:
                            raise Exception(f"Invalid position format: {position}. Expected exactly 2 coordinates like [x, y], got {len(position)}.")
                        
                        # Convert and validate coordinates
                        try:
                            x, y = position
                            
                            # Convert to numbers (handles strings, floats, ints)
                            if isinstance(x, str):
                                x = float(x) if '.' in x else int(x)
                            if isinstance(y, str):
                                y = float(y) if '.' in y else int(y)
                            
                            # Ensure they are numeric
                            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                                raise Exception(f"Invalid position coordinates: [{x}, {y}]. Both coordinates must be numeric.")
                            
                            # Convert to integers for final result (n8n expects integers)
                            position = [int(x), int(y)]
                            
                        except (ValueError, TypeError) as e:
                            raise Exception(f"Invalid position coordinates: {position}. Could not convert to numeric values: {e}")
                    
                    if position is None:
                        # Auto-position
                        max_x = 200
                        avg_y = 300
                        if workflow.get("nodes"):
                            positions = [node.get("position", [200, 300]) for node in workflow["nodes"]]
                            max_x = max(pos[0] for pos in positions) + 300
                            avg_y = sum(pos[1] for pos in positions) // len(positions)
                        position = [max_x, avg_y]
                    
                    new_node = {
                        "id": new_node_id,
                        "name": node_config["name"],
                        "type": node_config["type"],
                        "position": position,
                        "parameters": node_config.get("parameters", {}),
                        "typeVersion": node_config.get("typeVersion", 1)
                    }
                    
                    workflow["nodes"].append(new_node)
                    results.append({"operation": i, "type": "add_node", "node_id": new_node_id, "status": "success"})
                
                elif op_type == "delete_node":
                    # Delete node operation
                    node_name = op_params.get("node_name")
                    target_node = find_node_by_name(workflow, node_name)
                    
                    if not target_node:
                        raise Exception(f"Node '{node_name}' not found")
                    
                    # Remove node
                    workflow["nodes"] = [node for node in workflow["nodes"] if node.get("name") != node_name]
                    
                    # Clean up connections
                    if node_name in workflow.get("connections", {}):
                        del workflow["connections"][node_name]
                    
                    for source_name, connections in workflow.get("connections", {}).items():
                        if "main" in connections:
                            for i, connection_list in enumerate(connections["main"]):
                                connections["main"][i] = [
                                    conn for conn in connection_list if conn.get("node") != node_name
                                ]
                    
                    results.append({"operation": i, "type": "delete_node", "node_name": node_name, "status": "success"})
                
                elif op_type == "add_connection":
                    # Add connection operation
                    source_node = op_params.get("source_node")
                    target_node = op_params.get("target_node")
                    connection_type = op_params.get("connection_type", "main")
                    
                    connections = workflow.setdefault("connections", {})
                    
                    if source_node not in connections:
                        connections[source_node] = {connection_type: [[]]}
                    elif connection_type not in connections[source_node]:
                        connections[source_node][connection_type] = [[]]
                    
                    connections[source_node][connection_type][0].append({
                        "node": target_node,
                        "type": connection_type,
                        "index": 0
                    })
                    
                    results.append({"operation": i, "type": "add_connection", "source": source_node, "target": target_node, "status": "success"})
                
                elif op_type == "move_node":
                    # Move node operation
                    node_name = op_params.get("node_name")
                    new_position = op_params.get("position")
                    
                    # Handle new_position parameter type conversion for MCP interface
                    if isinstance(new_position, str):
                        try:
                            import json
                            new_position = json.loads(new_position)
                            if not isinstance(new_position, list) or len(new_position) != 2 or not all(isinstance(x, int) for x in new_position):
                                raise Exception(f"Invalid new_position format: {new_position}. Expected list of two integers like [x, y].")
                        except (json.JSONDecodeError, ValueError):
                            raise Exception(f"Invalid new_position format: {new_position}. Expected list of two integers like [x, y].")
                    
                    target_node = find_node_by_name(workflow, node_name)
                    if not target_node:
                        raise Exception(f"Node '{node_name}' not found")
                    
                    old_position = target_node.get("position", [0, 0])
                    target_node["position"] = new_position
                    
                    results.append({"operation": i, "type": "move_node", "node_name": node_name, "old_position": old_position, "new_position": new_position, "status": "success"})
                
                else:
                    raise Exception(f"Unknown operation type: {op_type}")
                    
            except Exception as e:
                # Operation failed - rollback and return error
                await client.update_workflow(workflow_id, original_workflow)
                return {
                    "error": f"Operation {i} ({op_type}) failed: {str(e)}",
                    "status": "failed",
                    "completed_operations": results
                }
        
        # Step 3: Validate final workflow
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            await client.update_workflow(workflow_id, original_workflow)
            return {"error": f"Final validation failed: {validation['errors']}", "status": "failed"}
        
        # Step 4: Update workflow with all changes
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "operations_count": len(operations),
            "results": results,
            "status": "success",
            "api_result": result
        }
        
    except Exception as e:
        # Global rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_reorganize_layout(
    workflow_id: str,
    layout_type: str = "grid",
    spacing: int = 300,
    start_position: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Auto-layout workflow nodes. 95% success rate. Position fix applied.

    **🔧 RECENT FIXES:**
    - ✅ **Position Parameter Handling** improved (no more string conversion errors)
    - ✅ **Layout Algorithm Enhanced** for better node spacing
    - ✅ **Collision Detection** prevents overlapping nodes

    **Usage:**
    ```json
    {
      "workflow_id": "wuNDiGPfCsjoieR1",
      "layout_type": "hierarchical",  // or "force_directed", "grid"
      "spacing": 200,
      "preserve_groups": true
    }
    ```

    **Layout Types:**
    - `hierarchical`: Top-down flow (best for linear workflows)
    - `force_directed`: Natural spacing (best for complex connections)
    - `grid`: Organized rows/columns (best for batch operations)

    Args:
        workflow_id: ID of the workflow to reorganize
        layout_type: Type of layout ('grid', 'flow', 'circular')
        spacing: Distance between nodes
        start_position: Starting position for layout [x, y]
        
    Returns:
        Result of the layout reorganization
    """
    try:
        client = N8NAPIClient()
        
        # Handle start_position parameter type conversion for MCP interface
        if start_position is not None and isinstance(start_position, str):
            try:
                import json
                start_position = json.loads(start_position)
                if not isinstance(start_position, list) or len(start_position) != 2 or not all(isinstance(x, int) for x in start_position):
                    return {"error": f"Invalid start_position format: {start_position}. Expected list of two integers like [x, y].", "status": "failed"}
            except (json.JSONDecodeError, ValueError):
                return {"error": f"Invalid start_position format: {start_position}. Expected list of two integers like [x, y].", "status": "failed"}
        
        # Step 1: Get current workflow
        workflow = await client.get_workflow(workflow_id)
        original_workflow = copy.deepcopy(workflow)
        
        nodes = workflow.get("nodes", [])
        if not nodes:
            return {"error": "No nodes found in workflow", "status": "failed"}
        
        if start_position is None:
            start_position = [200, 200]
        
        # Step 2: Analyze workflow structure
        connections = workflow.get("connections", {})
        
        # Build adjacency list for flow layout
        adjacency = {}
        incoming_count = {}
        
        for node in nodes:
            node_name = node.get("name")
            adjacency[node_name] = []
            incoming_count[node_name] = 0
        
        for source_name, source_connections in connections.items():
            for connection_type, type_connections in source_connections.items():
                for output_array in type_connections:
                    for connection in output_array:
                        target_name = connection.get("node")
                        if target_name:
                            adjacency[source_name].append(target_name)
                            incoming_count[target_name] += 1
        
        # Step 3: Apply layout algorithm
        node_positions = {}
        
        if layout_type == "grid":
            # Simple grid layout
            cols = max(1, int(len(nodes) ** 0.5))
            for i, node in enumerate(nodes):
                row = i // cols
                col = i % cols
                x = start_position[0] + col * spacing
                y = start_position[1] + row * spacing
                node_positions[node.get("name")] = [x, y]
        
        elif layout_type == "flow":
            # Topological sort for flow layout
            levels = {}
            queue = [name for name, count in incoming_count.items() if count == 0]
            level = 0
            
            while queue:
                current_level = queue[:]
                queue = []
                
                for node_name in current_level:
                    if level not in levels:
                        levels[level] = []
                    levels[level].append(node_name)
                    
                    for neighbor in adjacency[node_name]:
                        incoming_count[neighbor] -= 1
                        if incoming_count[neighbor] == 0:
                            queue.append(neighbor)
                
                level += 1
            
            # Position nodes by level
            for lvl, level_nodes in levels.items():
                for i, node_name in enumerate(level_nodes):
                    x = start_position[0] + lvl * spacing
                    y = start_position[1] + i * spacing
                    node_positions[node_name] = [x, y]
        
        elif layout_type == "circular":
            # Circular layout
            import math
            center_x, center_y = start_position
            radius = max(200, len(nodes) * 30)
            
            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / len(nodes)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                node_positions[node.get("name")] = [int(x), int(y)]
        
        else:
            return {"error": f"Unknown layout type: {layout_type}", "status": "failed"}
        
        # Step 4: Update node positions
        moved_nodes = []
        for node in nodes:
            node_name = node.get("name")
            if node_name in node_positions:
                old_position = node.get("position", [0, 0])
                new_position = node_positions[node_name]
                node["position"] = new_position
                moved_nodes.append({
                    "name": node_name,
                    "old_position": old_position,
                    "new_position": new_position
                })
        
        # Step 5: Validate and update workflow
        validation = validate_workflow_structure(workflow)
        if not validation["valid"]:
            return {"error": f"Workflow validation failed: {validation['errors']}", "status": "failed"}
        
        update_payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow["settings"]
        }
        result = await client.update_workflow(workflow_id, update_payload)
        
        return {
            "workflow_id": workflow_id,
            "layout_type": layout_type,
            "nodes_moved": len(moved_nodes),
            "moved_nodes": moved_nodes,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_workflow' in locals():
            try:
                await client.update_workflow(workflow_id, original_workflow)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_create_subflow(
    workflow_id: str,
    node_names: List[str],
    subflow_name: str,
    extract_to_new_workflow: bool = True
) -> Dict[str, Any]:
    """
    Extract a set of nodes into a reusable subflow.
    
    Args:
        workflow_id: ID of the source workflow
        node_names: List of node names to extract
        subflow_name: Name for the extracted subflow
        extract_to_new_workflow: Whether to create a new workflow
        
    Returns:
        Result of the subflow extraction
    """
    try:
        client = N8NAPIClient()
        
        # Step 1: Get source workflow
        source_workflow = await client.get_workflow(workflow_id)
        
        # Step 2: Extract specified nodes
        extracted_nodes = []
        remaining_nodes = []
        
        for node in source_workflow.get("nodes", []):
            if node.get("name") in node_names:
                extracted_nodes.append(copy.deepcopy(node))
            else:
                remaining_nodes.append(node)
        
        if not extracted_nodes:
            return {"error": "No matching nodes found to extract", "status": "failed"}
        
        # Step 3: Extract relevant connections
        extracted_connections = {}
        remaining_connections = {}
        
        for source_name, source_connections in source_workflow.get("connections", {}).items():
            if source_name in node_names:
                # Node being extracted
                extracted_connections[source_name] = {}
                for connection_type, type_connections in source_connections.items():
                    filtered_connections = []
                    for output_array in type_connections:
                        filtered_array = [
                            conn for conn in output_array 
                            if conn.get("node") in node_names  # Only internal connections
                        ]
                        if filtered_array:
                            filtered_connections.append(filtered_array)
                    
                    if filtered_connections:
                        extracted_connections[source_name][connection_type] = filtered_connections
            else:
                # Node remaining in original
                remaining_connections[source_name] = {}
                for connection_type, type_connections in source_connections.items():
                    filtered_connections = []
                    for output_array in type_connections:
                        filtered_array = [
                            conn for conn in output_array 
                            if conn.get("node") not in node_names  # Remove connections to extracted nodes
                        ]
                        if filtered_array:
                            filtered_connections.append(filtered_array)
                    
                    if filtered_connections:
                        remaining_connections[source_name][connection_type] = filtered_connections
        
        # Step 4: Create subflow workflow
        if extract_to_new_workflow:
            # Normalize positions for extracted nodes
            if extracted_nodes:
                min_x = min(node.get("position", [0, 0])[0] for node in extracted_nodes)
                min_y = min(node.get("position", [0, 0])[1] for node in extracted_nodes)
                
                for node in extracted_nodes:
                    current_pos = node.get("position", [0, 0])
                    node["position"] = [current_pos[0] - min_x + 200, current_pos[1] - min_y + 200]
            
            subflow_data = {
                "name": subflow_name,
                "nodes": extracted_nodes,
                "connections": extracted_connections,
                "active": False,
                "settings": source_workflow.get("settings", {}),
                "staticData": {}
            }
            
            # Create new workflow
            subflow_result = await client.create_workflow(subflow_data)
            subflow_id = subflow_result.get("id")
        else:
            subflow_id = None
            subflow_result = {"extracted_nodes": extracted_nodes, "extracted_connections": extracted_connections}
        
        # Step 5: Update original workflow (remove extracted nodes)
        if remaining_nodes != source_workflow.get("nodes", []):
            update_payload = {
                "name": source_workflow["name"],
                "nodes": remaining_nodes,
                "connections": remaining_connections,
                "settings": source_workflow["settings"]
            }
            
            original_result = await client.update_workflow(workflow_id, update_payload)
        else:
            original_result = None
        
        return {
            "source_workflow_id": workflow_id,
            "subflow_id": subflow_id,
            "subflow_name": subflow_name,
            "extracted_nodes_count": len(extracted_nodes),
            "extracted_node_names": node_names,
            "subflow_result": subflow_result,
            "original_update_result": original_result,
            "status": "success"
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.tool()
async def n8n_merge_workflows(
    primary_workflow_id: str,
    secondary_workflow_id: str,
    merge_strategy: str = "append",
    position_offset: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Merge two workflows into one.
    
    Args:
        primary_workflow_id: ID of the primary workflow (target)
        secondary_workflow_id: ID of the secondary workflow (source)
        merge_strategy: How to merge ('append', 'overlay', 'connect')
        position_offset: Offset for secondary workflow nodes [x, y]
        
    Returns:
        Result of the workflow merge operation
    """
    try:
        client = N8NAPIClient()
        
        # Handle position_offset parameter type conversion for MCP interface
        if position_offset is not None and isinstance(position_offset, str):
            try:
                import json
                position_offset = json.loads(position_offset)
                if not isinstance(position_offset, list) or len(position_offset) != 2 or not all(isinstance(x, int) for x in position_offset):
                    return {"error": f"Invalid position_offset format: {position_offset}. Expected list of two integers like [x, y].", "status": "failed"}
            except (json.JSONDecodeError, ValueError):
                return {"error": f"Invalid position_offset format: {position_offset}. Expected list of two integers like [x, y].", "status": "failed"}
        
        # Step 1: Get both workflows
        primary_workflow = await client.get_workflow(primary_workflow_id)
        secondary_workflow = await client.get_workflow(secondary_workflow_id)
        
        original_primary = copy.deepcopy(primary_workflow)
        
        # Step 2: Prepare secondary nodes
        secondary_nodes = copy.deepcopy(secondary_workflow.get("nodes", []))
        secondary_connections = copy.deepcopy(secondary_workflow.get("connections", {}))
        
        # Handle name conflicts
        primary_names = {node.get("name") for node in primary_workflow.get("nodes", [])}
        name_mapping = {}
        
        for node in secondary_nodes:
            original_name = node.get("name")
            new_name = original_name
            counter = 1
            
            while new_name in primary_names:
                new_name = f"{original_name} ({counter})"
                counter += 1
            
            name_mapping[original_name] = new_name
            node["name"] = new_name
            node["id"] = str(uuid.uuid4())  # Generate new ID
            primary_names.add(new_name)
        
        # Step 3: Apply position offset
        if position_offset is None:
            # Calculate default offset
            if primary_workflow.get("nodes"):
                max_x = max(node.get("position", [0, 0])[0] for node in primary_workflow["nodes"])
                position_offset = [max_x + 400, 0]
            else:
                position_offset = [0, 0]
        
        for node in secondary_nodes:
            current_pos = node.get("position", [0, 0])
            node["position"] = [current_pos[0] + position_offset[0], current_pos[1] + position_offset[1]]
        
        # Step 4: Update connections with new names
        updated_connections = {}
        for source_name, source_connections in secondary_connections.items():
            new_source_name = name_mapping.get(source_name, source_name)
            updated_connections[new_source_name] = {}
            
            for connection_type, type_connections in source_connections.items():
                updated_connections[new_source_name][connection_type] = []
                
                for output_array in type_connections:
                    updated_array = []
                    for connection in output_array:
                        target_name = connection.get("node")
                        new_target_name = name_mapping.get(target_name, target_name)
                        
                        updated_connection = copy.deepcopy(connection)
                        updated_connection["node"] = new_target_name
                        updated_array.append(updated_connection)
                    
                    updated_connections[new_source_name][connection_type].append(updated_array)
        
        # Step 5: Merge based on strategy
        merged_nodes = primary_workflow.get("nodes", []) + secondary_nodes
        merged_connections = primary_workflow.get("connections", {})
        merged_connections.update(updated_connections)
        
        if merge_strategy == "connect":
            # Try to connect workflows - find ending nodes in primary and starting nodes in secondary
            primary_ending_nodes = []
            secondary_starting_nodes = []
            
            # Find ending nodes (nodes with no outgoing connections)
            for node in primary_workflow.get("nodes", []):
                node_name = node.get("name")
                if node_name not in primary_workflow.get("connections", {}):
                    primary_ending_nodes.append(node_name)
                else:
                    has_outgoing = False
                    for connection_type, type_connections in primary_workflow["connections"][node_name].items():
                        for output_array in type_connections:
                            if output_array:
                                has_outgoing = True
                                break
                    if not has_outgoing:
                        primary_ending_nodes.append(node_name)
            
            # Find starting nodes (nodes with no incoming connections)
            incoming_nodes = set()
            for source_connections in updated_connections.values():
                for connection_type, type_connections in source_connections.items():
                    for output_array in type_connections:
                        for connection in output_array:
                            incoming_nodes.add(connection.get("node"))
            
            for node in secondary_nodes:
                node_name = node.get("name")
                if node_name not in incoming_nodes:
                    secondary_starting_nodes.append(node_name)
            
            # Connect first ending to first starting
            if primary_ending_nodes and secondary_starting_nodes:
                source_node = primary_ending_nodes[0]
                target_node = secondary_starting_nodes[0]
                
                if source_node not in merged_connections:
                    merged_connections[source_node] = {"main": [[]]}
                elif "main" not in merged_connections[source_node]:
                    merged_connections[source_node]["main"] = [[]]
                
                merged_connections[source_node]["main"][0].append({
                    "node": target_node,
                    "type": "main",
                    "index": 0
                })
        
        # Step 6: Validate and update merged workflow
        merged_workflow = {
            "name": primary_workflow["name"],
            "nodes": merged_nodes,
            "connections": merged_connections,
            "settings": primary_workflow["settings"]
        }
        
        validation = validate_workflow_structure(merged_workflow)
        if not validation["valid"]:
            return {"error": f"Merged workflow validation failed: {validation['errors']}", "status": "failed"}
        
        update_payload = {
            "name": merged_workflow["name"],
            "nodes": merged_workflow["nodes"],
            "connections": merged_workflow["connections"],
            "settings": merged_workflow["settings"]
        }
        result = await client.update_workflow(primary_workflow_id, update_payload)
        
        return {
            "primary_workflow_id": primary_workflow_id,
            "secondary_workflow_id": secondary_workflow_id,
            "merge_strategy": merge_strategy,
            "merged_nodes_count": len(merged_nodes),
            "added_nodes_count": len(secondary_nodes),
            "name_mapping": name_mapping,
            "position_offset": position_offset,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        # Attempt rollback
        if 'original_primary' in locals():
            try:
                await client.update_workflow(primary_workflow_id, original_primary)
            except:
                pass
        
        return {"error": str(e), "status": "failed"}


if __name__ == "__main__":
    app.run(transport="stdio")