import requests
import logging

def get_xiaomi_jobs(keyword="", limit=10, offset=0, location_codes=None):
    url = "https://xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN",
        "content-type": "application/json",
        "origin": "https://xiaomi.jobs.f.mioffice.cn",
        "referer": "https://xiaomi.jobs.f.mioffice.cn/index/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "website-path": "index",
        "portal-channel": "saas-career",
        "portal-platform": "pc"
    }

    cookies = {
        "device-id": "",
        "locale": "en-US",
        "channel": "saas-career",
        "platform": "pc",
        "s_v_web_id": "verify_mcoh7ij8_hZMeHe7e_cEvs_4P0L_AJjj_cxmXxMDYZB4F"
    }

    payload = {
        "keyword": keyword,
        "limit": limit,
        "offset": offset,
        "job_category_id_list": [],
        "tag_id_list": [],
        "location_code_list": location_codes or [],
        "subject_id_list": [],
        "recruitment_id_list": [],
        "portal_type": 6,
        "job_function_id_list": [],
        "storefront_id_list": [],
        "portal_entrance": 1
    }

    response = requests.post(url, headers=headers, cookies=cookies, json=payload)
    response.raise_for_status()
    return response.json()

# 示例：查找深圳的软件工程师（location_code: CN_440300）
data = get_xiaomi_jobs(keyword="软件", location_codes=["CN_440300"], limit=10)

logging.info(data)
print(data)

# 打印结果
# for post in data['data']['posts']:
#     print(f"{post['name']} | {post['job_location_name']} | https://xiaomi.jobs.f.mioffice.cn/index/position/{post['post_id']}/detail")
