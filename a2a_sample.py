#!/usr/bin/env python3
"""
A2A (Application-to-Application) Sample for Xiaomi Jobs MCP Server

This sample demonstrates different integration patterns:
1. Direct API integration (bypassing MCP)
2. MCP client integration (using MCP protocol)
3. REST API wrapper (exposing MCP as REST API)
4. Webhook integration (event-driven)
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
import requests
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XiaomiJobsDirectAPI:
    """Direct API integration - bypasses MCP, calls Xiaomi API directly"""
    
    def __init__(self):
        self.base_url = "https://xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "content-type": "application/json",
            "origin": "https://xiaomi.jobs.f.mioffice.cn",
            "referer": "https://xiaomi.jobs.f.mioffice.cn/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    def search_jobs(self, keyword: str = "", limit: int = 5) -> Dict[str, Any]:
        """Search jobs directly via Xiaomi API"""
        payload = {
            "keyword": keyword,
            "limit": limit,
            "offset": 0,
            "job_category_id_list": [],
            "tag_id_list": [],
            "location_code_list": [],
            "subject_id_list": [],
            "recruitment_id_list": [],
            "portal_type": 6,
            "job_function_id_list": [],
            "storefront_id_list": [],
            "portal_entrance": 1
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

class XiaomiJobsMCPClient:
    """MCP client integration - communicates with MCP server via subprocess"""
    
    def __init__(self, mcp_script_path: str):
        self.mcp_script_path = mcp_script_path
    
    async def search_jobs_via_mcp(self, keyword: str = "", limit: int = 5) -> str:
        """Search jobs via MCP server"""
        try:
            # Create MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search_xiaomi_jobs",
                    "arguments": {
                        "keyword": keyword,
                        "limit": limit
                    }
                }
            }
            
            # Start MCP server process
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.mcp_script_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send initialization request first
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "a2a-sample", "version": "1.0.0"}
                }
            }
            
            # Send requests
            init_json = json.dumps(init_request) + '\n'
            request_json = json.dumps(mcp_request) + '\n'
            
            stdout, stderr = await process.communicate(
                input=(init_json + request_json).encode()
            )
            
            if process.returncode != 0:
                return f"MCP Error: {stderr.decode()}"
            
            # Parse response
            lines = stdout.decode().strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        response = json.loads(line)
                        if response.get('id') == 1 and 'result' in response:
                            content = response['result']['content']
                            if content and len(content) > 0:
                                return content[0]['text']
                    except json.JSONDecodeError:
                        continue
            
            return "No valid response from MCP server"
            
        except Exception as e:
            return f"MCP Client Error: {str(e)}"

class XiaomiJobsRESTWrapper:
    """REST API wrapper - exposes MCP functionality as REST endpoints"""
    
    def __init__(self, mcp_client: XiaomiJobsMCPClient):
        self.mcp_client = mcp_client
    
    async def create_rest_server(self, port: int = 8080):
        """Create a simple REST server (conceptual - would need Flask/FastAPI)"""
        # This is a conceptual example - in practice you'd use Flask or FastAPI
        rest_endpoints = {
            "GET /jobs": "Search jobs with query parameters",
            "POST /jobs/search": "Search jobs with JSON payload",
            "GET /jobs/{job_id}": "Get specific job details",
            "POST /webhooks/job-alerts": "Register webhook for job alerts"
        }
        
        logger.info(f"REST API would be available at http://localhost:{port}")
        logger.info("Available endpoints:")
        for endpoint, description in rest_endpoints.items():
            logger.info(f"  {endpoint} - {description}")
        
        return rest_endpoints

class JobAlertSystem:
    """Webhook/Event-driven integration example"""
    
    def __init__(self, direct_api: XiaomiJobsDirectAPI):
        self.direct_api = direct_api
        self.alerts = []
        self.last_check = datetime.now()
    
    def add_alert(self, keyword: str, webhook_url: str):
        """Add a job alert"""
        alert = {
            "id": len(self.alerts) + 1,
            "keyword": keyword,
            "webhook_url": webhook_url,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None
        }
        self.alerts.append(alert)
        logger.info(f"Added job alert for '{keyword}' -> {webhook_url}")
        return alert
    
    async def check_alerts(self):
        """Check for new jobs matching alerts"""
        logger.info("Checking job alerts...")
        
        for alert in self.alerts:
            try:
                # Search for jobs matching the alert keyword
                results = self.direct_api.search_jobs(
                    keyword=alert["keyword"], 
                    limit=3
                )
                
                if results.get("data", {}).get("job_post_list"):
                    jobs = results["data"]["job_post_list"]
                    
                    # Simulate webhook notification
                    webhook_payload = {
                        "alert_id": alert["id"],
                        "keyword": alert["keyword"],
                        "new_jobs_count": len(jobs),
                        "jobs": [
                            {
                                "title": job.get("title"),
                                "code": job.get("code"),
                                "url": f"https://xiaomi.jobs.f.mioffice.cn/index/position/{job.get('id', '')}/detail"
                            }
                            for job in jobs[:2]  # Send top 2 jobs
                        ],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # In a real implementation, you'd POST to the webhook_url
                    logger.info(f"🔔 Alert triggered for '{alert['keyword']}':")
                    logger.info(f"   Found {len(jobs)} jobs")
                    logger.info(f"   Would POST to: {alert['webhook_url']}")
                    logger.info(f"   Payload: {json.dumps(webhook_payload, indent=2)}")
                    
                    alert["last_triggered"] = datetime.now().isoformat()
                
            except Exception as e:
                logger.error(f"Error checking alert {alert['id']}: {e}")

async def demonstrate_integrations():
    """Demonstrate different A2A integration patterns"""
    
    print("🚀 Xiaomi Jobs A2A Integration Samples")
    print("=" * 50)
    
    # 1. Direct API Integration
    print("\n1️⃣ Direct API Integration")
    print("-" * 30)
    direct_api = XiaomiJobsDirectAPI()
    direct_results = direct_api.search_jobs(keyword="python", limit=3)
    
    if direct_results.get("data", {}).get("job_post_list"):
        jobs = direct_results["data"]["job_post_list"]
        print(f"✅ Found {len(jobs)} Python jobs via direct API")
        for job in jobs[:2]:
            print(f"   • {job.get('title', 'N/A')} ({job.get('code', 'N/A')})")
    else:
        print("❌ No jobs found via direct API")
    
    # 2. MCP Client Integration
    print("\n2️⃣ MCP Client Integration")
    print("-" * 30)
    mcp_script = Path(__file__).parent / "xiaomi_jobs_mcp.py"
    if mcp_script.exists():
        mcp_client = XiaomiJobsMCPClient(str(mcp_script))
        mcp_results = await mcp_client.search_jobs_via_mcp(keyword="engineer", limit=3)
        print("✅ MCP Client Results:")
        print(mcp_results[:200] + "..." if len(mcp_results) > 200 else mcp_results)
    else:
        print("❌ MCP script not found")
    
    # 3. REST API Wrapper
    print("\n3️⃣ REST API Wrapper")
    print("-" * 30)
    if 'mcp_client' in locals():
        rest_wrapper = XiaomiJobsRESTWrapper(mcp_client)
        endpoints = await rest_wrapper.create_rest_server(port=8080)
        print("✅ REST API endpoints defined")
    else:
        print("❌ MCP client not available for REST wrapper")
    
    # 4. Webhook/Event-driven Integration
    print("\n4️⃣ Webhook/Event-driven Integration")
    print("-" * 30)
    alert_system = JobAlertSystem(direct_api)
    
    # Add some sample alerts
    alert_system.add_alert("AI engineer", "https://example.com/webhook/ai-jobs")
    alert_system.add_alert("backend developer", "https://example.com/webhook/backend-jobs")
    
    # Check alerts
    await alert_system.check_alerts()
    
    print("\n🎉 A2A Integration Demo Complete!")
    print("\nIntegration Patterns Summary:")
    print("• Direct API: Fastest, but bypasses MCP benefits")
    print("• MCP Client: Uses MCP protocol, more structured")
    print("• REST Wrapper: Exposes MCP as web API")
    print("• Webhooks: Event-driven, great for notifications")

if __name__ == "__main__":
    asyncio.run(demonstrate_integrations())
