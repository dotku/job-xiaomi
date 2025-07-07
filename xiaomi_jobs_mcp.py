#!/usr/bin/env python3
"""
Xiaomi Jobs MCP Server
Provides Xiaomi job search functionality as MCP tools
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
import requests
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

app = Server("xiaomi-jobs")

def xiaomi_jobs_query(
    keyword: str = "",
    limit: int = 10,
    offset: int = 0,
    location_code_list: Optional[List[str]] = None,
    job_category_id_list: Optional[List[str]] = None,
    tag_id_list: Optional[List[str]] = None,
    subject_id_list: Optional[List[str]] = None,
    recruitment_id_list: Optional[List[str]] = None,
    job_function_id_list: Optional[List[str]] = None,
    storefront_id_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Query Xiaomi jobs API with specified parameters."""
    
    url = "https://xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "content-type": "application/json",
        "origin": "https://xiaomi.jobs.f.mioffice.cn",
        "referer": "https://xiaomi.jobs.f.mioffice.cn/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    
    cookies = {
        "tt_scid": "example_scid",
        "passport_csrf_token": "example_token",
        "passport_csrf_token_default": "example_token_default"
    }
    
    payload = {
        "keyword": keyword,
        "limit": limit,
        "offset": offset,
        "job_category_id_list": job_category_id_list or [],
        "tag_id_list": tag_id_list or [],
        "location_code_list": location_code_list or [],
        "subject_id_list": subject_id_list or [],
        "recruitment_id_list": recruitment_id_list or [],
        "portal_type": 6,
        "job_function_id_list": job_function_id_list or [],
        "storefront_id_list": storefront_id_list or [],
        "portal_entrance": 1
    }
    
    try:
        response = requests.post(url, headers=headers, cookies=cookies, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def format_job_results(data: Dict[str, Any]) -> str:
    """Format job search results for display."""
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    if data.get("code") != 0:
        return f"❌ API Error: {data.get('message', 'Unknown error')}"
    
    if "data" not in data or "job_post_list" not in data["data"]:
        return "❌ No job data found in response"
    
    job_posts = data["data"]["job_post_list"]
    total_count = data["data"].get("count", len(job_posts))
    
    if len(job_posts) == 0:
        return f"📭 No job postings found (Total: {total_count})"
    
    result = [f"📋 Found {total_count} job(s), showing {len(job_posts)} results\n" + "=" * 80]
    
    for i, job in enumerate(job_posts, 1):
        job_info = [f"{i}. {job.get('title', 'N/A')}"]
        job_info.append(f"   🆔 Job Code: {job.get('code', 'N/A')}")
        
        # Handle locations
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
        
        location_str = ", ".join(locations) if locations else "N/A"
        job_info.append(f"   📍 Location: {location_str}")
        job_info.append(f"   💼 Type: {job.get('recruit_type', 'N/A')}")
        job_info.append(f"   🔗 URL: https://xiaomi.jobs.f.mioffice.cn/index/position/{job.get('id', '')}/detail")
        
        # Add description and requirements if available
        if job.get('description'):
            clean_desc = job['description'].replace('\n', ' ').replace('\r', ' ').strip()
            desc_preview = clean_desc[:150] + "..." if len(clean_desc) > 150 else clean_desc
            job_info.append(f"   📝 Description: {desc_preview}")
        
        if job.get('requirement'):
            clean_req = job['requirement'].replace('\n', ' ').replace('\r', ' ').strip()
            req_preview = clean_req[:100] + "..." if len(clean_req) > 100 else clean_req
            job_info.append(f"   📋 Requirements: {req_preview}")
        
        result.append("\n".join(job_info))
    
    return "\n\n".join(result)

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="search_xiaomi_jobs",
            description="Search for job postings on Xiaomi careers website",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword for job titles or descriptions",
                        "default": ""
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of results to skip for pagination (default: 0)",
                        "default": 0,
                        "minimum": 0
                    },
                    "location_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of location codes to filter by (e.g., ['CN_110000'] for Beijing)"
                    }
                },
                "required": []
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "search_xiaomi_jobs":
        keyword = arguments.get("keyword", "")
        limit = arguments.get("limit", 10)
        offset = arguments.get("offset", 0)
        location_codes = arguments.get("location_codes", [])
        
        # Query the API
        result = xiaomi_jobs_query(
            keyword=keyword,
            limit=limit,
            offset=offset,
            location_code_list=location_codes
        )
        
        # Format the results
        formatted_result = format_job_results(result)
        
        return [types.TextContent(type="text", text=formatted_result)]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="xiaomi-jobs",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
