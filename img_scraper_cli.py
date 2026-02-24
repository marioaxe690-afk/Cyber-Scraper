import os
import sys
import requests
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm


def find_next_page_link(soup, current_url):
    """智能查找下一页链接"""
    # 常见的"下一页"关键词
    next_keywords = ['下一页', '下页', 'next', 'Next', 'NEXT', '›', '»', '→']

    # 查找所有链接
    all_links = soup.find_all('a', href=True)

    for link in all_links:
        link_text = link.get_text(strip=True)
        link_title = link.get('title', '')
        link_class = ' '.join(link.get('class', []))

        # 检查链接文本、title 或 class 是否包含"下一页"关键词
        for keyword in next_keywords:
            if keyword in link_text or keyword in link_title or keyword in link_class:
                next_url = urljoin(current_url, link['href'])
                return next_url

    return None


def scrape_images(url, page_num, total_pages, save_dir='images'):
    """从指定URL抓取所有图片"""

    # 伪装浏览器身份（更新为最新 Chrome 版本）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    try:
        # 获取网页内容
        print(f"\n{'='*60}")
        print(f"[*] 正在收割第 {page_num}/{total_pages} 页...")
        print(f"[+] URL: {url}")
        print(f"{'='*60}")

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 防封印护盾：模拟人类浏览速度
        time.sleep(random.uniform(0.8, 1.5))

        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # 提取所有图片标签
        img_tags = soup.find_all('img')

        if not img_tags:
            print("[!] 未找到任何图片")
            return soup, 0

        print(f"[+] 找到 {len(img_tags)} 张图片")

        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"[+] 已创建目录: {save_dir}")

        # 提取图片链接并转换为绝对路径
        img_urls = []
        for img in img_tags:
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                # 转换相对路径为绝对路径
                absolute_url = urljoin(url, img_url)
                img_urls.append(absolute_url)

        # 下载图片
        success_count = 0
        for idx, img_url in enumerate(tqdm(img_urls, desc=f"[>>] Page {page_num} Download", ncols=80), 1):
            try:
                # 获取文件名
                parsed_url = urlparse(img_url)
                filename = os.path.basename(parsed_url.path)

                # 如果文件名为空或无扩展名，使用序号命名
                if not filename or '.' not in filename:
                    filename = f"page{page_num}_image_{idx}.jpg"
                else:
                    # 添加页码前缀避免重名
                    name, ext = os.path.splitext(filename)
                    filename = f"page{page_num}_{name}{ext}"

                filepath = os.path.join(save_dir, filename)

                # 下载图片时添加 Referer 防止防盗链拦截
                download_headers = headers.copy()
                download_headers['Referer'] = url

                img_response = requests.get(img_url, headers=download_headers, timeout=10)
                img_response.raise_for_status()

                # 保存图片
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)

                success_count += 1

                # 防封印护盾：每下载几张图片就休息一下
                if idx % 5 == 0:
                    time.sleep(random.uniform(0.3, 0.8))

            except Exception as e:
                print(f"\n[X] Download failed [{img_url}]: {str(e)}")
                continue

        print(f"[OK] Page {page_num} completed! Downloaded {success_count}/{len(img_urls)} images")

        return soup, success_count

    except requests.exceptions.RequestException as e:
        print(f"[X] Failed to access webpage: {str(e)}")
        return None, 0
    except Exception as e:
        print(f"[X] Error occurred: {str(e)}")
        return None, 0


def main():
    print("=" * 60)
    print(">> Image Scraper - Auto Mode")
    print("=" * 60)

    # 从命令行参数获取URL和页数
    if len(sys.argv) < 3:
        print("\nUsage: python img_scraper_cli.py <URL> <pages>")
        print("Example: python img_scraper_cli.py https://example.com 3")
        return

    url = sys.argv[1].strip()

    try:
        total_pages = int(sys.argv[2])
        if total_pages <= 0:
            print("[X] Pages must be greater than 0")
            return
    except ValueError:
        print("[X] Please provide a valid number for pages")
        return

    # 确保URL包含协议
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    print(f"\n[*] Starting auto mode: will scrape {total_pages} pages")
    print("[*] Anti-ban shield activated, simulating human browsing speed...")

    # 创建保存目录
    save_dir = 'images'

    # 开始自动翻页抓取
    current_url = url
    total_images = 0

    for page_num in range(1, total_pages + 1):
        # 抓取当前页
        soup, success_count = scrape_images(current_url, page_num, total_pages, save_dir)
        total_images += success_count

        if soup is None:
            print(f"\n[!] Page {page_num} scraping failed, stopping pagination")
            break

        # 如果还有下一页，查找下一页链接
        if page_num < total_pages:
            print(f"\n[?] Looking for next page link...")
            next_url = find_next_page_link(soup, current_url)

            if next_url:
                print(f"[+] Found next page: {next_url}")
                current_url = next_url

                # 防封印护盾：翻页前休息一下
                wait_time = random.uniform(1.5, 3.0)
                print(f"[Z] Resting {wait_time:.1f} seconds before continuing...")
                time.sleep(wait_time)
            else:
                print(f"[!] No next page link found, stopped after {page_num} pages")
                break

    # 最终统计
    print(f"\n{'='*60}")
    print(f"[OK] Auto mode completed!")
    print(f"[+] Total downloaded {total_images} images to {save_dir} directory")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
