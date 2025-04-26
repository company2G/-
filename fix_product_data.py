# 文件名: fix_product_data.py
from app_simple import app, get_db

def fix_product_data():
    with app.app_context():
        db = get_db()
        
        # 查看client_product_id=13的产品信息
        product = db.execute(
            'SELECT * FROM client_product WHERE id = 13'
        ).fetchone()
        
        if product:
            print("当前产品信息:", dict(product))
            
            # 检查是否有剩余次数和到期日期
            if product['remaining_amount'] is None or product['remaining_amount'] == '':
                # 从原始产品获取信息
                original_product = db.execute(
                    'SELECT * FROM product WHERE id = ?', 
                    (product['product_id'],)
                ).fetchone()
                
                if original_product:
                    # 修复剩余次数
                    remaining = original_product['total_amount']
                    print(f"设置剩余次数为: {remaining}")
                    
                    # 修复到期日期（如果为空）
                    import datetime
                    expiry_date = datetime.date.today() + datetime.timedelta(days=365)
                    expiry_str = expiry_date.isoformat()
                    print(f"设置到期日期为: {expiry_str}")
                    
                    # 更新产品信息
                    db.execute(
                        'UPDATE client_product SET remaining_amount = ?, expiry_date = ? WHERE id = ?',
                        (remaining, expiry_str, 13)
                    )
                    db.commit()
                    print("产品信息已更新")
                    
                    # 查看更新后的信息
                    updated = db.execute('SELECT * FROM client_product WHERE id = 13').fetchone()
                    print("更新后产品信息:", dict(updated))
                else:
                    print("找不到原始产品信息")
            else:
                print("产品剩余次数和到期日期正常，无需修复")
        else:
            print("找不到产品ID=13的记录")
            
            # 列出所有客户产品
            all_products = db.execute('SELECT * FROM client_product').fetchall()
            print(f"数据库中有 {len(all_products)} 条客户产品记录")
            if len(all_products) > 0:
                print("前3条记录:")
                for p in all_products[:3]:
                    print(dict(p))

if __name__ == "__main__":
    fix_product_data()