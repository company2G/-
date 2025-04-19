"""
禾燃客户管理系统 - 增强版启动脚本
该脚本先应用补丁修复admin_required问题，然后启动应用
"""
import os
import sys
import subprocess
import webbrowser
from time import sleep

def main():
    """主启动函数"""
    print("="*65)
    print("禾燃客户管理系统 - 增强版启动器")
    print("="*65)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)  # 将工作目录设置为脚本所在目录
    
    # 先应用补丁
    print("正在应用补丁...")
    try:
        from app_patch import apply_patch
        apply_patch()
    except Exception as e:
        print(f"应用补丁失败: {e}")
        print("尝试手动修复...")
        try:
            # 如果导入失败，直接运行补丁脚本
            subprocess.run([sys.executable, os.path.join(script_dir, "app_patch.py")])
        except Exception as e:
            print(f"手动修复也失败了: {e}")
            print("请按照以下步骤手动修复：")
            print("1. 打开app_simple.py文件")
            print("2. 在'app = Flask(__name__)'行之前添加以下代码：")
            print('''
# 添加admin_required装饰器
def admin_required(view):
    """检查用户是否为管理员的装饰器"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        if not g.user.get('role') == 'admin':
            flash('需要管理员权限访问该页面', 'danger')
            return redirect(url_for('dashboard'))
        return view(**kwargs)
    return wrapped_view
''')
            input("修复完成后按Enter继续...")
    
    # 然后启动应用
    print("\n正在启动禾燃客户管理系统...")
    
    # 启动Flask应用
    flask_process = subprocess.Popen([sys.executable, os.path.join(script_dir, "app_simple.py")])
    
    # 等待服务器启动
    print("等待服务器启动...")
    sleep(2)
    
    # 自动打开浏览器
    print("正在打开浏览器...")
    webbrowser.open("http://127.0.0.1:5000")
    
    print("\n系统已启动！按Ctrl+C结束程序。")
    
    try:
        # 保持程序运行
        flask_process.wait()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        flask_process.terminate()
        print("服务器已关闭。")

if __name__ == "__main__":
    main() 