"""
这是app_simple.py文件中特定部分的修复代码。
将这段代码直接替换掉原始app_simple.py文件中的对应部分
（从"获取新增客户"段落到"获取产品添加统计"段落）
"""

# 获取新增客户和归属统计
try:
    new_clients_query = f"""
    SELECT 
        c.*, 
        u.username as user_name 
    FROM client c 
    LEFT JOIN user u ON c.user_id = u.id 
    WHERE 1=1 {client_filter}
    ORDER BY c.id DESC
    """
    
    app.logger.info(f"新增客户查询SQL: {new_clients_query}, 参数: {client_params}")
    
    new_clients = db.execute(new_clients_query, client_params).fetchall()
    new_clients = [dict_from_row(row) for row in new_clients]
    
    # 更新recent_clients变量用于模板
    recent_clients = new_clients[:10]  # 获取最近10个客户
    
    # 获取客户归属统计
    attribution_query = """
    SELECT 
        u.username as user_name, 
        COUNT(c.id) as client_count 
    FROM client c 
    JOIN user u ON c.user_id = u.id 
    GROUP BY u.id 
    ORDER BY client_count DESC
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
    
except Exception as e:
    app.logger.error(f"获取详细使用记录出错: {str(e)}")
    import traceback
    traceback.print_exc()
    detailed_usage = []

# 获取最近的使用记录（不分组）
try:
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
    app.logger.error(f"获取最近使用记录出错: {str(e)}")
    import traceback
    traceback.print_exc()
    recent_usages = []

# 获取产品添加统计
try:
    product_add_query = f"""
    SELECT 
        p.name as product_name, 
        COUNT(cp.id) as add_count 
    FROM client_product cp 
    JOIN product p ON cp.product_id = p.id 
    WHERE 1=1 {product_add_filter}
    GROUP BY p.id 
    ORDER BY add_count DESC
    """
except Exception as e:
    app.logger.error(f"获取产品添加统计出错: {str(e)}")
    product_add_query = "" 