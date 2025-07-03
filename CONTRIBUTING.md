# Contributing to N8N Workflow Generator MCP Server

Thank you for your interest in contributing! This guide will help you get started with development and contributions.

## Development Setup

### Prerequisites

- Python 3.12+
- uv package manager
- Git
- n8n instance for testing

### Getting Started

1. **Fork and clone the repository:**
```bash
git clone https://github.com/your-username/n8n-workflow-generator-mcp
cd n8n-workflow-generator-mcp
```

2. **Set up development environment:**
```bash
uv sync --dev
```

3. **Configure environment for testing:**
```bash
cp .env.example .env
# Edit .env with your test n8n instance details
```

4. **Run tests to verify setup:**
```bash
uv run pytest tests/
```

## Development Workflow

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting  
- **mypy** for type checking

Before committing, run:
```bash
# Format code
uv run black mcp-server/
uv run isort mcp-server/

# Type checking
uv run mypy mcp-server/

# Run tests
uv run pytest tests/
```

### Project Structure

```
mcp-server/
├── mcp_server.py          # Main MCP server and tool definitions
├── n8n_api_client.py      # n8n REST API client
├── n8n_workflow_builder.py # Workflow generation logic
├── node_library.py        # Node type definitions
└── utils.py               # Shared utilities

tests/
├── unit/                  # Unit tests
└── integration/           # Integration tests
```

### Adding New Features

1. **New MCP Tools:** Add to `mcp_server.py` with proper FastMCP decorators
2. **n8n Node Types:** Add to `node_library.py` with complete configurations
3. **API Endpoints:** Extend `n8n_api_client.py` with new methods
4. **Workflow Logic:** Enhance `n8n_workflow_builder.py` and `utils.py`

## Testing

### Running Tests

```bash
# All tests
uv run pytest tests/

# Unit tests only
uv run pytest tests/unit/

# Integration tests only  
uv run pytest tests/integration/

# With coverage
uv run pytest tests/ --cov=mcp-server/
```

### Writing Tests

- **Unit tests:** Test individual functions and classes
- **Integration tests:** Test MCP tool functionality end-to-end
- **Mock n8n API:** Use pytest fixtures for API responses

Example test structure:
```python
import pytest
from mcp_server.n8n_workflow_builder import N8NWorkflowBuilder

def test_workflow_generation():
    builder = N8NWorkflowBuilder()
    result = builder.generate_from_description("webhook trigger")
    assert "nodes" in result
    assert len(result["nodes"]) > 0
```

## Contributing Guidelines

### Pull Request Process

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes:**
   - Write code following existing patterns
   - Add/update tests for new functionality
   - Update documentation if needed

3. **Test your changes:**
```bash
uv run pytest tests/
uv run black mcp-server/ --check
uv run mypy mcp-server/
```

4. **Commit with clear messages:**
```bash
git commit -m "Add: New workflow validation feature

- Implement expression syntax checking
- Add comprehensive error messages  
- Include test coverage for edge cases
- Update documentation with examples"
```

5. **Push and create pull request:**
```bash
git push origin feature/your-feature-name
```

### Code Review Criteria

Pull requests will be reviewed for:

- **Functionality:** Does it work as intended?
- **Code Quality:** Follows project patterns and style?
- **Testing:** Adequate test coverage?
- **Documentation:** Clear docstrings and comments?
- **Backwards Compatibility:** No breaking changes?

## Types of Contributions

### 🐛 Bug Fixes
- Fix issues with workflow generation
- Resolve API client problems
- Correct validation logic

### ✨ New Features  
- Additional n8n node types
- New MCP tools
- Enhanced workflow capabilities

### 📚 Documentation
- Improve setup instructions
- Add usage examples
- API documentation

### 🧪 Testing
- Increase test coverage
- Add integration tests
- Performance testing

## Debugging and Development Tips

### Local MCP Server Testing

```bash
# Run server with debug output
DEBUG=true python -m mcp-server.mcp_server

# Test specific MCP tools
python -c "
from mcp_server.mcp_server import n8n_create_workflow
import asyncio
result = asyncio.run(n8n_create_workflow('webhook trigger'))
print(result)
"
```

### n8n API Testing

```bash
# Test API connection
python -c "
from mcp_server.n8n_api_client import N8NAPIClient
import asyncio
client = N8NAPIClient()
result = asyncio.run(client.list_workflows())
print(result)
"
```

## Common Development Tasks

### Adding a New Node Type

1. **Add to node library:**
```python
# In node_library.py
N8N_NODE_LIBRARY["NewNode"] = {
    "displayName": "New Node",
    "name": "newNode",
    "group": ["transform"],
    "description": "Description of new node",
    "defaults": {
        "name": "New Node"
    },
    "inputs": ["main"],
    "outputs": ["main"],
    "properties": [
        # Node configuration properties
    ]
}
```

2. **Add configuration helper:**
```python
def get_new_node_config(parameters: Dict[str, Any]) -> Dict[str, Any]:
    # Configuration logic
    pass
```

3. **Write tests:**
```python
def test_new_node_config():
    config = get_new_node_config({"param": "value"})
    assert config["type"] == "newNode"
```

### Adding a New MCP Tool

1. **Add to mcp_server.py:**
```python
@app.tool()
async def n8n_new_tool(parameter: str) -> Dict[str, Any]:
    """
    Tool description for MCP clients.
    
    Args:
        parameter: Description of parameter
        
    Returns:
        Result dictionary
    """
    # Implementation
    pass
```

2. **Add comprehensive tests**
3. **Update documentation**

## Release Process

Releases follow semantic versioning (x.y.z):

- **Major (x):** Breaking changes
- **Minor (y):** New features, backwards compatible
- **Patch (z):** Bug fixes

### Preparing a Release

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Tag release: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`

## Getting Help

- **GitHub Issues:** Report bugs or request features
- **Discussions:** Ask questions or share ideas
- **Discord/Slack:** Real-time discussion (if available)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute
- Follow project guidelines and standards

Thank you for contributing to the N8N Workflow Generator MCP Server!