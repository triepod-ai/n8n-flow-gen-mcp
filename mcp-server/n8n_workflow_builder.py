import uuid
import json
from typing import Dict, List, Any, Optional


class N8NWorkflowBuilder:
    def __init__(self, name: str = "Generated Workflow"):
        self.workflow = {
            "name": name,
            "nodes": [],
            "connections": {},
            "settings": {
                "executionOrder": "v1"
            },
            "staticData": {}
        }
        self.node_counter = 0
    
    def add_node(self, node_type: str, name: Optional[str] = None, 
                 parameters: Dict[str, Any] = None, 
                 position: Optional[List[int]] = None) -> str:
        """Add a node to the workflow"""
        node_id = str(uuid.uuid4())
        node_name = name or f"{node_type.split('.')[-1]}{self.node_counter}"
        self.node_counter += 1
        
        node = {
            "parameters": parameters or {},
            "id": node_id,
            "name": node_name,
            "type": node_type,
            "typeVersion": 1,
            "position": position or [200 + (self.node_counter * 200), 200]
        }
        
        self.workflow["nodes"].append(node)
        return node_name
    
    def connect_nodes(self, from_node: str, to_node: str, 
                     output_index: int = 0, input_index: int = 0):
        """Connect two nodes in the workflow"""
        if from_node not in self.workflow["connections"]:
            self.workflow["connections"][from_node] = {"main": [[]]}
        
        if len(self.workflow["connections"][from_node]["main"]) <= output_index:
            self.workflow["connections"][from_node]["main"].extend(
                [[] for _ in range(output_index + 1 - len(self.workflow["connections"][from_node]["main"]))]
            )
        
        self.workflow["connections"][from_node]["main"][output_index].append({
            "node": to_node,
            "type": "main",
            "index": input_index
        })
    
    def validate(self) -> List[str]:
        """Validate workflow structure"""
        errors = []
        
        if len(self.workflow["nodes"]) == 0:
            errors.append("Workflow must have at least one node")
        
        # Check for trigger node
        has_trigger = any(
            "trigger" in node["type"] or 
            "webhook" in node["type"] or
            "cron" in node["type"] or
            "manual" in node["type"]
            for node in self.workflow["nodes"]
        )
        
        if not has_trigger:
            errors.append("Workflow must have a trigger node")
        
        # Check for required fields
        required_fields = ["name", "nodes", "connections", "settings", "staticData"]
        for field in required_fields:
            if field not in self.workflow:
                errors.append(f"Missing required field: {field}")
        
        # Check settings structure
        if "settings" in self.workflow and "executionOrder" not in self.workflow["settings"]:
            errors.append("Missing required field: settings.executionOrder")
        
        return errors
    
    def export(self) -> str:
        """Export workflow as JSON string"""
        errors = self.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        return json.dumps(self.workflow, indent=2)
    
    def get_workflow_dict(self) -> Dict[str, Any]:
        """Get workflow as dictionary"""
        errors = self.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        return self.workflow