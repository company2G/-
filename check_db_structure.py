from app_simple import app, get_db
import json

def check_db_structure():
    """检查数据库结构并输出详细信息"""
    
    with app.app_context():
        db = get_db()
        print("连接数据库成功！")
        
        # 获取所有表
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"\n数据库中共有 {len(tables)} 个表:")
        for table in tables:
            print(f"- {table['name']}")
        
        # 详细检查关键表结构
        key_tables = ['client', 'product', 'user', 'client_product', 'client_product_usage']
        
        for table_name in key_tables:
            try:
                # 获取表结构
                columns = db.execute(f"PRAGMA table_info({table_name})").fetchall()
                print(f"\n【{table_name}】表结构:")
                print("序号 | 字段名称 | 数据类型 | 是否必填 | 默认值 | 是否主键")
                print("-" * 60)
                for col in columns:
                    print(f"{col['cid']} | {col['name']} | {col['type']} | {col['notnull']} | {col['dflt_value']} | {col['pk']}")
                
                # 获取一条示例数据
                sample = db.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchone()
                if sample:
                    print(f"\n【{table_name}】表示例数据:")
                    sample_dict = dict(sample)
                    for key, value in sample_dict.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"\n【{table_name}】表中没有数据")
                    
                # 对特定表进行额外检查
                if table_name == 'client':
                    check_client_creator_field(db)
                elif table_name == 'product':
                    check_product_creator_field(db)
                    
            except Exception as e:
                print(f"检查表 {table_name} 时出错: {e}")
        
        # 检查表关系
        print("\n\n关键表关系检查:")
        check_table_relationships(db)

def check_client_creator_field(db):
    """检查client表中创建者信息的存储方式"""
    print("\n正在检查client表的创建者字段...")
    
    # 检查可能的创建者字段
    possible_fields = ['user_id', 'created_by', 'creator_id', 'creator']
    existing_fields = []
    
    # 获取表结构
    columns = db.execute("PRAGMA table_info(client)").fetchall()
    column_names = [col['name'] for col in columns]
    
    for field in possible_fields:
        if field in column_names:
            existing_fields.append(field)
            print(f"找到可能的创建者字段: {field}")
            
            # 检查字段值
            sample_values = db.execute(f"SELECT {field} FROM client LIMIT 5").fetchall()
            print(f"  字段 {field} 的示例值: {[row[0] for row in sample_values]}")
            
            # 如果字段似乎存储了user_id，尝试关联查询
            try:
                creators = db.execute(f"""
                    SELECT c.id as client_id, c.{field} as creator_id, u.username
                    FROM client c
                    LEFT JOIN user u ON c.{field} = u.id
                    LIMIT 5
                """).fetchall()
                print(f"  关联查询结果:")
                for row in creators:
                    print(f"    客户ID: {row['client_id']}, 创建者ID: {row['creator_id']}, 创建者用户名: {row['username']}")
            except Exception as e:
                print(f"  关联查询出错: {e}")
    
    if not existing_fields:
        print("未找到明确的创建者字段")

def check_product_creator_field(db):
    """检查product表中创建者信息的存储方式"""
    print("\n正在检查product表的创建者字段...")
    
    # 检查可能的创建者字段
    possible_fields = ['user_id', 'created_by', 'creator_id', 'creator']
    existing_fields = []
    
    # 获取表结构
    columns = db.execute("PRAGMA table_info(product)").fetchall()
    column_names = [col['name'] for col in columns]
    
    for field in possible_fields:
        if field in column_names:
            existing_fields.append(field)
            print(f"找到可能的创建者字段: {field}")
            
            # 检查字段值
            sample_values = db.execute(f"SELECT {field} FROM product LIMIT 5").fetchall()
            print(f"  字段 {field} 的示例值: {[row[0] for row in sample_values]}")
            
            # 如果字段似乎存储了user_id，尝试关联查询
            try:
                creators = db.execute(f"""
                    SELECT p.id as product_id, p.{field} as creator_id, u.username
                    FROM product p
                    LEFT JOIN user u ON p.{field} = u.id
                    LIMIT 5
                """).fetchall()
                print(f"  关联查询结果:")
                for row in creators:
                    print(f"    产品ID: {row['product_id']}, 创建者ID: {row['creator_id']}, 创建者用户名: {row['username']}")
            except Exception as e:
                print(f"  关联查询出错: {e}")
    
    if not existing_fields:
        print("未找到明确的创建者字段")

def check_table_relationships(db):
    """检查表之间的关系"""
    try:
        # 检查client和user的关系
        client_user_relation = db.execute("""
            SELECT COUNT(*) as count FROM client c
            JOIN user u ON c.user_id = u.id
        """).fetchone()
        print(f"client表和user表的连接关系: {client_user_relation['count']} 条记录")
    except Exception as e:
        print(f"检查client和user关系时出错: {e}")
    
    try:
        # 检查product和user的关系
        product_user_relation = db.execute("""
            SELECT COUNT(*) as count FROM product p
            JOIN user u ON p.user_id = u.id
        """).fetchone()
        print(f"product表和user表的连接关系: {product_user_relation['count']} 条记录")
    except Exception as e:
        print(f"检查product和user关系时出错: {e}")
    
    try:
        # 检查client_product的关系
        cp_relation = db.execute("""
            SELECT COUNT(*) as count FROM client_product cp
            JOIN client c ON cp.client_id = c.id
            JOIN product p ON cp.product_id = p.id
        """).fetchone()
        print(f"client_product与client和product的连接关系: {cp_relation['count']} 条记录")
    except Exception as e:
        print(f"检查client_product关系时出错: {e}")

if __name__ == "__main__":
    check_db_structure() 