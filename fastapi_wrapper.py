#!/usr/bin/env python3
"""
FastAPI REST Wrapper for Xiaomi Jobs MCP Server

This creates a REST API that wraps the MCP server functionality,
making it accessible via HTTP endpoints.

Usage:
    pip install fastapi uvicorn
    python fastapi_wrapper.py
    
Then visit: http://localhost:8000/docs for interactive API documentation
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Import our direct API class
from a2a_sample import XiaomiJobsDirectAPI

app = FastAPI(
    title="Xiaomi Jobs API",
    description="REST API wrapper for Xiaomi Jobs search functionality",
    version="1.0.0"
)

# Initialize direct API client
jobs_api = XiaomiJobsDirectAPI()

# Pydantic models for request/response
class JobSearchRequest(BaseModel):
    keyword: str = ""
    limit: int = 10
    offset: int = 0
    location_codes: Optional[List[str]] = None

class JobSearchResponse(BaseModel):
    success: bool
    total_count: int
    jobs: List[Dict[str, Any]]
    message: Optional[str] = None

class WebhookRequest(BaseModel):
    keyword: str
    webhook_url: str
    check_interval_minutes: int = 60

# In-memory storage for webhooks (in production, use a database)
active_webhooks = []

@app.get("/", response_class=HTMLResponse)
async def root():
    """API documentation homepage"""
    return """
    <html>
        <head>
            <title>Xiaomi Jobs API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { color: #fff; padding: 2px 8px; border-radius: 3px; font-weight: bold; }
                .get { background: #61affe; }
                .post { background: #49cc90; }
            </style>
        </head>
        <body>
            <h1>🚀 Xiaomi Jobs API</h1>
            <p>REST API wrapper for Xiaomi Jobs search functionality</p>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/jobs/search</strong>
                <p>Search for jobs with query parameters</p>
                <p>Example: <code>/jobs/search?keyword=python&limit=5</code></p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/jobs/search</strong>
                <p>Search for jobs with JSON payload</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/jobs/trending</strong>
                <p>Get trending job categories</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <strong>/webhooks/register</strong>
                <p>Register a webhook for job alerts</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <strong>/webhooks</strong>
                <p>List active webhooks</p>
            </div>
            
            <p><a href="/docs">📖 Interactive API Documentation</a></p>
            <p><a href="/redoc">📋 ReDoc Documentation</a></p>
        </body>
    </html>
    """

@app.get("/jobs/search")
async def search_jobs_get(
    keyword: str = "",
    limit: int = 10,
    offset: int = 0,
    location_codes: Optional[str] = None
):
    """Search for jobs using GET parameters"""
    
    # Parse location codes if provided
    location_list = None
    if location_codes:
        location_list = [code.strip() for code in location_codes.split(",")]
    
    return await search_jobs_internal(
        keyword=keyword,
        limit=limit,
        offset=offset,
        location_codes=location_list
    )

@app.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs_post(request: JobSearchRequest):
    """Search for jobs using POST with JSON payload"""
    
    return await search_jobs_internal(
        keyword=request.keyword,
        limit=request.limit,
        offset=request.offset,
        location_codes=request.location_codes
    )

async def search_jobs_internal(
    keyword: str = "",
    limit: int = 10,
    offset: int = 0,
    location_codes: Optional[List[str]] = None
) -> JobSearchResponse:
    """Internal job search function"""
    
    try:
        # Call the direct API
        results = jobs_api.search_jobs(keyword=keyword, limit=limit)
        
        if results.get("error"):
            return JobSearchResponse(
                success=False,
                total_count=0,
                jobs=[],
                message=results["error"]
            )
        
        if results.get("code") != 0:
            return JobSearchResponse(
                success=False,
                total_count=0,
                jobs=[],
                message=results.get("message", "API error")
            )
        
        # Extract job data
        data = results.get("data", {})
        job_posts = data.get("job_post_list", [])
        total_count = data.get("count", len(job_posts))
        
        # Format jobs for response
        formatted_jobs = []
        for job in job_posts:
            formatted_job = {
                "id": job.get("id"),
                "title": job.get("title"),
                "code": job.get("code"),
                "description": job.get("description", "")[:200] + "..." if job.get("description", "") else "",
                "requirements": job.get("requirement", "")[:200] + "..." if job.get("requirement", "") else "",
                "recruit_type": job.get("recruit_type"),
                "url": f"https://xiaomi.jobs.f.mioffice.cn/index/position/{job.get('id', '')}/detail",
                "locations": []
            }
            
            # Handle locations
            if job.get('city_info'):
                city_info = job['city_info']
                if isinstance(city_info, dict):
                    formatted_job["locations"].append(city_info.get('name', str(city_info)))
                else:
                    formatted_job["locations"].append(str(city_info))
            elif job.get('city_list'):
                for city in job['city_list']:
                    if isinstance(city, dict):
                        formatted_job["locations"].append(city.get('name', str(city)))
                    else:
                        formatted_job["locations"].append(str(city))
            
            formatted_jobs.append(formatted_job)
        
        return JobSearchResponse(
            success=True,
            total_count=total_count,
            jobs=formatted_jobs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/jobs/trending")
async def get_trending_jobs():
    """Get trending job categories by searching popular keywords"""
    
    trending_keywords = ["AI", "python", "engineer", "developer", "manager"]
    trending_data = {}
    
    for keyword in trending_keywords:
        try:
            results = jobs_api.search_jobs(keyword=keyword, limit=5)
            if results.get("data", {}).get("count"):
                trending_data[keyword] = {
                    "count": results["data"]["count"],
                    "sample_jobs": [
                        {
                            "title": job.get("title"),
                            "code": job.get("code")
                        }
                        for job in results["data"]["job_post_list"][:3]
                    ]
                }
        except Exception:
            continue
    
    return {
        "success": True,
        "trending_keywords": trending_data,
        "generated_at": datetime.now().isoformat()
    }

@app.post("/webhooks/register")
async def register_webhook(request: WebhookRequest, background_tasks: BackgroundTasks):
    """Register a webhook for job alerts"""
    
    webhook = {
        "id": len(active_webhooks) + 1,
        "keyword": request.keyword,
        "webhook_url": request.webhook_url,
        "check_interval_minutes": request.check_interval_minutes,
        "created_at": datetime.now().isoformat(),
        "last_check": None,
        "total_notifications": 0
    }
    
    active_webhooks.append(webhook)
    
    # Start background task to check this webhook
    background_tasks.add_task(start_webhook_monitoring, webhook)
    
    return {
        "success": True,
        "webhook_id": webhook["id"],
        "message": f"Webhook registered for keyword '{request.keyword}'"
    }

@app.get("/webhooks")
async def list_webhooks():
    """List all active webhooks"""
    return {
        "success": True,
        "active_webhooks": active_webhooks,
        "total_count": len(active_webhooks)
    }

@app.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: int):
    """Delete a webhook"""
    global active_webhooks
    
    webhook = next((w for w in active_webhooks if w["id"] == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    active_webhooks = [w for w in active_webhooks if w["id"] != webhook_id]
    
    return {
        "success": True,
        "message": f"Webhook {webhook_id} deleted"
    }

async def start_webhook_monitoring(webhook: Dict[str, Any]):
    """Background task to monitor webhook and send notifications"""
    
    # This is a simplified example - in production you'd use a proper task queue
    # like Celery or run this as a separate service
    
    import time
    import requests
    
    while webhook in active_webhooks:
        try:
            # Search for jobs
            results = jobs_api.search_jobs(keyword=webhook["keyword"], limit=5)
            
            if results.get("data", {}).get("job_post_list"):
                jobs = results["data"]["job_post_list"]
                
                # Prepare webhook payload
                payload = {
                    "webhook_id": webhook["id"],
                    "keyword": webhook["keyword"],
                    "new_jobs_count": len(jobs),
                    "jobs": [
                        {
                            "title": job.get("title"),
                            "code": job.get("code"),
                            "url": f"https://xiaomi.jobs.f.mioffice.cn/index/position/{job.get('id', '')}/detail"
                        }
                        for job in jobs[:3]
                    ],
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send webhook notification (in a real app, you'd handle failures, retries, etc.)
                try:
                    response = requests.post(
                        webhook["webhook_url"],
                        json=payload,
                        timeout=10,
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code == 200:
                        webhook["total_notifications"] += 1
                except Exception as e:
                    print(f"Webhook notification failed: {e}")
            
            webhook["last_check"] = datetime.now().isoformat()
            
            # Wait for next check
            await asyncio.sleep(webhook["check_interval_minutes"] * 60)
            
        except Exception as e:
            print(f"Webhook monitoring error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_webhooks": len(active_webhooks)
    }

if __name__ == "__main__":
    print("🚀 Starting Xiaomi Jobs FastAPI Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🏠 Homepage: http://localhost:8000/")
    
    uvicorn.run(
        "fastapi_wrapper:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
