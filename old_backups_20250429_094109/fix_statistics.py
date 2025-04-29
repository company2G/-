# 修复app_simple.py中的嵌套try-except结构问题

"""
此文件包含用于修复app_simple.py中获取详细使用记录部分的代码片段。
问题是在"获取新增客户和归属统计"的try-except块内嵌套了"获取详细使用记录"的try块，
但没有为其添加单独的except块，导致静态代码分析工具报错。

修复方法是：将"获取详细使用记录"部分从外部try块中移出，并为其添加单独的except块。
"""

# 原始代码片段 (app_simple.py 2740行左右)
'''
        attribution_stats = db.execute(attribution_query).fetchall()
        attribution_stats = [dict_from_row(row) for row in attribution_stats]
        
        # 更新creator_stats变量用于模板
        creator_stats = attribution_stats
        
        # 获取详细使用记录
        try:
            # 先获取来自product_usage表的记录
            pu_detailed_query = f"""
            SELECT 
                pu.id as record_id,
                c.id as client_id,
                c.name as client_name,
                p.id as product_id,
                p.name as product_name,
                cp.price as price,
                cp.purchase_date as purchase_date,
                o.id as operator_id,
                o.name as operator_name,
                o.position as operator_position,
                COUNT(pu.id) as usage_times,
                SUM(pu.count_used) as amount_used,
                MAX(pu.usage_date) as last_usage_date,
                u.username as created_by
            FROM product_usage pu 
            JOIN client_product cp ON pu.client_product_id = cp.id 
            JOIN client c ON cp.client_id = c.id 
            JOIN product p ON cp.product_id = p.id 
            JOIN operators o ON pu.operator_id = o.id 
            LEFT JOIN user u ON c.user_id = u.id 
            WHERE 1=1 {product_usage_filter}
            GROUP BY cp.id, o.id 
            ORDER BY last_usage_date DESC
            LIMIT 100
            """
            
            app.logger.info(f"详细使用记录查询SQL (product_usage): {pu_detailed_query}, 参数: {pu_params}")
            
            pu_detailed_usage = db.execute(pu_detailed_query, pu_params).fetchall()
            pu_detailed_usage = [dict_from_row(row) for row in pu_detailed_usage]
            
            # 再获取来自client_product_usage表的记录
            cpu_detailed_query = f"""
            SELECT 
                cpu.id as record_id,
                c.id as client_id,
                c.name as client_name,
                p.id as product_id,
                p.name as product_name,
                cp.price as price,
                cp.purchase_date as purchase_date,
                o.id as operator_id,
                o.name as operator_name,
                o.position as operator_position,
                COUNT(cpu.id) as usage_times,
                SUM(cpu.amount_used) as amount_used,
                MAX(cpu.usage_date) as last_usage_date,
                u.username as created_by
            FROM client_product_usage cpu 
            JOIN client_product cp ON cpu.client_product_id = cp.id 
            JOIN client c ON cp.client_id = c.id 
            JOIN product p ON cp.product_id = p.id 
            JOIN operators o ON cpu.operator_id = o.id 
            LEFT JOIN user u ON c.user_id = u.id 
            WHERE 1=1 {client_product_usage_filter}
            GROUP BY cp.id, o.id 
            ORDER BY last_usage_date DESC
            LIMIT 100
            """
            
            app.logger.info(f"详细使用记录查询SQL (client_product_usage): {cpu_detailed_query}, 参数: {cpu_params}")
            
            cpu_detailed_usage = db.execute(cpu_detailed_query, cpu_params).fetchall()
            cpu_detailed_usage = [dict_from_row(row) for row in cpu_detailed_usage]
            
            # 合并两个表的记录
            detailed_usage = pu_detailed_usage + cpu_detailed_usage
            
            # 按最近使用日期排序
            detailed_usage.sort(key=lambda x: x['last_usage_date'] if x['last_usage_date'] else '', reverse=True)
            
            # 限制返回的记录数
            detailed_usage = detailed_usage[:100]
            
            # 获取最近的使用记录（不分组）
            recent_usages_query = f"""
            SELECT 
                'product_usage' as source_table,
                pu.id as id,
                c.name as client_name,
                p.name as product_name,
                pu.count_used as amount_used,
                pu.usage_date as usage_date,
                o.name as operator_name
            FROM product_usage pu 
            JOIN client_product cp ON pu.client_product_id = cp.id 
            JOIN client c ON cp.client_id = c.id 
            JOIN product p ON cp.product_id = p.id 
            JOIN operators o ON pu.operator_id = o.id 
            WHERE 1=1 {product_usage_filter}
            UNION ALL
            SELECT 
                'client_product_usage' as source_table,
                cpu.id as id,
                c.name as client_name,
                p.name as product_name,
                cpu.amount_used as amount_used,
                cpu.usage_date as usage_date,
                o.name as operator_name
            FROM client_product_usage cpu 
            JOIN client_product cp ON cpu.client_product_id = cp.id 
            JOIN client c ON cp.client_id = c.id 
            JOIN product p ON cp.product_id = p.id 
            JOIN operators o ON cpu.operator_id = o.id 
            WHERE 1=1 {client_product_usage_filter}
            ORDER BY usage_date DESC
            LIMIT 10
            """
            
            recent_usages = db.execute(recent_usages_query, pu_params + cpu_params).fetchall()
            recent_usages = [dict_from_row(row) for row in recent_usages]
        
    except Exception as e:
        app.logger.error(f"获取客户统计出错: {str(e)}")
        new_clients = []
        attribution_stats = []
        detailed_usage = []
        recent_usages = []
'''

