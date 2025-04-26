from app_simple import app, get_db
import importlib.util
import sys
import re

def fix_function():
    with app.app_context():
        # 读取app_simple.py文件
        with open('app_simple.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找use_client_product函数
        pattern = r'(@app\.route\(\'/client/<int:client_id>/use_product/<int:client_product_id>\', methods=\[\'GET\', \'POST\'\])\n@login_required\ndef use_client_product\(client_id, client_product_id\):(.*?)@app\.route'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            print("找到use_client_product函数")
            old_function = match.group(0)
            
            # 检查当前数据库表结构
            db = get_db()
            # 获取客户产品表的结构
            table_info = db.execute("PRAGMA table_info(client_product)").fetchall()
            column_names = [col[1] for col in table_info]
            print("客户产品表的列名:", column_names)
            
            # 构建替换函数
            # 检查是否有remaining_count而不是remaining_amount
            if 'remaining_count' in column_names and 'remaining_amount' not in column_names:
                print("检测到表使用remaining_count字段，将更新函数")
                
                # 创建更新后的函数
                # 替换表单中的remaining_amount为remaining_count
                new_function = old_function.replace(
                    "client_product = db.execute(\n",
                    "client_product = db.execute(\n"
                    "        'SELECT cp.*, p.name as product_name, '\n"
                    "        'cp.remaining_count as remaining_amount '\n"
                )
                
                if "client_product['remaining_amount']" in new_function:
                    print("发现remaining_amount引用，将被替换")
                
                # 更新模板文件
                try:
                    with open('templates/use_product.html', 'r', encoding='utf-8') as f:
                        template_content = f.read()
                    
                    # 检查并更新模板中的字段引用
                    if "client_product['remaining_amount']" in template_content:
                        print("更新模板中的字段引用")
                        updated_template = template_content.replace(
                            "client_product['remaining_amount']", 
                            "client_product['remaining_amount'] if 'remaining_amount' in client_product else client_product['remaining_count']"
                        )
                        
                        with open('templates/use_product.html', 'w', encoding='utf-8') as f:
                            f.write(updated_template)
                        print("模板已更新")
                    
                except Exception as e:
                    print(f"更新模板时出错: {e}")
                
                return "检测到remaining_count字段，请在/client/6/use_product/13路由上测试功能。"
            else:
                return "数据库结构正常，无需更改函数"
        else:
            return "未找到use_client_product函数，请检查文件"

if __name__ == "__main__":
    result = fix_function()
    print(result) 