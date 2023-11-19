import requests
import re
import ast
import json
from urllib.parse import urlparse, parse_qs
import requests
import sys
from bs4 import BeautifulSoup
import os 

def convert_js_to_python(data_str):
    # 移除 JavaScript 的 '||' 和 '* 1' 表达式
    data_str = re.sub(r"\|\| ''", '', data_str)
    data_str = re.sub(r"\|\| 0", '', data_str)
    data_str = re.sub(r"'(\d+)' \* 1", r'\1', data_str)
    data_str = re.sub(r"\).replace\(\/\^http\(s\?\):\/\, location.protocol\)", '', data_str)
    data_str = re.sub(r"'", '\"', data_str)
    data_str = re.sub(r"(\w+):", r'"\1":', data_str)  # 键
    data_str = re.sub(r"\(\"\"http\":", '\"https:', data_str)
    data_str = re.sub(r"\"\"http\":", '\"https:', data_str)
    data_str = re.sub(r"\\x26amp;", '&', data_str)
    data_str = re.sub(r"\s+", '', data_str)
    data_str = re.sub(r",]", ']', data_str)
    data_str = re.sub(r",}", '}', data_str)
    return data_str

def fetch_webpage(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Error fetching {url}: HTTP {response.status_code}")

def download_images(soup, image_urls, save_dir):
    meta_tag = soup.find('meta', {'property': 'og:title'})
    title = meta_tag['content'] if meta_tag else "内容未找到"
    print(title)

    image_save_dir = str(title) + '/images'
    if not os.path.exists(image_save_dir):
        os.makedirs(image_save_dir)

    # 下载并保存图片
    for i, url in enumerate(image_urls):
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(image_save_dir, f'image_{i}.jpg')
            with open(file_path, 'wb') as file:
                file.write(response.content)

def extract_image_urls(soup, html_content):
    images = soup.find_all('img')
    image_urls = [img['data-src'] for img in images if 'data-src' in img.attrs]
    return image_urls

def extract_video_info(soup, html_content):
    meta_tag = soup.find('meta', {'property': 'og:title'})
    title = meta_tag['content'] if meta_tag else "内容未找到"

    div_content = soup.find('div', {'class': 'rich_media_wrp'})
    div_str = str(div_content) if div_content else "指定的 div 未找到"

    output_file = os.path.join(str(title), str(title) + '.html')
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(div_str)

    print(f"内容已保存到 {output_file}")

    start_phrase = "var videoPageInfos ="
    end_phrase = ";\nwindow.__videoPageInfos"
    start_index = html_content.find(start_phrase)
    end_index = html_content.find(end_phrase)

    if start_index != -1 and end_index != -1:
        videoInfos = html_content[start_index + len(start_phrase):end_index].strip()
    else:
        videoInfos = "指定内容未找到"

    jsondata = convert_js_to_python(videoInfos)
    converted_data = json.loads(jsondata)
    return converted_data

def download_videos(soup, video_info, save_dir, headers):
    meta_tag = soup.find('meta', {'property': 'og:title'})
    title = meta_tag['content'] if meta_tag else "内容未找到" 
    video_save_dir = str(title) + '/videos'
    if not os.path.exists(video_save_dir):
        os.makedirs(video_save_dir)
    for video in video_info:
        video_id = video['video_id']
        for trans_info in video['mp_video_trans_info']:
            format_id = trans_info['format_id']
            url = trans_info['url']

            parsed_url = urlparse(url)

            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

            query_str = parsed_url.query

            # 解析查询参数字符串到字典
            # auth_info 里面有加号，parse_qs可能把加号变成空格，所以需要替换成 %2B
            params = parse_qs(query_str.replace("+", "%2B"))

            # 将列表值转换为单个值
            params = {k: v[0] for k, v in params.items()}

            params['vid'] = str(video_id)
            params['format_id'] = str(format_id)
            params['support_redirect'] = '0'
            params['mmversion'] = 'false'

            print(trans_info['video_quality_wording'] + str(trans_info['filesize']) + "下载开始…………")
            response = requests.get(base_url, params=params, headers=headers, stream=True)

            if response.status_code == 200:
                video_output_file = os.path.join(video_save_dir, trans_info['video_quality_wording'] + str(trans_info['filesize']) +'.mp4')
                print(video_output_file)
                with open(video_output_file, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192): 
                        file.write(chunk)
                print(trans_info['video_quality_wording'] + str(trans_info['filesize']) + "下载完成")
            else:
                print("请求失败，状态码：", response.status_code)

def main(url):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Origin': 'https://mp.weixin.qq.com',
        'Referer': 'https://mp.weixin.qq.com/',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36 Edg/119.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"'
    }
    html_content = fetch_webpage(url, headers)
    soup = BeautifulSoup(html_content, 'html.parser')
    image_urls = extract_image_urls(soup, html_content)
    download_images(soup, image_urls, 'images')
    video_info = extract_video_info(soup, html_content)
    download_videos(soup, video_info, 'videos', headers)

if __name__ == "__main__":
    main(sys.argv[1])

