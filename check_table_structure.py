from app_simple import app, get_db

def check_table_structure():
    with app.app_context():
        db = get_db()
        
        # 检查weight_management表的结构
        print("===== weight_management表结构 =====")
        table_info = db.execute('PRAGMA table_info(weight_management)').fetchall()
        for col in table_info:
            print(f"列名: {col['name']}, 类型: {col['type']}, 非空: {col['notnull']}, 默认值: {col['dflt_value']}")
        
        # 检查是否有记录
        print("\n===== weight_management表数据样例 =====")
        sample = db.execute('SELECT * FROM weight_management LIMIT 1').fetchone()
        if sample:
            for key in sample.keys():
                print(f"{key}: {sample[key]}")
        else:
            print("表中没有数据")

if __name__ == "__main__":
    check_table_structure() 