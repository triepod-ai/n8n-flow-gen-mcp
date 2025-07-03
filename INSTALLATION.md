# Installation Guide

This guide provides detailed instructions for setting up the N8N Workflow Generator MCP Server.

## Prerequisites

Before installing, ensure you have:

- **Python 3.12 or higher** - Check with `python --version`
- **uv package manager** - Install from [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- **n8n instance** - Local or remote n8n installation
- **n8n API key** - Generated from your n8n instance
- **MCP client** - Claude Code or another MCP-compatible client

## Step 1: Clone and Setup

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/n8n-workflow-generator-mcp
cd n8n-workflow-generator-mcp
```

2. **Install dependencies:**
```bash
uv sync
```

This will create a virtual environment and install all required dependencies.

## Step 2: Configure n8n API Access

1. **Generate n8n API key:**
   - Open your n8n instance (e.g., `http://localhost:5678`)
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Copy the generated key

2. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` file:
```bash
# Required: n8n instance URL and API key
N8N_HOST=http://localhost:5678
N8N_API_KEY=your_actual_api_key_here

# Optional: Debug settings
DEBUG=false
LOG_LEVEL=info
```

## Step 3: Configure MCP Client

### For Claude Code

1. **Create MCP configuration:**
```bash
cp .mcp.json.example .mcp.json
```

2. **Edit `.mcp.json`** with the correct path:
```json
{
  "mcpServers": {
    "n8n-workflow-generator": {
      "command": "python",
      "args": [
        "-m",
        "mcp-server.mcp_server"
      ],
      "cwd": "/full/path/to/n8n-flow-gen-mcp"
    }
  }
}
```

Replace `/full/path/to/n8n-flow-gen-mcp` with the actual path to this directory.

3. **Add to Claude Code global configuration:**
```bash
# Copy your .mcp.json to Claude Code's config directory
cp .mcp.json ~/.claude/.mcp.json
```

### For Other MCP Clients

Refer to your MCP client's documentation for configuration. The server can be started with:
```bash
python -m mcp-server.mcp_server
```

## Step 4: Test Installation

1. **Test MCP server directly:**
```bash
cd /path/to/n8n-flow-gen-mcp
python -m mcp-server.mcp_server
```

2. **Test with Claude Code:**
```bash
claude
```

Then try generating a workflow:
```
Create a simple webhook workflow that responds with "Hello World"
```

## Step 5: Verify n8n Connection

The server will automatically test the n8n connection on startup. Check for:

- ✅ n8n API connection successful
- ✅ API key validation passed
- ✅ Workflow operations available

## Troubleshooting

### Common Issues

**1. "N8N_API_KEY not found"**
- Ensure `.env` file exists and contains your API key
- Check the key is not wrapped in quotes

**2. "Connection refused to n8n"**
- Verify n8n is running and accessible
- Check the `N8N_HOST` URL is correct
- Ensure firewall/network allows connections

**3. "MCP server not starting"**
- Check Python version: `python --version` (must be 3.12+)
- Verify uv installation: `uv --version`
- Run `uv sync` to ensure dependencies are installed

**4. "Module not found"**
- Ensure you're in the correct directory
- Run `uv sync` to install dependencies
- Check the path in `.mcp.json` is absolute and correct

### Debug Mode

Enable debug logging by setting in `.env`:
```bash
DEBUG=true
LOG_LEVEL=debug
```

This will provide detailed output about API calls and operations.

### API Key Permissions

Ensure your n8n API key has the following permissions:
- Read workflows
- Write workflows
- Activate/deactivate workflows
- Read workflow executions

## Advanced Configuration

### Custom n8n Endpoints

For custom n8n deployments, you may need to adjust endpoints:

```bash
# In .env file
N8N_HOST=https://your-n8n-instance.com
N8N_API_KEY=your_key_here
```

### Workflow Defaults

Configure default workflow settings:

```bash
# In .env file
DEFAULT_WORKFLOW_ACTIVE=true
DEFAULT_WORKFLOW_SETTINGS={"timezone": "UTC"}
```

## Next Steps

Once installed, you can:

1. **Generate workflows** using natural language descriptions
2. **Validate workflows** before deploying
3. **Manage nodes and connections** programmatically
4. **Batch operations** for complex workflow management

See the main [README.md](README.md) for usage examples and available tools.

## Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review the [README.md](README.md) for usage examples
3. Submit an issue on GitHub with:
   - Your operating system
   - Python version
   - n8n version
   - Error messages and logs