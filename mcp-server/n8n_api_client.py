import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()


class N8NAPIClient:
    def __init__(self):
        self.base_url = os.getenv('N8N_HOST', 'http://localhost:5678')
        self.api_key = os.getenv('N8N_API_KEY')
        
        if not self.api_key:
            raise ValueError('N8N_API_KEY not found in environment variables')
        
        self.headers = {
            'X-N8N-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    async def list_workflows(self) -> Dict[str, Any]:
        """List all workflows"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/workflows",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to list workflows: {str(e)}")
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get specific workflow"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/workflows/{workflow_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to get workflow {workflow_id}: {str(e)}")
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new workflow"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/workflows",
                headers=self.headers,
                json=workflow_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            error_details = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = f" - Response: {e.response.json()}"
                except:
                    error_details = f" - Response text: {e.response.text}"
            raise Exception(f"Failed to create workflow: {str(e)}{error_details}")
    
    async def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing workflow"""
        try:
            response = requests.put(
                f"{self.base_url}/api/v1/workflows/{workflow_id}",
                headers=self.headers,
                json=workflow_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            error_details = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = f" - Response: {e.response.json()}"
                except:
                    error_details = f" - Response text: {e.response.text}"
            raise Exception(f"Failed to update workflow {workflow_id}: {str(e)}{error_details}")
    
    async def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete workflow"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/workflows/{workflow_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to delete workflow {workflow_id}: {str(e)}")
    
    async def execute_workflow(self, workflow_id: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute workflow"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                headers=self.headers,
                json=data or {}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to execute workflow {workflow_id}: {str(e)}")
    
    async def activate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Activate workflow using correct POST method per n8n API docs"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/workflows/{workflow_id}/activate",
                headers=self.headers,
                json={}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to activate workflow {workflow_id}: {str(e)}")
    
    async def deactivate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Deactivate workflow using correct POST method per n8n API docs"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/workflows/{workflow_id}/deactivate",
                headers=self.headers,
                json={}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to deactivate workflow {workflow_id}: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            await self.list_workflows()
            return True
        except:
            return False