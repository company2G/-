import sqlite3

def clear_client_data():
    """清除所有客户相关数据，包括产品购买和使用记录"""
    conn = sqlite3.connect('database.db')  # 连接到您的数据库
    cursor = conn.cursor()
    
    try:
        # 开始事务
        cursor.execute('BEGIN TRANSACTION')
        
        # 首先删除依赖于client_id或client_product_id的记录
        print("删除预约记录...")
        cursor.execute('DELETE FROM appointment')
        
        print("删除客户体重记录...")
        cursor.execute('DELETE FROM weight_record')
        
        print("删除客户体重管理记录...")
        cursor.execute('DELETE FROM weight_management')
        
        print("删除通知日志...")
        cursor.execute('DELETE FROM notification_logs')
        
        print("删除客户设置...")
        cursor.execute('DELETE FROM client_settings')
        
        # 删除产品使用记录
        print("删除产品使用记录...")
        cursor.execute('DELETE FROM product_usage')
        cursor.execute('DELETE FROM client_product_usage')
        
        # 删除客户产品关联
        print("删除客户产品记录...")
        cursor.execute('DELETE FROM client_product')
        
        # 最后删除客户记录
        print("删除客户记录...")
        cursor.execute('DELETE FROM client')
        
        # 提交事务
        conn.commit()
        print("所有客户数据已成功清除！")
        
    except Exception as e:
        # 出错时回滚事务
        conn.rollback()
        print(f"清除数据时出错: {e}")
    finally:
        # 关闭连接
        conn.close()

if __name__ == "__main__":
    # 执行前确认
    confirm = input("警告: 此操作将删除所有客户和相关记录，且无法恢复！确定要继续吗？(y/n): ")
    if confirm.lower() == 'y':
        clear_client_data()
    else:
        print("操作已取消")