import os
import requests
import time
import random
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


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


def scrape_images(url, page_num, total_pages, save_dir='images', log_callback=None):
    """从指定URL抓取所有图片"""

    def log(msg):
        """统一日志输出"""
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    # 伪装浏览器身份（更新为最新 Chrome 版本）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    try:
        # 获取网页内容
        log(f"\n{'='*60}")
        log(f"[*] 正在收割第 {page_num}/{total_pages} 页...")
        log(f"[+] URL: {url}")
        log(f"{'='*60}")

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 防封印护盾：模拟人类浏览速度
        time.sleep(random.uniform(0.8, 1.5))

        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # 提取所有图片标签
        img_tags = soup.find_all('img')

        if not img_tags:
            log("[!] 未找到任何图片")
            return soup, 0

        log(f"[+] 找到 {len(img_tags)} 张图片")

        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            log(f"[+] 已创建目录: {save_dir}")

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
        for idx, img_url in enumerate(img_urls, 1):
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
                log(f"[>>] 第{page_num}页 下载进度: {idx}/{len(img_urls)} - {filename}")

                # 防封印护盾：每下载几张图片就休息一下
                if idx % 5 == 0:
                    time.sleep(random.uniform(0.3, 0.8))

            except Exception as e:
                log(f"[X] 下载失败 [{img_url}]: {str(e)}")
                continue

        log(f"[OK] 第 {page_num} 页完成！成功下载 {success_count}/{len(img_urls)} 张图片")

        return soup, success_count

    except requests.exceptions.RequestException as e:
        log(f"[X] 访问网页失败: {str(e)}")
        return None, 0
    except Exception as e:
        log(f"[X] 发生错误: {str(e)}")
        return None, 0


def main():
    print("=" * 60)
    print(">> 图片爬虫工具 - 挂机模式")
    print("=" * 60)

    # 获取初始URL
    url = input("\n请输入初始网页的URL: ").strip()

    if not url:
        print("[X] URL不能为空")
        return

    # 确保URL包含协议
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # 获取要抓取的总页数
    while True:
        try:
            total_pages = int(input("请输入要自动抓取的总页数（例如 3）: ").strip())
            if total_pages <= 0:
                print("[X] 页数必须大于0，请重新输入")
                continue
            break
        except ValueError:
            print("[X] 请输入有效的数字")

    print(f"\n[*] 开始挂机模式：将自动抓取 {total_pages} 页")
    print("[*] 防封印护盾已启动，模拟人类浏览速度...")

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
            print(f"\n[!] 第 {page_num} 页抓取失败，停止翻页")
            break

        # 如果还有下一页，查找下一页链接
        if page_num < total_pages:
            print(f"\n[?] 正在查找下一页链接...")
            next_url = find_next_page_link(soup, current_url)

            if next_url:
                print(f"[+] 找到下一页: {next_url}")
                current_url = next_url

                # 防封印护盾：翻页前休息一下
                wait_time = random.uniform(1.5, 3.0)
                print(f"[Z] 休息 {wait_time:.1f} 秒后继续...")
                time.sleep(wait_time)
            else:
                print(f"[!] 未找到下一页链接，已抓取 {page_num} 页后停止")
                break

    # 最终统计
    print(f"\n{'='*60}")
    print(f"[OK] 挂机完成！")
    print(f"[+] 总共成功下载 {total_images} 张图片到 {save_dir} 目录")
    print(f"{'='*60}")


