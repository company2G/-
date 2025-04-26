from app_simple import app
import re

def update_statistics():
    """更新统计报表，添加操作人员使用统计"""
    
    # 读取app_simple.py文件
    with open('app_simple.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open('app_simple.py.stats_bak', 'w', encoding='utf-8') as f:
        f.write(content)
    print("创建了app_simple.py的备份")
    
    # 找到admin_statistics函数
    stats_pattern = r'(@app\.route\(\'/admin/statistics\'.*?def admin_statistics\(\):.*?)(?=\n@app\.route|\Z)'
    stats_match = re.search(stats_pattern, content, re.DOTALL)
    
    if stats_match:
        print("找到admin_statistics函数，准备更新...")
        old_stats = stats_match.group(1)
        
        # 更新统计函数，添加操作人员使用统计
        new_stats = """@app.route('/admin/statistics')
@login_required
@admin_required
def admin_statistics():
    db = get_db()
    
    # 获取筛选参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 构建日期筛选条件
    date_filter = ''
    params = []
    
    if start_date:
        date_filter += ' AND date(p.created_at) >= ?'
        params.append(start_date)
    
    if end_date:
        date_filter += ' AND date(p.created_at) <= ?'
        params.append(end_date)
    
    # 新增产品统计
    new_products = db.execute(
        'SELECT p.*, u.username as creator_name '
        'FROM product p '
        'JOIN user u ON p.created_by = u.id '
        f'WHERE 1=1 {date_filter} '
        'ORDER BY p.created_at DESC', 
        params
    ).fetchall()
    
    # 产品使用统计
    usage_filter = ''
    usage_params = []
    
    if start_date:
        usage_filter += ' AND date(cpu.usage_date) >= ?'
        usage_params.append(start_date)
    
    if end_date:
        usage_filter += ' AND date(cpu.usage_date) <= ?'
        usage_params.append(end_date)
    
    product_usage = db.execute(
        'SELECT p.name, COUNT(cpu.id) as usage_count, SUM(cpu.amount_used) as total_used '
        'FROM client_product_usage cpu '
        'JOIN client_product cp ON cpu.client_product_id = cp.id '
        'JOIN product p ON cp.product_id = p.id '
        f'WHERE 1=1 {usage_filter} '
        'GROUP BY p.id '
        'ORDER BY total_used DESC',
        usage_params
    ).fetchall()
    
    # 操作人员使用统计
    operator_usage = db.execute(
        'SELECT o.id, o.name as operator_name, o.position, '
        'COUNT(cpu.id) as usage_count, SUM(cpu.amount_used) as total_used, '
        'COUNT(DISTINCT cp.client_id) as client_count, '
        'COUNT(DISTINCT cp.product_id) as product_type_count '
        'FROM client_product_usage cpu '
        'JOIN operators o ON cpu.operator_id = o.id '
        'JOIN client_product cp ON cpu.client_product_id = cp.id '
        f'WHERE 1=1 {usage_filter} '
        'GROUP BY o.id '
        'ORDER BY total_used DESC',
        usage_params
    ).fetchall()
    
    # 无操作人员的使用记录统计（按记录人统计）
    no_operator_usage = db.execute(
        'SELECT u.id, u.username, u.role, '
        'COUNT(cpu.id) as usage_count, SUM(cpu.amount_used) as total_used, '
        'COUNT(DISTINCT cp.client_id) as client_count '
        'FROM client_product_usage cpu '
        'JOIN user u ON cpu.user_id = u.id '
        'JOIN client_product cp ON cpu.client_product_id = cp.id '
        f'WHERE cpu.operator_id IS NULL {usage_filter} '
        'GROUP BY u.id '
        'ORDER BY total_used DESC',
        usage_params
    ).fetchall()
    
    # 新增客户统计
    client_filter = ''
    client_params = []
    
    if start_date:
        client_filter += ' AND date(c.created_at) >= ?'
        client_params.append(start_date)
    
    if end_date:
        client_filter += ' AND date(c.created_at) <= ?'
        client_params.append(end_date)
    
    new_clients = db.execute(
        'SELECT c.*, u.username as creator_name '
        'FROM client c '
        'JOIN user u ON c.created_by = u.id '
        f'WHERE 1=1 {client_filter} '
        'ORDER BY c.created_at DESC',
        client_params
    ).fetchall()
    
    # 归因统计 - 哪个员工带来了多少新客户
    attribution_stats = db.execute(
        'SELECT u.username, COUNT(c.id) as client_count '
        'FROM client c '
        'JOIN user u ON c.created_by = u.id '
        f'WHERE 1=1 {client_filter} '
        'GROUP BY c.created_by '
        'ORDER BY client_count DESC',
        client_params
    ).fetchall()
    
    return render_template(
        'admin/statistics.html',
        new_products=new_products,
        product_usage=product_usage,
        operator_usage=operator_usage,
        no_operator_usage=no_operator_usage,
        new_clients=new_clients,
        attribution_stats=attribution_stats,
        start_date=start_date,
        end_date=end_date
    )"""
        
        # 替换函数
        content = content.replace(old_stats, new_stats)
        print("已更新admin_statistics函数")
    else:
        print("未找到admin_statistics函数，请检查代码")
    
    # 写回文件
    with open('app_simple.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 更新统计模板，添加操作人员统计部分
    update_statistics_template()
    
    print("已完成对统计功能的更新，请重启应用以应用更改")

def update_statistics_template():
    """更新统计模板，添加操作人员统计部分"""
    
    try:
        # 先检查现有模板
        with open('templates/admin/statistics.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 创建备份
        with open('templates/admin/statistics.html.bak', 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # 查找产品使用统计部分
        product_usage_pattern = r'(<!-- 产品使用统计.*?</div>\s*</div>)'
        product_usage_match = re.search(product_usage_pattern, template_content, re.DOTALL)
        
        if product_usage_match:
            product_usage_section = product_usage_match.group(1)
            
            # 创建操作人员使用统计部分
            operator_usage_section = """<!-- 操作人员使用统计 -->
  <div class="card mb-4">
    <div class="card-header bg-primary text-white">
      <h5 class="mb-0">操作人员使用统计</h5>
    </div>
    <div class="card-body">
      <h6 class="card-subtitle mb-3">有操作人员的使用记录</h6>
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>操作人员</th>
              <th>职位</th>
              <th>使用次数</th>
              <th>总计用量</th>
              <th>服务客户数</th>
              <th>产品种类数</th>
            </tr>
          </thead>
          <tbody>
            {% for usage in operator_usage %}
              <tr>
                <td>{{ usage['operator_name'] }}</td>
                <td>{{ usage['position'] or '' }}</td>
                <td>{{ usage['usage_count'] }}</td>
                <td>{{ usage['total_used'] }}</td>
                <td>{{ usage['client_count'] }}</td>
                <td>{{ usage['product_type_count'] }}</td>
              </tr>
            {% else %}
              <tr>
                <td colspan="6" class="text-center">无数据</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      
      <h6 class="card-subtitle mb-3 mt-4">无操作人员的使用记录（按记录人统计）</h6>
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>记录人</th>
              <th>角色</th>
              <th>使用次数</th>
              <th>总计用量</th>
              <th>服务客户数</th>
            </tr>
          </thead>
          <tbody>
            {% for usage in no_operator_usage %}
              <tr>
                <td>{{ usage['username'] }}</td>
                <td>
                  <span class="badge bg-{{ 'danger' if usage['role'] == 'admin' else 'info' }}">
                    {{ usage['role'] }}
                  </span>
                </td>
                <td>{{ usage['usage_count'] }}</td>
                <td>{{ usage['total_used'] }}</td>
                <td>{{ usage['client_count'] }}</td>
              </tr>
            {% else %}
              <tr>
                <td colspan="5" class="text-center">无数据</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>"""
            
            # 在产品使用统计后插入操作人员统计
            modified_template = template_content.replace(
                product_usage_section,
                product_usage_section + "\n\n" + operator_usage_section
            )
            
            # 写回文件
            with open('templates/admin/statistics.html', 'w', encoding='utf-8') as f:
                f.write(modified_template)
            
            print("已更新统计模板，添加了操作人员使用统计部分")
        else:
            print("未找到产品使用统计部分，请检查模板")
    except FileNotFoundError:
        print("未找到统计模板文件，请确保templates/admin/statistics.html存在")
    except Exception as e:
        print(f"更新模板时出错: {e}")

if __name__ == "__main__":
    update_statistics() 