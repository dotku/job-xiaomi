
#!/usr/bin/env python3
"""
Xiaomi Jobs API Query Script
Replicates the exact curl request for fetching job postings from Xiaomi careers portal.
"""

import requests
import json
import sys
from typing import Dict, List, Optional


def xiaomi_jobs_query(
    keyword: str = "",
    limit: int = 10,
    offset: int = 0,
    job_category_id_list: List[str] = None,
    tag_id_list: List[str] = None,
    location_code_list: List[str] = None,
    subject_id_list: List[str] = None,
    recruitment_id_list: List[str] = None,
    job_function_id_list: List[str] = None,
    storefront_id_list: List[str] = None
) -> Dict:
    """
    Query Xiaomi jobs API with exact parameters from the curl request.
    
    Args:
        keyword: Search keyword for job positions
        limit: Number of results to return (default: 10)
        offset: Offset for pagination (default: 0)
        job_category_id_list: List of job category IDs to filter by
        tag_id_list: List of tag IDs to filter by
        location_code_list: List of location codes to filter by
        subject_id_list: List of subject IDs to filter by
        recruitment_id_list: List of recruitment IDs to filter by
        job_function_id_list: List of job function IDs to filter by
        storefront_id_list: List of storefront IDs to filter by
    
    Returns:
        Dict containing the API response
    """
    
    url = "https://xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts"
    
    # Headers exactly as specified in the curl request
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN',
        'content-type': 'application/json',
        'env': 'undefined',
        'origin': 'https://xiaomi.jobs.f.mioffice.cn',
        'portal-channel': 'saas-career',
        'portal-platform': 'pc',
        'priority': 'u=1, i',
        'referer': 'https://xiaomi.jobs.f.mioffice.cn/index/?keywords=&category=&location=&project=&type=&job_hot_flag=&current=1&limit=10&functionCategory=&tag=',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'website-path': 'index',
        'x-csrf-token': 'undefined'
    }
    
    # Cookies from the curl request
    cookies = {
        'device-id': '',
        'locale': 'en-US',
        'channel': 'saas-career',
        'platform': 'pc',
        's_v_web_id': 'verify_mcoh7ij8_hZMeHe7e_cEvs_4P0L_AJjj_cxmXxMDYZB4F'
    }
    
    # Request payload exactly as specified
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
        response = requests.post(
            url, 
            headers=headers, 
            cookies=cookies, 
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        return result
        
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP Error {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request Error: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON Decode Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected Error: {str(e)}"}


def print_job_results(data: Dict) -> None:
    """
    Pretty print job search results.
    
    Args:
        data: Response data from the API
    """
    # Check if there was an error in our request handling
    if data.get("error"):
        print(f"❌ Error: {data['error']}")
        return
    
    # Check if API returned success
    if data.get("code") != 0:
        print(f"❌ API Error: {data.get('message', 'Unknown error')}")
        return
        
    if "data" not in data:
        print("❌ No 'data' key found in response")
        return
        
    data_section = data["data"]
    
    if "job_post_list" not in data_section:
        print("❌ No 'job_post_list' key found in data section")
        return
    
    job_posts = data_section["job_post_list"]
    total_count = data_section.get("count", len(job_posts))
    
    print(f"📋 Found {total_count} job(s), showing {len(job_posts)} results")
    
    if len(job_posts) == 0:
        print("📭 No job postings found")
        return
        
    print("=" * 80)
    
    for i, job in enumerate(job_posts, 1):
        print(f"{i}. {job.get('title', 'N/A')}")
        print(f"   🆔 Job Code: {job.get('code', 'N/A')}")
        
        # Handle location - can be city_info (single) or city_list (multiple)
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
        print(f"   📍 Location: {location_str}")
        
        # Recruitment type
        recruit_type = job.get('recruit_type', 'N/A')
        print(f"   💼 Type: {recruit_type}")
        
        # Job URL
        job_id = job.get('id', '')
        print(f"   🔗 URL: https://xiaomi.jobs.f.mioffice.cn/index/position/{job_id}/detail")
        
        # Description preview (clean newlines and limit length)
        description = job.get('description', '')
        if description:
            clean_desc = description.replace('\n', ' ').replace('\r', ' ').strip()
            desc_preview = clean_desc[:150] + "..." if len(clean_desc) > 150 else clean_desc
            print(f"   📝 Description: {desc_preview}")
        
        # Requirements preview (clean newlines and limit length)
        requirement = job.get('requirement', '')
        if requirement:
            clean_req = requirement.replace('\n', ' ').replace('\r', ' ').strip()
            req_preview = clean_req[:100] + "..." if len(clean_req) > 100 else clean_req
            print(f"   📋 Requirements: {req_preview}")
        
        print()


def main():
    """
    Main function to demonstrate the API usage.
    """
    print("🔍 Querying Xiaomi Jobs API...")
    
    # Example 1: Basic search with no filters
    print("\n1. Basic search (no filters):")
    data = xiaomi_jobs_query(limit=5)
    print_job_results(data)
    
    # Example 2: Search with keyword
    print("\n2. Search with keyword '工程师':")
    data = xiaomi_jobs_query(keyword="工程师", limit=5)
    print_job_results(data)
    
    # Example 3: Search with location filter (Beijing: CN_110000)
    print("\n3. Search in Beijing:")
    data = xiaomi_jobs_query(
        keyword="software", 
        location_code_list=["CN_110000"], 
        limit=5
    )
    print_job_results(data)


if __name__ == "__main__":
    main()