# A2A (Application-to-Application) Integration Samples

This directory contains various integration patterns for the Xiaomi Jobs MCP Server, demonstrating how different applications can interact with the job search functionality.

## 🚀 Available Integration Patterns

### 1. Direct API Integration (`a2a_sample.py`)

**Pattern**: Bypass MCP, call Xiaomi API directly

- ✅ **Pros**: Fastest performance, minimal overhead
- ❌ **Cons**: No MCP benefits (standardization, tooling)
- **Use Case**: High-performance applications, simple integrations

```python
from a2a_sample import XiaomiJobsDirectAPI

api = XiaomiJobsDirectAPI()
results = api.search_jobs(keyword="python", limit=5)
```

### 2. MCP Client Integration (`a2a_sample.py`)

**Pattern**: Communicate with MCP server via JSON-RPC protocol

- ✅ **Pros**: Standardized protocol, structured communication
- ❌ **Cons**: Additional overhead, subprocess management
- **Use Case**: Applications that need MCP protocol compliance

```python
from a2a_sample import XiaomiJobsMCPClient

client = XiaomiJobsMCPClient("./xiaomi_jobs_mcp.py")
results = await client.search_jobs_via_mcp(keyword="engineer", limit=3)
```

### 3. REST API Wrapper (`fastapi_wrapper.py`)

**Pattern**: Expose MCP functionality as HTTP REST endpoints

- ✅ **Pros**: Web-friendly, language-agnostic, scalable
- ❌ **Cons**: Network overhead, requires web server
- **Use Case**: Web applications, microservices, external integrations

```bash
# Start the REST API server
python fastapi_wrapper.py

# Use the API
curl "http://localhost:8000/jobs/search?keyword=python&limit=5"
```

### 4. Webhook/Event-driven Integration (`a2a_sample.py`)

**Pattern**: Register webhooks for job alerts and notifications

- ✅ **Pros**: Event-driven, real-time notifications, scalable
- ❌ **Cons**: Complex setup, requires webhook endpoints
- **Use Case**: Job alert systems, monitoring, automation

```python
from a2a_sample import JobAlertSystem

alert_system = JobAlertSystem(direct_api)
alert_system.add_alert("AI engineer", "https://your-app.com/webhook")
await alert_system.check_alerts()
```

### 5. Google A2A (Agent2Agent) Protocol Sample

The **Google A2A Protocol** is an open standard for agent-to-agent communication that enables AI agents from different vendors to collaborate securely and effectively.

#### What is Google A2A?

Google's Agent2Agent (A2A) protocol addresses the challenge of enabling AI agents built on diverse frameworks by different companies to communicate and collaborate as agents, not just tools. Key features include:

- **Agent Discovery**: Via "Agent Cards" describing capabilities
- **Task-based Collaboration**: Structured task lifecycle management
- **Secure Communication**: JSON-RPC 2.0 over HTTP with enterprise authentication
- **Long-running Tasks**: Support for complex, multi-step operations
- **Modality Agnostic**: Text, audio, video, and structured data support

#### Running the Google A2A Sample

```bash
# Install A2A SDK
pip install a2a-sdk

# Run the A2A agent server
python google_a2a_sample.py

# Or run the demo
python google_a2a_sample.py demo
```

The A2A agent will be available at:

- **Agent Card**: http://localhost:8001/agent-card
- **Root**: http://localhost:8001/
- **Task Creation**: POST http://localhost:8001/task
- **Task Status**: GET http://localhost:8001/task/{task_id}/status

#### A2A Agent Capabilities

The Xiaomi Jobs A2A agent exposes these skills:

1. **search_jobs**: Search for job postings by keywords and criteria
2. **analyze_job_market**: Analyze job market trends and insights
3. **get_job_recommendations**: Provide personalized job recommendations

#### Example A2A Task Request

```json
{
  "task_id": "uuid-here",
  "instruction": "Search for Python developer jobs at Xiaomi",
  "context": {
    "keyword": "python",
    "limit": 5
  },
  "user_id": "demo_user"
}
```

#### A2A vs Other Integration Patterns

