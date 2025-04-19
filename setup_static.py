#!/usr/bin/env python
import os
import urllib.request
import shutil

def setup_static_files():
    """设置静态文件"""
    print("正在设置静态文件...")
    
    # 确保静态目录存在
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    css_dir = os.path.join(static_dir, 'css')
    js_dir = os.path.join(static_dir, 'js')
    
    for directory in [static_dir, css_dir, js_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # 下载Bootstrap CSS
    bootstrap_css_url = "https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css"
    bootstrap_css_path = os.path.join(css_dir, "bootstrap.min.css")
    
    # 下载jQuery
    jquery_url = "https://code.jquery.com/jquery-3.5.1.min.js"
    jquery_path = os.path.join(js_dir, "jquery-3.5.1.min.js")
    
    # 下载Bootstrap JS
    bootstrap_js_url = "https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"
    bootstrap_js_path = os.path.join(js_dir, "bootstrap.bundle.min.js")
    
    # 下载文件
    files_to_download = [
        (bootstrap_css_url, bootstrap_css_path),
        (jquery_url, jquery_path),
        (bootstrap_js_url, bootstrap_js_path)
    ]
    
    for url, path in files_to_download:
        if not os.path.exists(path):
            print(f"下载 {url} 到 {path}")
            try:
                urllib.request.urlretrieve(url, path)
                print(f"✓ 已下载 {os.path.basename(path)}")
            except Exception as e:
                print(f"✗ 下载失败: {str(e)}")
    
    print("静态文件设置完成")

if __name__ == "__main__":
    setup_static_files() 