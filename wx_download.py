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

    # 确保所有键和字符串值被双引号括起来
    data_str = re.sub(r"(\w+):", r'"\1":', data_str)  # 键
    # data_str = re.sub(r": '([^']+)'", r': "\1"', data_str)  # 字符串值


    data_str = re.sub(r"\(\"\"http\":", '\"https:', data_str)

    data_str = re.sub(r"\"\"http\":", '\"https:', data_str)
    data_str = re.sub(r"\\x26amp;", '&', data_str)
    data_str = re.sub(r"\s+", '', data_str)
    data_str = re.sub(r",]", ']', data_str)
    data_str = re.sub(r",}", '}', data_str)
    # 特殊处理 URL 字段
    # data_str = re.sub(r"\('", '', data_str)
    # data_str = re.sub(r"\":", 's:', data_str)

    return data_str

# 请求头
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
# 1. 访问指定的 URL 并获取内容
print(sys.argv[1])
url = sys.argv[1]#"https://mp.weixin.qq.com/s/P3ZKQhUr8bWlAv27SXI2Ww"
response = requests.get(url, params={}, headers=headers)
content = response.text

html_content = response.text

# 使用 BeautifulSoup 解析 HTML 内容
soup = BeautifulSoup(html_content, 'html.parser')

# 查找所有图片标签
images = soup.find_all('img')

# 图片 URL 列表
image_urls = [img['data-src'] for img in images if 'data-src' in img.attrs]


# print(image_urls)

# 获取标题
# 查找具有特定属性的 meta 标签
meta_tag = soup.find('meta', {'property': 'og:title'})

# 获取 content 属性的值
title = meta_tag['content'] if meta_tag else "内容未找到"

print(title)

# 准备一个文件夹来保存图片
image_save_dir = str(title) + '/images'
if not os.path.exists(image_save_dir):
    os.makedirs(image_save_dir)

# 准备一个文件夹来保存视频
video_save_dir = str(title) + '/videos'
if not os.path.exists(video_save_dir):
    os.makedirs(video_save_dir)

# 下载并保存图片
for i, url in enumerate(image_urls):
    # print(url)
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(image_save_dir, f'image_{i}.jpg')
        with open(file_path, 'wb') as file:
            file.write(response.content)

# 找到 id="img-content" 的 div
div_content = soup.find('div', {'class': 'rich_media_wrp'})

# 将 div 内容转换为字符串
div_str = str(div_content) if div_content else "指定的 div 未找到"

# 指定输出文件路径
output_file = os.path.join(str(title), str(title) + '.html')

# 保存到文件
with open(output_file, 'w', encoding='utf-8') as file:
    file.write(div_str)

print(f"内容已保存到 {output_file}")

# 2. 从获取的内容中截取特定部分
start_phrase = "var videoPageInfos ="
end_phrase = ";\nwindow.__videoPageInfos"
start_index = content.find(start_phrase)
end_index = content.find(end_phrase)

if start_index != -1 and end_index != -1:
    videoInfos = content[start_index + len(start_phrase):end_index].strip()
else:
    videoInfos = "指定内容未找到"


# 打印截取的内容
# print(videoInfos)

# 转换字符串
jsondata = convert_js_to_python(videoInfos)

# print(jsondata)

converted_data = json.loads(jsondata)

# print(converted_data)

# 提取和打印所需信息
for video in converted_data:
    video_id = video['video_id']
    for trans_info in video['mp_video_trans_info']:
        format_id = trans_info['format_id']
        url = trans_info['url']

        # 解析 URL
        parsed_url = urlparse(url)

        # 获取 ? 前的 URL 部分
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # 获取查询参数字符串
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

        # print(base_url)
        # print(params)
        # 发送 GET 请求

        print(trans_info['video_quality_wording'] + str(trans_info['filesize']) + "下载开始…………")
        response = requests.get(base_url, params=params, headers=headers, stream=True)

        # 检查请求是否成功
        if response.status_code == 200:
            # 打开一个文件用于写入
            video_output_file = os.path.join(video_save_dir, trans_info['video_quality_wording'] + str(trans_info['filesize']) +'.mp4')
            print(video_output_file)
            with open(video_output_file, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192): 
                    file.write(chunk)
            print(trans_info['video_quality_wording'] + str(trans_info['filesize']) + "下载完成")
        else:
            print("请求失败，状态码：", response.status_code)