| Pattern        | Use Case                     | Pros                                | Cons                                          |
| -------------- | ---------------------------- | ----------------------------------- | --------------------------------------------- |
| **Google A2A** | Agent-to-agent collaboration | Standardized, secure, task-oriented | Newer protocol, requires A2A-compliant agents |
| **Direct API** | Simple integration           | Fast, direct                        | No standardization                            |
| **MCP Client** | Tool-based integration       | Structured, MCP ecosystem           | Limited to tool paradigm                      |
| **REST API**   | Web service integration      | Universal, well-known               | Not agent-specific                            |

#### Learn More

- [A2A Protocol Documentation](https://goo.gle/a2a)
- [A2A GitHub Repository](https://github.com/a2aproject/A2A)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)

## 🛠️ Setup and Installation

### Prerequisites

```bash
# Ensure you're in the job-xiaomi conda environment
conda activate job-xiaomi

# Install dependencies
pip install -r requirements.txt
```

### Running the Samples

#### 1. Basic A2A Demo

```bash
python a2a_sample.py
```

#### 2. FastAPI REST Server

```bash
python fastapi_wrapper.py
```

Then visit:

- **Homepage**: http://localhost:8000/
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 3. Test REST API Endpoints

```bash
# Search jobs via GET
curl "http://localhost:8000/jobs/search?keyword=python&limit=3"

# Search jobs via POST
curl -X POST "http://localhost:8000/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "engineer", "limit": 5}'

# Get trending jobs
curl "http://localhost:8000/jobs/trending"

# Register a webhook
curl -X POST "http://localhost:8000/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "AI", "webhook_url": "https://your-app.com/webhook"}'
```

## 📊 Integration Comparison

| Pattern      | Performance | Complexity | Scalability | Use Case                     |
| ------------ | ----------- | ---------- | ----------- | ---------------------------- |
| Direct API   | ⭐⭐⭐⭐⭐  | ⭐⭐       | ⭐⭐⭐      | Simple, fast apps            |
| MCP Client   | ⭐⭐⭐      | ⭐⭐⭐⭐   | ⭐⭐⭐      | MCP-compliant apps           |
| REST Wrapper | ⭐⭐⭐      | ⭐⭐⭐     | ⭐⭐⭐⭐⭐  | Web apps, APIs               |
| Webhooks     | ⭐⭐⭐⭐    | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐  | Event-driven systems         |
| Google A2A   | ⭐⭐⭐      | ⭐⭐⭐⭐   | ⭐⭐⭐⭐⭐  | Agent-to-agent collaboration |

## 🔧 Customization

### Adding New Endpoints (REST API)

Edit `fastapi_wrapper.py` and add new endpoints:

```python
@app.get("/jobs/by-location/{location}")
async def get_jobs_by_location(location: str):
    # Your implementation here
    pass
```

### Custom Webhook Handlers

Modify the `JobAlertSystem` class in `a2a_sample.py`:

```python
def add_custom_alert(self, criteria: dict, webhook_url: str):
    # Custom alert logic
    pass
```

### MCP Protocol Extensions

Extend the MCP client to support additional tools:

```python
# Add new tool calls to xiaomi_jobs_mcp.py
@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "your_new_tool":
        # Implementation
        pass
```

## 🚦 Production Considerations

### Security

- Add API authentication (JWT, API keys)
- Implement rate limiting
- Validate and sanitize inputs
- Use HTTPS in production

### Scalability

- Use proper database for webhook storage
- Implement job queues (Celery, RQ) for background tasks
- Add caching (Redis) for frequent queries
- Use load balancers for multiple instances

### Monitoring

- Add logging and metrics
- Implement health checks
- Set up error tracking (Sentry)
- Monitor API performance

### Example Production Setup

```python
# Add to fastapi_wrapper.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)
```

## 📝 API Documentation

### REST API Endpoints

#### Job Search

- `GET /jobs/search` - Search with query parameters
- `POST /jobs/search` - Search with JSON payload

#### Trending

- `GET /jobs/trending` - Get trending job categories

#### Webhooks

- `POST /webhooks/register` - Register job alert webhook
- `GET /webhooks` - List active webhooks
- `DELETE /webhooks/{id}` - Delete webhook

#### System

- `GET /health` - Health check
- `GET /` - API documentation homepage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your integration pattern
4. Update this README
5. Submit a pull request

## 📄 License

This project is part of the job-xiaomi MCP server implementation.