# 修复后的代码片段
"""
        attribution_stats = db.execute(attribution_query).fetchall()
        attribution_stats = [dict_from_row(row) for row in attribution_stats]
        
        # 更新creator_stats变量用于模板
        creator_stats = attribution_stats
        
    except Exception as e:
        app.logger.error(f"获取客户统计出错: {str(e)}")
        new_clients = []
        attribution_stats = []
        creator_stats = []
    
    # 获取详细使用记录
    try:
        # 先获取来自product_usage表的记录
        pu_detailed_query = f\"\"\"
        SELECT 
            pu.id as record_id,
            c.id as client_id,
            c.name as client_name,
            p.id as product_id,
            p.name as product_name,
            cp.price as price,
            cp.purchase_date as purchase_date,
            o.id as operator_id,
            o.name as operator_name,
            o.position as operator_position,
            COUNT(pu.id) as usage_times,
            SUM(pu.count_used) as amount_used,
            MAX(pu.usage_date) as last_usage_date,
            u.username as created_by
        FROM product_usage pu 
        JOIN client_product cp ON pu.client_product_id = cp.id 
        JOIN client c ON cp.client_id = c.id 
        JOIN product p ON cp.product_id = p.id 
        JOIN operators o ON pu.operator_id = o.id 
        LEFT JOIN user u ON c.user_id = u.id 
        WHERE 1=1 {product_usage_filter}
        GROUP BY cp.id, o.id 
        ORDER BY last_usage_date DESC
        LIMIT 100
        \"\"\"
        
        app.logger.info(f"详细使用记录查询SQL (product_usage): {pu_detailed_query}, 参数: {pu_params}")
        
        pu_detailed_usage = db.execute(pu_detailed_query, pu_params).fetchall()
        pu_detailed_usage = [dict_from_row(row) for row in pu_detailed_usage]
        
        # 再获取来自client_product_usage表的记录
        cpu_detailed_query = f\"\"\"
        SELECT 
            cpu.id as record_id,
            c.id as client_id,
            c.name as client_name,
            p.id as product_id,
            p.name as product_name,
            cp.price as price,
            cp.purchase_date as purchase_date,
            o.id as operator_id,
            o.name as operator_name,
            o.position as operator_position,
            COUNT(cpu.id) as usage_times,
            SUM(cpu.amount_used) as amount_used,
            MAX(cpu.usage_date) as last_usage_date,
            u.username as created_by
        FROM client_product_usage cpu 
        JOIN client_product cp ON cpu.client_product_id = cp.id 
        JOIN client c ON cp.client_id = c.id 
        JOIN product p ON cp.product_id = p.id 
        JOIN operators o ON cpu.operator_id = o.id 
        LEFT JOIN user u ON c.user_id = u.id 
        WHERE 1=1 {client_product_usage_filter}
        GROUP BY cp.id, o.id 
        ORDER BY last_usage_date DESC
        LIMIT 100
        \"\"\"
        
        app.logger.info(f"详细使用记录查询SQL (client_product_usage): {cpu_detailed_query}, 参数: {cpu_params}")
        
        cpu_detailed_usage = db.execute(cpu_detailed_query, cpu_params).fetchall()
        cpu_detailed_usage = [dict_from_row(row) for row in cpu_detailed_usage]
        
        # 合并两个表的记录
        detailed_usage = pu_detailed_usage + cpu_detailed_usage
        
        # 按最近使用日期排序
        detailed_usage.sort(key=lambda x: x['last_usage_date'] if x['last_usage_date'] else '', reverse=True)
        
        # 限制返回的记录数
        detailed_usage = detailed_usage[:100]
        
    except Exception as e:
        app.logger.error(f"获取详细使用记录出错: {str(e)}")
        import traceback
        traceback.print_exc()
        detailed_usage = []
    
    # 获取最近的使用记录（不分组）
    try:
        recent_usages_query = f\"\"\"
        SELECT 
            'product_usage' as source_table,
            pu.id as id,
            c.name as client_name,
            p.name as product_name,
            pu.count_used as amount_used,
            pu.usage_date as usage_date,
            o.name as operator_name
        FROM product_usage pu 
        JOIN client_product cp ON pu.client_product_id = cp.id 
        JOIN client c ON cp.client_id = c.id 
        JOIN product p ON cp.product_id = p.id 
        JOIN operators o ON pu.operator_id = o.id 
        WHERE 1=1 {product_usage_filter}
        UNION ALL
        SELECT 
            'client_product_usage' as source_table,
            cpu.id as id,
            c.name as client_name,
            p.name as product_name,
            cpu.amount_used as amount_used,
            cpu.usage_date as usage_date,
            o.name as operator_name
        FROM client_product_usage cpu 
        JOIN client_product cp ON cpu.client_product_id = cp.id 
        JOIN client c ON cp.client_id = c.id 
        JOIN product p ON cp.product_id = p.id 
        JOIN operators o ON cpu.operator_id = o.id 
        WHERE 1=1 {client_product_usage_filter}
        ORDER BY usage_date DESC
        LIMIT 10
        \"\"\"
        
        recent_usages = db.execute(recent_usages_query, pu_params + cpu_params).fetchall()
        recent_usages = [dict_from_row(row) for row in recent_usages]
        
    except Exception as e:
        app.logger.error(f"获取最近使用记录出错: {str(e)}")
        import traceback
        traceback.print_exc()
        recent_usages = []
""" 