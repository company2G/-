from app_simple import app, get_db
import ast
import re

def update_function():
    with app.app_context():
        db = get_db()
        
        # 检查表结构
        table_info = db.execute("PRAGMA table_info(client_product)").fetchall()
        columns = [col[1] for col in table_info]
        print("客户产品表结构:", columns)
        
        # 从数据库获取实际产品信息
        product = db.execute('SELECT * FROM client_product WHERE id = 13').fetchone()
        if product:
            product_dict = dict(product)
            print("产品实际数据:", product_dict)
        
        # 读取app_simple.py文件
        try:
            with open('app_simple.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 找到use_client_product函数
            pattern = r'(@app\.route\(\'/client/<int:client_id>/use_product/<int:client_product_id>\', methods=\[\'GET\', \'POST\'\])\s+@login_required\s+def use_client_product\(client_id, client_product_id\):(.*?)(?=@app\.route|\Z)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                function_code = match.group(0)
                print("找到use_client_product函数")
                
                # 检查函数是否需要修改
                if 'remaining_amount' in function_code and 'remaining_count' in columns:
                    print("需要更新函数中的字段引用")
                    
                    # 构建修改后的查询语句
                    if 'remaining_count' in function_code:
                        print("函数已经使用remaining_count")
                    else:
                        print("需要修改函数中的remaining_amount引用")
                    
                    # 修改POST逻辑
                    if 'if request.method == \'POST\':' in function_code:
                        print("找到POST处理逻辑")
                        
                        # 替换remaining_amount为remaining_count
                        post_logic = re.search(r'if request.method == \'POST\':(.*?)(?=return|if|else)', function_code, re.DOTALL)
                        if post_logic and 'remaining_amount' in post_logic.group(1):
                            print("POST逻辑中包含remaining_amount引用")
                            
                            # 提取这一部分为用户检查
                            print("\n==== 需要修改的代码片段 ====")
                            print(post_logic.group(1))
                            print("===========================\n")
                            
                            print("请在app_simple.py文件中将该部分的'remaining_amount'替换为'remaining_count'")
                
                print("\n建议手动更新app_simple.py中的use_client_product函数:")
                print("1. 将查询语句中的'remaining_amount'替换为'remaining_count'")
                print("2. 将POST处理逻辑中的'remaining_amount'替换为'remaining_count'")
                print("3. 确保在产品使用减少后更新正确的字段")
            else:
                print("未找到use_client_product函数")
        
        except Exception as e:
            print(f"处理文件时出错: {e}")

if __name__ == "__main__":
    update_function() 