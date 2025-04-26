import sqlite3
import os

# 使用正确的数据库路径
DB_PATH = "I:\\bettest\\禾燃客户管理\\database.db"

def inspect_database():
    """检查数据库结构并打印所有表名和字段名"""
    try:
        # 连接到数据库
        print(f"尝试连接数据库: {DB_PATH}")
        
        # 检查文件是否存在
        if not os.path.exists(DB_PATH):
            print(f"错误: 数据库文件不存在于 {DB_PATH}")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("数据库中没有找到表")
            return
            
        print("\n==== 数据库表结构 ====\n")
        
        # 对于每个表，获取字段信息
        for table in tables:
            table_name = table[0]
            print(f"\n表名: {table_name}")
            
            # 获取表字段信息
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("字段:")
            for column in columns:
                # column格式: (cid, name, type, notnull, dflt_value, pk)
                print(f"  - {column[1]} ({column[2]})" + (" (主键)" if column[5] == 1 else ""))
            
            # 尝试获取表中的行数
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                print(f"行数: {row_count}")
            except sqlite3.Error as e:
                print(f"无法获取表 {table_name} 的行数: {e}")
        
        conn.close()
        print("\n==== 数据库检查完成 ====")
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    inspect_database() 