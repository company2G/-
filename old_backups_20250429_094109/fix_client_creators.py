"""修复客户创建者数据脚本"""
from app_simple import get_db

def fix_client_creators():
    db = get_db()
    # 查找所有客户记录
    clients = db.execute('SELECT * FROM client').fetchall()
    
    for client in clients:
        if client['user_id'] and len(str(client['user_id'])) > 5:  # 可能是错误存储的手机号
            # 这里需要设置一个合理的默认用户ID，或者根据其他逻辑确定
            # 例如设置为ID为1的管理员用户
            db.execute('UPDATE client SET user_id = ? WHERE id = ?', (1, client['id']))
    
    db.commit()
    print("已完成客户创建者数据修复")

if __name__ == '__main__':
    fix_client_creators() 