import sqlite3
import os

# 使用正确的数据库路径
DB_PATH = "I:\\bettest\\禾燃客户管理\\database.db"

def check_specific_tables():
    """检查特定表的结构和记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查重量记录表
        print("\n==== 体重记录表 (weight_record) ====")
        cursor.execute("PRAGMA table_info(weight_record)")
        columns = cursor.fetchall()
        print("字段:")
        for column in columns:
            print(f"  - {column['name']} ({column['type']})" + (" (主键)" if column['pk'] == 1 else ""))
        
        # 获取最新的10条记录
        cursor.execute("SELECT * FROM weight_record ORDER BY id DESC LIMIT 10")
        records = cursor.fetchall()
        print(f"\n最新记录 (共 {len(records)} 条):")
        for record in records:
            print(f"  ID: {record['id']}, 日期: {record['record_date']}, 客户ID: {record['client_id']}, 体重: {record['morning_weight']}kg")
        
        # 检查客户表
        print("\n==== 客户表 (client) ====")
        cursor.execute("PRAGMA table_info(client)")
        columns = cursor.fetchall()
        print("字段:")
        for column in columns:
            print(f"  - {column['name']} ({column['type']})" + (" (主键)" if column['pk'] == 1 else ""))
        
        # 获取所有客户
        cursor.execute("SELECT id, name, phone, user_id FROM client")
        clients = cursor.fetchall()
        print(f"\n客户列表 (共 {len(clients)} 条):")
        for client in clients:
            print(f"  ID: {client['id']}, 姓名: {client['name']}, 电话: {client['phone']}, 创建者ID: {client['user_id']}")
        
        # 检查用户表
        print("\n==== 用户表 (user) ====")
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        print("字段:")
        for column in columns:
            print(f"  - {column['name']} ({column['type']})" + (" (主键)" if column['pk'] == 1 else ""))
        
        # 获取所有用户
        cursor.execute("SELECT id, username, role FROM user")
        users = cursor.fetchall()
        print(f"\n用户列表 (共 {len(users)} 条):")
        for user in users:
            print(f"  ID: {user['id']}, 用户名: {user['username']}, 角色: {user['role']}")
        
        # 检查客户产品表
        print("\n==== 客户产品表 (client_product) ====")
        cursor.execute("PRAGMA table_info(client_product)")
        columns = cursor.fetchall()
        print("字段:")
        for column in columns:
            print(f"  - {column['name']} ({column['type']})" + (" (主键)" if column['pk'] == 1 else ""))
        
        # 获取最新的10条记录
        cursor.execute("""
            SELECT cp.id, cp.client_id, c.name as client_name, cp.product_id, 
                   p.name as product_name, cp.remaining_count, cp.expiry_date 
            FROM client_product cp
            JOIN client c ON cp.client_id = c.id
            JOIN product p ON cp.product_id = p.id
            ORDER BY cp.id DESC LIMIT 10
        """)
        records = cursor.fetchall()
        print(f"\n最新产品记录 (共 {len(records)} 条):")
        for record in records:
            print(f"  ID: {record['id']}, 客户: {record['client_name']}(ID:{record['client_id']}), 产品: {record['product_name']}(ID:{record['product_id']}), 剩余次数: {record['remaining_count']}, 有效期至: {record['expiry_date']}")
            
        conn.close()
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    check_specific_tables() 