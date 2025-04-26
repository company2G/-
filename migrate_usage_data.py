# 文件名：migrate_usage_data.py
from app_simple import app, get_db, dict_from_row  # 导入dict_from_row函数

def migrate_data():
    with app.app_context():
        db = get_db()
        
        # 检查是否存在旧的使用记录表
        old_table_exists = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='product_usage'"
        ).fetchone()
        
        if old_table_exists:
            print("发现旧的使用记录表，开始迁移数据...")
            
            # 首先检查旧表的结构
            table_info = db.execute("PRAGMA table_info(product_usage)").fetchall()
            print("旧表结构:", [col[1] for col in table_info])  # 打印列名
            
            # 获取旧表中的数据
            old_records_raw = db.execute("SELECT * FROM product_usage").fetchall()
            
            # 转换为字典列表
            old_records = [dict_from_row(record) for record in old_records_raw]
            
            if len(old_records) > 0:
                # 打印第一条记录的键
                print("记录样例键:", list(old_records[0].keys()))
            
            # 动态获取列名
            migrated_count = 0
            for record in old_records:
                try:
                    # 尝试不同可能的列名组合
                    client_product_id = record.get('client_product_id') or record.get('product_id')
                    amount_used = record.get('amount_used') or record.get('usage_amount') or 1
                    usage_date = record.get('usage_date') or 'CURRENT_TIMESTAMP'
                    notes = record.get('notes') or ''
                    user_id = record.get('user_id') or 1
                    
                    db.execute(
                        'INSERT INTO client_product_usage (client_product_id, amount_used, usage_date, notes, user_id) '
                        'VALUES (?, ?, ?, ?, ?)',
                        (client_product_id, amount_used, usage_date, notes, user_id)
                    )
                    migrated_count += 1
                except Exception as e:
                    print(f"迁移记录时出错: {e}, 记录: {record}")
            
            db.commit()
            print(f"成功迁移 {migrated_count} 条使用记录")
        else:
            print("没有发现旧的使用记录表，无需迁移数据")
        
        # 确认client_product_usage表存在
        db.execute('''
        CREATE TABLE IF NOT EXISTS client_product_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_product_id INTEGER NOT NULL,
            amount_used INTEGER NOT NULL,
            usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            user_id INTEGER NOT NULL,
            operator_id INTEGER,
            FOREIGN KEY (client_product_id) REFERENCES client_product (id),
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (operator_id) REFERENCES operators (id)
        )
        ''')
        
        # 查询是否有记录
        count = db.execute('SELECT COUNT(*) FROM client_product_usage').fetchone()[0]
        print(f"client_product_usage表中有 {count} 条记录")
        
        db.commit()
        print("确认client_product_usage表结构正确")

if __name__ == "__main__":
    migrate_data()