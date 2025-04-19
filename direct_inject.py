"""
直接将admin_required代码注入到app_simple.py文件中
这是一个一次性工具，用于解决admin_required未定义的问题
"""
import os
import sys

def inject_admin_required():
    """在正确位置直接注入admin_required代码"""
    print("="*65)
    print("直接修复工具 - 将admin_required代码注入到app_simple.py")
    print("="*65)
    
    # 获取app_simple.py的路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, 'app_simple.py')
    
    # 检查文件是否存在
    if not os.path.exists(app_path):
        print(f"错误: 找不到文件 {app_path}")
        return False
    
    # 读取原始文件内容
    try:
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return False
    
    # 检查代码是否已经存在
    if "def admin_required(view):" in content:
        print("admin_required函数已存在于文件中，无需修改")
        return True
    
    # 准备要注入的代码
    admin_required_code = """
# 直接定义admin_required装饰器，避免导入问题
def admin_required(view):
    \"\"\"检查用户是否为管理员的装饰器\"\"\"
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        if not g.user.get('role') == 'admin':
            flash('需要管理员权限访问该页面', 'danger')
            return redirect(url_for('dashboard'))
        return view(**kwargs)
    return wrapped_view
"""
    
    # 找到合适的注入点
    # 我们尝试在Flask应用创建前，导入语句后插入
    app_creation_pos = content.find("app = Flask(__name__)")
    if app_creation_pos == -1:
        print("警告: 找不到'app = Flask(__name__)'，尝试插入到文件开头")
        # 如果找不到，则尝试直接插入到开头
        new_content = admin_required_code + content
    else:
        # 找到最后一个import语句
        import_lines = [line for line in content[:app_creation_pos].split('\n') if line.strip().startswith("import") or line.strip().startswith("from")]
        
        if not import_lines:
            # 如果找不到import语句，就插入到文件开头
            new_content = admin_required_code + content
        else:
            # 找到最后一个import语句的位置，并在其后插入
            last_import_pos = content.find(import_lines[-1]) + len(import_lines[-1])
            new_content = content[:last_import_pos] + "\n" + admin_required_code + content[last_import_pos:]
    
    # 备份原文件
    backup_path = app_path + '.bak'
    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已备份原文件到 {backup_path}")
    except Exception as e:
        print(f"备份文件失败: {e}")
        return False
    
    # 写入修改后的内容
    try:
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("成功将admin_required代码注入到app_simple.py")
        return True
    except Exception as e:
        print(f"写入文件失败: {e}")
        # 尝试恢复原文件
        try:
            with open(app_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except:
            pass
        return False

if __name__ == "__main__":
    if inject_admin_required():
        print("操作成功完成！")
        print("\n现在可以使用原始的启动脚本启动应用：")
        print("& i:/bettest/禾燃客户管理/.venv/Scripts/python.exe i:/bettest/禾燃客户管理/run_app.py")
    else:
        print("操作失败！请尝试手动修改文件。")
        print("请查看direct_fix.txt文件了解手动修复步骤。") 