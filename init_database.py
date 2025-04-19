"""
禾燃客户管理系统 - 数据库初始化工具
该脚本仅用于初始化或重置数据库
"""
import os
import sqlite3
import sys

def init_db():
    """初始化数据库"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'database.db')
    schema_path = os.path.join(current_dir, 'schema.sql')
    
    print(f"当前工作目录: {current_dir}")
    print(f"数据库路径: {db_path}")
    print(f"SQL模式文件: {schema_path}")
    
    # 检查schema.sql是否存在
    if not os.path.exists(schema_path):
        print(f"错误：找不到schema.sql文件，请确保它存在于: {schema_path}")
        return False
    
    # 如果数据库已存在，询问用户是否删除
    if os.path.exists(db_path):
        try:
            confirm = input(f"警告：数据库文件已存在({db_path})。删除并重新创建？(y/n): ")
            if confirm.lower() != 'y':
                print("操作已取消。")
                return False
                
            os.remove(db_path)
            print("已删除旧数据库文件。")
        except PermissionError:
            print("错误：无法删除数据库文件，它可能正在被其他程序使用。")
            print("请关闭所有使用该数据库的程序后重试。")
            return False
    
    try:
        # 创建新的数据库连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 读取和执行schema.sql
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        
        # 提交更改
        conn.commit()
        conn.close()
        
        print("="*50)
        print("✓ 数据库初始化成功！")
        print("="*50)
        return True
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("禾燃客户管理系统 - 数据库初始化工具")
    print("="*50)
    
    success = init_db()
    
    if success:
        print("您现在可以运行应用程序了。")
    else:
        print("数据库初始化失败，请解决上述错误后重试。")
        sys.exit(1) 