# 文件：create_operators_table.py
from app_simple import app, get_db

def update_database():
    with app.app_context():
        db = get_db()
        
        # 创建operators表
        db.execute('''
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES user (id)
        )
        ''')
        
        # 创建client_product_usage表
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
        
        db.commit()
        print("数据库更新完成！")

if __name__ == "__main__":
    update_database()