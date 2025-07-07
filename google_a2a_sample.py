#!/usr/bin/env python3
"""
Google A2A (Agent2Agent) Protocol Sample for Xiaomi Jobs MCP Server

This sample demonstrates how to expose the Xiaomi Jobs functionality as an A2A-compliant agent
that can communicate with other agents using Google's Agent2Agent protocol.

The A2A protocol enables:
- Agent discovery via Agent Cards
- Task-based collaboration between agents
- Secure communication using JSON-RPC 2.0 over HTTP
- Support for long-running tasks and streaming responses

Installation:
    pip install a2a-sdk fastapi uvicorn

Usage:
    python google_a2a_sample.py
    
Then the agent will be available at: http://localhost:8001
Agent Card: http://localhost:8001/agent-card
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our existing Xiaomi Jobs API
from a2a_sample import XiaomiJobsDirectAPI

# A2A Protocol Models
class AgentCard(BaseModel):
    """A2A Agent Card - describes the agent's capabilities"""
    name: str
    description: str
    version: str
    capabilities: List[str]
    skills: List[Dict[str, Any]]
    contact_info: Dict[str, str]
    authentication: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    """A2A Task Request"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instruction: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    priority: Optional[str] = "normal"
    expected_completion_time: Optional[str] = None

class TaskStatus(BaseModel):
    """A2A Task Status"""
    task_id: str
    status: str  # "pending", "in_progress", "completed", "failed", "cancelled"
    progress: Optional[float] = None  # 0.0 to 1.0
    message: Optional[str] = None
    artifacts: Optional[List[Dict[str, Any]]] = None
    created_at: str
    updated_at: str

class A2AMessage(BaseModel):
    """A2A Protocol Message"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    sender: str
    recipient: str
    content: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class XiaomiJobsA2AAgent:
    """Xiaomi Jobs Agent implementing Google's A2A Protocol"""
    
    def __init__(self):
        self.agent_name = "xiaomi-jobs-agent"
        self.version = "1.0.0"
        self.jobs_api = XiaomiJobsDirectAPI()
        self.active_tasks: Dict[str, TaskStatus] = {}
        
        # Define agent capabilities and skills
        self.agent_card = AgentCard(
            name="Xiaomi Jobs Search Agent",
            description="An AI agent specialized in searching and analyzing Xiaomi job postings. Can find jobs by keywords, locations, and categories, and provide detailed job information including requirements and descriptions.",
            version=self.version,
            capabilities=[
                "job_search",
                "job_analysis", 
                "career_guidance",
                "market_insights"
            ],
            skills=[
                {
                    "name": "search_jobs",
                    "description": "Search for job postings at Xiaomi based on keywords, location, and other criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "Search keyword for job titles or descriptions"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            },
                            "location_codes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of location codes to filter by"
                            }
                        }
                    }
                },
                {
                    "name": "analyze_job_market",
                    "description": "Analyze job market trends and provide insights about specific roles or skills",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "role_type": {
                                "type": "string",
                                "description": "Type of role to analyze (e.g., 'engineer', 'manager', 'designer')"
                            },
                            "skills": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific skills to analyze demand for"
                            }
                        }
                    }
                },
                {
                    "name": "get_job_recommendations",
                    "description": "Get personalized job recommendations based on user profile and preferences",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "experience_level": {
                                "type": "string",
                                "enum": ["entry", "mid", "senior", "executive"],
                                "description": "Experience level of the candidate"
                            },
                            "preferred_skills": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Skills the candidate wants to use"
                            },
                            "location_preference": {
                                "type": "string",
                                "description": "Preferred work location"
                            }
                        }
                    }
                }
            ],
            contact_info={
                "endpoint": "http://localhost:8001",
                "protocol": "A2A",
                "supported_methods": ["task_request", "task_status", "message"]
            }
        )
    
    async def process_task(self, task_request: TaskRequest) -> TaskStatus:
        """Process an A2A task request"""
        
        # Create initial task status
        task_status = TaskStatus(
            task_id=task_request.task_id,
            status="in_progress",
            progress=0.0,
            message="Processing job search request...",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.active_tasks[task_request.task_id] = task_status
        
        try:
            # Parse the instruction to determine what action to take
            instruction = task_request.instruction.lower()
            context = task_request.context or {}
            
            if "search" in instruction or "find jobs" in instruction:
                result = await self._handle_job_search(instruction, context)
            elif "analyze" in instruction or "market" in instruction:
                result = await self._handle_market_analysis(instruction, context)
            elif "recommend" in instruction or "suggest" in instruction:
                result = await self._handle_job_recommendations(instruction, context)
            else:
                result = await self._handle_general_query(instruction, context)
            
            # Update task status with results
            task_status.status = "completed"
            task_status.progress = 1.0
            task_status.message = "Task completed successfully"
            task_status.artifacts = [result]
            task_status.updated_at = datetime.now().isoformat()
            
        except Exception as e:
            task_status.status = "failed"
            task_status.message = f"Task failed: {str(e)}"
            task_status.updated_at = datetime.now().isoformat()
        
        return task_status
    
    async def _handle_job_search(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle job search requests"""
        
        # Extract search parameters from instruction and context
        keyword = context.get("keyword", "")
        limit = context.get("limit", 10)
        
        # Try to extract keyword from instruction if not in context
        if not keyword:
            # Simple keyword extraction (in production, use NLP)
            words = instruction.split()
            for i, word in enumerate(words):
                if word in ["for", "about", "in"] and i + 1 < len(words):
                    keyword = words[i + 1]
                    break
        
        # Search for jobs
        results = self.jobs_api.search_jobs(keyword=keyword, limit=limit)
        
        if results.get("error"):
            raise Exception(results["error"])
        
        # Format results for A2A
        jobs_data = results.get("data", {})
        job_posts = jobs_data.get("job_post_list", [])
        
        formatted_jobs = []
        for job in job_posts:
            formatted_job = {
                "id": job.get("id"),
                "title": job.get("title"),
                "code": job.get("code"),
                "description": job.get("description", "")[:300] + "..." if job.get("description") else "",
                "requirements": job.get("requirement", "")[:300] + "..." if job.get("requirement") else "",
                "type": job.get("recruit_type"),
                "url": f"https://xiaomi.jobs.f.mioffice.cn/index/position/{job.get('id', '')}/detail",
                "locations": self._extract_locations(job)
            }
            formatted_jobs.append(formatted_job)
        
        return {
            "type": "job_search_results",
            "content": {
                "query": keyword,
                "total_count": jobs_data.get("count", len(job_posts)),
                "jobs": formatted_jobs,
                "search_timestamp": datetime.now().isoformat()
            },
            "format": "application/json"
        }
    
    async def _handle_market_analysis(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle market analysis requests"""
        
        # Analyze different job categories
        categories = ["AI", "engineer", "developer", "manager", "designer"]
        analysis_results = {}
        
        for category in categories:
            try:
                results = self.jobs_api.search_jobs(keyword=category, limit=5)
                if results.get("data", {}).get("count"):
                    analysis_results[category] = {
                        "total_jobs": results["data"]["count"],
                        "sample_titles": [
                            job.get("title", "N/A") 
                            for job in results["data"]["job_post_list"][:3]
                        ]
                    }
            except Exception:
                continue
        
        return {
            "type": "market_analysis",
            "content": {
                "analysis_date": datetime.now().isoformat(),
                "job_categories": analysis_results,
                "insights": [
                    f"Found {sum(cat.get('total_jobs', 0) for cat in analysis_results.values())} total jobs across analyzed categories",
                    f"Most active category: {max(analysis_results.keys(), key=lambda k: analysis_results[k].get('total_jobs', 0)) if analysis_results else 'N/A'}",
                    "Analysis based on current Xiaomi job postings"
                ]
            },
            "format": "application/json"
        }
    
    async def _handle_job_recommendations(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle job recommendation requests"""
        
        experience_level = context.get("experience_level", "mid")
        preferred_skills = context.get("preferred_skills", ["python", "AI"])
        
        recommendations = []
        
        # Search for jobs matching preferred skills
        for skill in preferred_skills[:3]:  # Limit to top 3 skills
            try:
                results = self.jobs_api.search_jobs(keyword=skill, limit=3)
                if results.get("data", {}).get("job_post_list"):
                    for job in results["data"]["job_post_list"]:
                        recommendations.append({
                            "title": job.get("title"),
                            "code": job.get("code"),
                            "matching_skill": skill,
                            "url": f"https://xiaomi.jobs.f.mioffice.cn/index/position/{job.get('id', '')}/detail",
                            "locations": self._extract_locations(job)
                        })
            except Exception:
                continue
        
        return {
            "type": "job_recommendations",
            "content": {
                "user_profile": {
                    "experience_level": experience_level,
                    "preferred_skills": preferred_skills
                },
                "recommendations": recommendations[:10],  # Top 10 recommendations
                "recommendation_timestamp": datetime.now().isoformat()
            },
            "format": "application/json"
        }
    
    async def _handle_general_query(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general queries about Xiaomi jobs"""
        
        # Default to a general search
        results = self.jobs_api.search_jobs(keyword="", limit=5)
        
        return {
            "type": "general_info",
            "content": {
                "message": "Here's some general information about current Xiaomi job opportunities",
                "total_jobs": results.get("data", {}).get("count", 0),
                "sample_jobs": [
                    {
                        "title": job.get("title"),
                        "code": job.get("code")
                    }
                    for job in results.get("data", {}).get("job_post_list", [])[:5]
                ],
                "query_timestamp": datetime.now().isoformat()
            },
            "format": "application/json"
        }
    
    def _extract_locations(self, job: Dict[str, Any]) -> List[str]:
        """Extract location information from job data"""
        locations = []
        
        if job.get('city_info'):
            city_info = job['city_info']
            if isinstance(city_info, dict):
                locations.append(city_info.get('name', str(city_info)))
            else:
                locations.append(str(city_info))
        elif job.get('city_list'):
            for city in job['city_list']:
                if isinstance(city, dict):
                    locations.append(city.get('name', str(city)))
                else:
                    locations.append(str(city))
        
        return locations

# FastAPI app implementing A2A endpoints
app = FastAPI(
    title="Xiaomi Jobs A2A Agent",
    description="Google A2A Protocol compliant agent for Xiaomi job search",
    version="1.0.0"
)

# Initialize the A2A agent
a2a_agent = XiaomiJobsA2AAgent()

@app.get("/agent-card")
async def get_agent_card():
    """A2A Agent Card endpoint - describes agent capabilities"""
    return a2a_agent.agent_card.dict()

@app.post("/task")
async def create_task(task_request: TaskRequest):
    """A2A Task creation endpoint"""
    try:
        task_status = await a2a_agent.process_task(task_request)
        return task_status.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}/status")
async def get_task_status(task_id: str):
    """A2A Task status endpoint"""
    if task_id not in a2a_agent.active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return a2a_agent.active_tasks[task_id].dict()

@app.post("/message")
async def send_message(message: A2AMessage):
    """A2A Message endpoint for agent-to-agent communication"""
    # In a full implementation, this would handle inter-agent messaging
    return {
        "status": "received",
        "message_id": message.message_id,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": a2a_agent.agent_name,
        "version": a2a_agent.version,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with agent information"""
    return {
        "agent": a2a_agent.agent_name,
        "protocol": "A2A",
        "version": a2a_agent.version,
        "agent_card_url": "/agent-card",
        "endpoints": {
            "agent_card": "/agent-card",
            "create_task": "/task",
            "task_status": "/task/{task_id}/status",
            "send_message": "/message",
            "health": "/health"
        },
        "documentation": "https://goo.gle/a2a"
    }

async def demo_a2a_interaction():
    """Demonstrate A2A protocol interaction"""
    
    print("🤖 Google A2A (Agent2Agent) Protocol Demo")
    print("=" * 50)
    
    # Simulate an A2A task request
    task_request = TaskRequest(
        instruction="Search for Python developer jobs at Xiaomi",
        context={
            "keyword": "python",
            "limit": 5
        },
        user_id="demo_user"
    )
    
    print(f"\n📋 Creating A2A Task:")
    print(f"   Task ID: {task_request.task_id}")
    print(f"   Instruction: {task_request.instruction}")
    print(f"   Context: {task_request.context}")
    
    # Process the task
    task_status = await a2a_agent.process_task(task_request)
    
    print(f"\n✅ Task Completed:")
    print(f"   Status: {task_status.status}")
    print(f"   Progress: {task_status.progress * 100}%")
    print(f"   Message: {task_status.message}")
    
    if task_status.artifacts:
        artifact = task_status.artifacts[0]
        print(f"\n📊 Results:")
        print(f"   Type: {artifact['type']}")
        if artifact['type'] == 'job_search_results':
            content = artifact['content']
            print(f"   Query: {content['query']}")
            print(f"   Total Jobs: {content['total_count']}")
            print(f"   Jobs Found: {len(content['jobs'])}")
            
            for i, job in enumerate(content['jobs'][:3], 1):
                print(f"   {i}. {job['title']} ({job['code']})")
    
    print(f"\n🔗 Agent Card URL: http://localhost:8001/agent-card")
    print(f"🔗 Task Status URL: http://localhost:8001/task/{task_request.task_id}/status")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run demo
        asyncio.run(demo_a2a_interaction())
    else:
        # Start A2A server
        print("🚀 Starting Xiaomi Jobs A2A Agent Server...")
        print("📖 Agent Card: http://localhost:8001/agent-card")
        print("🏠 Root: http://localhost:8001/")
        print("📋 A2A Protocol: https://goo.gle/a2a")
        print("\nTo run demo: python google_a2a_sample.py demo")
        
        uvicorn.run(
            "google_a2a_sample:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
