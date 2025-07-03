#!/usr/bin/env node
// Example: Deploy a workflow to n8n using the API

const { N8NAPIClient } = require('../src/n8n_api_client.js');
const { N8NWorkflowBuilder } = require('../src/workflow_builder.js');

async function deployExampleWorkflow() {
  try {
    // Create a simple workflow
    const builder = new N8NWorkflowBuilder('API Test Workflow');
    
    // Add webhook trigger
    const webhookNode = builder.addNode(
      'n8n-nodes-base.webhook',
      'Webhook',
      {
        httpMethod: 'POST',
        path: 'api-test',
        options: {}
      }
    );
    
    // Add response node
    const responseNode = builder.addNode(
      'n8n-nodes-base.respondToWebhook',
      'Respond',
      {
        options: {
          responseCode: 200,
          responseData: 'success',
          responseHeaders: {}
        }
      }
    );
    
    // Connect nodes
    builder.connectNodes(webhookNode, responseNode);
    
    // Get workflow JSON
    const workflowJSON = JSON.parse(builder.export());
    
    // Deploy to n8n
    console.log('🚀 Deploying workflow to n8n...');
    const client = new N8NAPIClient();
    const result = await client.createWorkflow(workflowJSON);
    
    console.log('✅ Workflow deployed successfully!');
    console.log(`   ID: ${result.id}`);
    console.log(`   Name: ${result.name}`);
    console.log(`   URL: ${process.env.N8N_HOST}/workflow/${result.id}`);
    
  } catch (error) {
    console.error('❌ Deployment failed:', error.message);
  }
}

// Run if called directly
if (require.main === module) {
  deployExampleWorkflow();
}

module.exports = { deployExampleWorkflow };