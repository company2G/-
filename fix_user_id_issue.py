from app_simple import app, get_db
import re

def fix_use_client_product():
    # 读取app_simple.py文件
    with open('app_simple.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open('app_simple.py.user_id_fix.bak', 'w', encoding='utf-8') as f:
        f.write(content)
    print("创建了app_simple.py的备份")
    
    # 找到use_client_product函数
    pattern = r'(@app\.route\(\'/client/<int:client_id>/use_product/<int:client_product_id>\', methods=\[\'GET\', \'POST\'\])\s+@login_required\s+def use_client_product\(client_id, client_product_id\):(.*?)(?=\n@app\.route|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("未找到use_client_product函数，请检查代码")
        return
    
    function_code = match.group(0)
    print("找到use_client_product函数")
    
    # 查找插入client_product_usage的代码段
    db_execute_pattern = r"db\.execute\(\s+'INSERT INTO client_product_usage.*?\)"
    db_execute_match = re.search(db_execute_pattern, function_code, re.DOTALL)
    
    if not db_execute_match:
        print("未找到数据库插入操作，请检查代码")
        return
    
    # 获取原始插入语句
    original_db_execute = db_execute_match.group(0)
    print("找到数据库插入语句")
    
    # 修改插入语句，添加用户ID检查
    if "g.user.id" in original_db_execute:
        modified_db_execute = original_db_execute.replace(
            "g.user.id", 
            "(g.user.id if g.user else 1)"  # 如果g.user为None，使用ID 1（通常是管理员）
        )
        
        # 更新函数代码
        modified_function = function_code.replace(original_db_execute, modified_db_execute)
        
        # 更新文件内容
        updated_content = content.replace(function_code, modified_function)
        
        # 写回文件
        with open('app_simple.py', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("已修复g.user.id引用问题")
    else:
        print("未找到g.user.id引用，可能已被修改")
    
    print("检查完成")

if __name__ == "__main__":
    fix_use_client_product() 