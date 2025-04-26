import sqlite3
import os

# 获取数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.sqlite')

def add_products_table():
    """仅添加产品表，不影响现有数据"""
    print(f"正在连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查product表是否已存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
    if cursor.fetchone():
        print("product表已存在，无需创建")
    else:
        print("正在创建product表...")
        cursor.execute('''
        CREATE TABLE product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            type TEXT NOT NULL,  -- 'count' 或 'period'
            category TEXT,
            details TEXT,
            count INTEGER DEFAULT 0,  -- 次数卡的使用次数
            validity_days INTEGER DEFAULT 0  -- 期限卡的有效天数
        )
        ''')
        
        # 添加一些示例产品数据（可选）
        sample_products = [
            ('【全身身材管理 】全身黑科技美体', 39.9, 'count', '热敷', '全身', 1, 0),
            ('【品质体验】三大部位 腿+腰+肩颈背', 69.9, 'count', '热敷', '腿+腰+肩颈背', 2, 0),
            ('【塑形5选1】妈妈臀/少女背/大腿/小腿/胳膊', 129.0, 'count', '塑形', '腹、臀、背、大腿、小腿、胳膊', 1, 0),
            ('【大体积】30/塑形', 8820.0, 'count', '塑形套餐', '全身可选', 30, 0),
            ('【大体积】90/热敷', 5400.0, 'period', '热敷', '全身', 0, 90),
            ('【小体积】塑形打造 美塑小套盒', 1980.0, 'count', '塑形套餐', '全身可选', 10, 0),
            ('【月卡畅做30天】全身体重管理', 980.0, 'period', '热敷', '全身', 0, 30),
            ('【王炸肩颈腰背】60分钟 肩颈/腰部疏通管理2选1+热敷放松', 69.0, 'count', '疏通', '肩颈', 1, 0),
            ('【调理专属体验】60分钟 平坦小肚子3次', 29.99, 'count', '体验卡', None, 3, 0),
            ('【超值周卡】7天全身体重管理（体验款）', 169.0, 'period', '热敷', '全身', 0, 7),
            ('大套塑形30次', 8820.0, 'count', '塑形套餐', '全身可选', 30, 0),
            ('小套塑形10次', 1980.0, 'count', '塑形套餐', '全身可选', 10, 0)
        ]
        
        cursor.executemany(
            'INSERT INTO product (name, price, type, category, details, count, validity_days) VALUES (?, ?, ?, ?, ?, ?, ?)',
            sample_products
        )
        
        print(f"已成功添加{len(sample_products)}个示例产品")
    
    # 检查client_product表是否已存在，如果不存在则创建
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client_product'")
    if not cursor.fetchone():
        print("正在创建client_product表...")
        cursor.execute('''
        CREATE TABLE client_product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            purchase_date DATE NOT NULL,
            start_date DATE,
            remaining_count INTEGER,
            expiry_date DATE,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES client (id),
            FOREIGN KEY (product_id) REFERENCES product (id)
        )
        ''')
        
        # 检查product_usage表是否已存在，如果不存在则创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_usage'")
        if not cursor.fetchone():
            print("正在创建product_usage表...")
            cursor.execute('''
            CREATE TABLE product_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_product_id INTEGER NOT NULL,
                usage_date DATE NOT NULL,
                notes TEXT,
                FOREIGN KEY (client_product_id) REFERENCES client_product (id)
            )
            ''')
    
    conn.commit()
    conn.close()
    print("数据库迁移完成！")

if __name__ == "__main__":
    add_products_table() 