class CyberScraperGUI:
    """4K壁纸赛博收割机 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("4K壁纸赛博收割机 V1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 设置赛博风格配色
        bg_color = "#0a0e27"
        fg_color = "#00ff41"
        button_color = "#1a1f3a"

        self.root.configure(bg=bg_color)

        # 是否正在运行
        self.is_running = False

        # 标题
        title_label = tk.Label(
            root,
            text="🔥 4K壁纸赛博收割机 V1.0 🔥",
            font=("Consolas", 18, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        title_label.pack(pady=15)

        # 输入框区域
        input_frame = tk.Frame(root, bg=bg_color)
        input_frame.pack(pady=10, padx=20, fill="x")

        # 目标网址
        url_label = tk.Label(
            input_frame,
            text="目标网址:",
            font=("Consolas", 11),
            bg=bg_color,
            fg=fg_color
        )
        url_label.grid(row=0, column=0, sticky="w", pady=5)

        self.url_entry = tk.Entry(
            input_frame,
            font=("Consolas", 10),
            bg=button_color,
            fg=fg_color,
            insertbackground=fg_color,
            width=60
        )
        self.url_entry.insert(0, "https://pic.netbian.com/4kfengjing/")
        self.url_entry.grid(row=0, column=1, pady=5, padx=10)

        # 抓取页数
        pages_label = tk.Label(
            input_frame,
            text="抓取页数:",
            font=("Consolas", 11),
            bg=bg_color,
            fg=fg_color
        )
        pages_label.grid(row=1, column=0, sticky="w", pady=5)

        self.pages_entry = tk.Entry(
            input_frame,
            font=("Consolas", 10),
            bg=button_color,
            fg=fg_color,
            insertbackground=fg_color,
            width=60
        )
        self.pages_entry.insert(0, "3")
        self.pages_entry.grid(row=1, column=1, pady=5, padx=10)

        # 开始收割按钮
        self.start_button = tk.Button(
            root,
            text="⚡ 开始收割 ⚡",
            font=("Consolas", 14, "bold"),
            bg="#ff0066",
            fg="white",
            activebackground="#cc0052",
            activeforeground="white",
            command=self.start_scraping,
            cursor="hand2",
            height=2,
            width=20
        )
        self.start_button.pack(pady=15)

        # 日志区域标签
        log_label = tk.Label(
            root,
            text="📡 实时日志",
            font=("Consolas", 12, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        log_label.pack(pady=(10, 5))

        # 日志滚动文本框
        self.log_text = scrolledtext.ScrolledText(
            root,
            font=("Consolas", 9),
            bg="#0d1117",
            fg="#00ff41",
            insertbackground=fg_color,
            wrap=tk.WORD,
            height=20
        )
        self.log_text.pack(pady=10, padx=20, fill="both", expand=True)

        # 初始欢迎信息
        self.log("=" * 80)
        self.log("欢迎使用 4K壁纸赛博收割机 V1.0")
        self.log("请输入目标网址和抓取页数，然后点击【开始收割】按钮")
        self.log("=" * 80)

    def log(self, message):
        """线程安全的日志输出"""
        def append():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)

        # 使用 after 确保在主线程中更新 GUI
        self.root.after(0, append)

    def start_scraping(self):
        """开始抓取（在后台线程运行）"""
        if self.is_running:
            messagebox.showwarning("警告", "收割机正在运行中，请等待完成！")
            return

        # 获取输入
        url = self.url_entry.get().strip()
        pages_str = self.pages_entry.get().strip()

        # 验证输入
        if not url:
            messagebox.showerror("错误", "目标网址不能为空！")
            return

        # 确保URL包含协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            total_pages = int(pages_str)
            if total_pages <= 0:
                messagebox.showerror("错误", "页数必须大于0！")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的页数！")
            return

        # 禁用按钮
        self.start_button.config(state="disabled", text="⏳ 收割中...")
        self.is_running = True

        # 清空日志
        self.log_text.delete(1.0, tk.END)

        # 在后台线程运行爬虫
        thread = threading.Thread(
            target=self.run_scraper,
            args=(url, total_pages),
            daemon=True
        )
        thread.start()

    def run_scraper(self, url, total_pages):
        """后台线程运行的爬虫逻辑"""
        try:
            self.log(f"\n[*] 开始挂机模式：将自动抓取 {total_pages} 页")
            self.log("[*] 防封印护盾已启动，模拟人类浏览速度...")

            # 创建保存目录
            save_dir = 'images'

            # 开始自动翻页抓取
            current_url = url
            total_images = 0

            for page_num in range(1, total_pages + 1):
                # 抓取当前页
                soup, success_count = scrape_images(
                    current_url,
                    page_num,
                    total_pages,
                    save_dir,
                    log_callback=self.log
                )
                total_images += success_count

                if soup is None:
                    self.log(f"\n[!] 第 {page_num} 页抓取失败，停止翻页")
                    break

                # 如果还有下一页，查找下一页链接
                if page_num < total_pages:
                    self.log(f"\n[?] 正在查找下一页链接...")
                    next_url = find_next_page_link(soup, current_url)

                    if next_url:
                        self.log(f"[+] 找到下一页: {next_url}")
                        current_url = next_url

                        # 防封印护盾：翻页前休息一下
                        wait_time = random.uniform(1.5, 3.0)
                        self.log(f"[Z] 休息 {wait_time:.1f} 秒后继续...")
                        time.sleep(wait_time)
                    else:
                        self.log(f"[!] 未找到下一页链接，已抓取 {page_num} 页后停止")
                        break

            # 最终统计
            self.log(f"\n{'='*80}")
            self.log(f"[OK] 挂机完成！")
            self.log(f"[+] 总共成功下载 {total_images} 张图片到 {save_dir} 目录")
            self.log(f"{'='*80}")

            # 显示完成对话框
            self.root.after(0, lambda: messagebox.showinfo(
                "收割完成",
                f"成功下载 {total_images} 张图片到 {save_dir} 目录！"
            ))

        except Exception as e:
            self.log(f"\n[X] 发生严重错误: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"发生错误: {str(e)}"))

        finally:
            # 恢复按钮
            self.is_running = False
            self.root.after(0, lambda: self.start_button.config(
                state="normal",
                text="⚡ 开始收割 ⚡"
            ))


def launch_gui():
    """启动 GUI 界面"""
    root = tk.Tk()
    app = CyberScraperGUI(root)
    root.mainloop()


if __name__ == '__main__':
    # 启动 GUI 界面
    launch_gui()
