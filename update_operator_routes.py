from app_simple import app
import re

def update_operator_routes():
    """更新app_simple.py中的操作人员相关路由"""
    
    # 读取app_simple.py文件
    with open('app_simple.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open('app_simple.py.operators_bak', 'w', encoding='utf-8') as f:
        f.write(content)
    print("创建了app_simple.py的备份")
    
    # 找到admin_operators函数
    admin_operators_pattern = r'(@app\.route\(\'/admin/operators\'\)\s+@login_required\s+@admin_required\s+def admin_operators\(\):.*?)(?=\n@app\.route|\Z)'
    admin_operators_match = re.search(admin_operators_pattern, content, re.DOTALL)
    
    if admin_operators_match:
        print("找到admin_operators函数，准备更新...")
        old_admin_operators = admin_operators_match.group(1)
        
        # 更新admin_operators函数
        new_admin_operators = """@app.route('/admin/operators')
@login_required
@admin_required
def admin_operators():
    db = get_db()
    operators = db.execute(
        'SELECT o.*, u.username, u.role FROM operators o '
        'LEFT JOIN user u ON o.user_id = u.id '
        'ORDER BY o.name'
    ).fetchall()
    
    return render_template('operators/admin_operators.html', operators=operators)"""
        
        # 替换函数
        content = content.replace(old_admin_operators, new_admin_operators)
        print("已更新admin_operators函数")
    else:
        print("未找到admin_operators函数，可能需要手动添加")
    
    # 找到add_operator函数
    add_operator_pattern = r'(@app\.route\(\'/admin/operator/add\'.*?def add_operator\(\):.*?)(?=\n@app\.route|\Z)'
    add_operator_match = re.search(add_operator_pattern, content, re.DOTALL)
    
    if add_operator_match:
        print("找到add_operator函数，准备更新...")
        old_add_operator = add_operator_match.group(1)
        
        # 更新add_operator函数
        new_add_operator = """@app.route('/admin/operator/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_operator():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form.get('position', '')
        user_id = request.form.get('user_id')
        
        # 如果user_id是空字符串，转换为None
        if user_id == '':
            user_id = None
            
        error = None
        
        if not name:
            error = '操作人员姓名不能为空'
            
        if error is None:
            db = get_db()
            db.execute(
                'INSERT INTO operators (name, position, user_id, created_by, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)',
                (name, position, user_id, g.user.id if g.user else 1)
            )
            db.commit()
            flash('操作人员添加成功')
            return redirect(url_for('admin_operators'))
            
        flash(error)
    
    # 获取所有用户列表供选择
    db = get_db()
    users = db.execute('SELECT id, username, role FROM user ORDER BY username').fetchall()
    
    return render_template('operators/operator_form.html', users=users)"""
        
        # 替换函数
        content = content.replace(old_add_operator, new_add_operator)
        print("已更新add_operator函数")
    else:
        print("未找到add_operator函数，可能需要手动添加")
    
    # 找到edit_operator函数
    edit_operator_pattern = r'(@app\.route\(\'/admin/operator/edit.*?def edit_operator\(operator_id\):.*?)(?=\n@app\.route|\Z)'
    edit_operator_match = re.search(edit_operator_pattern, content, re.DOTALL)
    
    if edit_operator_match:
        print("找到edit_operator函数，准备更新...")
        old_edit_operator = edit_operator_match.group(1)
        
        # 更新edit_operator函数
        new_edit_operator = """@app.route('/admin/operator/edit/<int:operator_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_operator(operator_id):
    db = get_db()
    operator = db.execute('SELECT * FROM operators WHERE id = ?', (operator_id,)).fetchone()
    
    if operator is None:
        abort(404, f"操作人员ID {operator_id} 不存在。")
        
    if request.method == 'POST':
        name = request.form['name']
        position = request.form.get('position', '')
        user_id = request.form.get('user_id')
        
        # 如果user_id是空字符串，转换为None
        if user_id == '':
            user_id = None
        
        error = None
        
        if not name:
            error = '操作人员姓名不能为空'
            
        if error is None:
            db = get_db()
            db.execute(
                'UPDATE operators SET name = ?, position = ?, user_id = ? WHERE id = ?',
                (name, position, user_id, operator_id)
            )
            db.commit()
            flash('操作人员信息更新成功')
            return redirect(url_for('admin_operators'))
            
        flash(error)
    
    # 获取所有用户列表供选择
    users = db.execute('SELECT id, username, role FROM user ORDER BY username').fetchall()
    
    return render_template('operators/operator_form.html', operator=operator, users=users)"""
        
        # 替换函数
        content = content.replace(old_edit_operator, new_edit_operator)
        print("已更新edit_operator函数")
    else:
        print("未找到edit_operator函数，可能需要手动添加")
    
    # 找到use_client_product函数的用户ID问题
    use_client_product_pattern = r'(db\.execute\(\s+\'INSERT INTO client_product_usage.*?g\.user\.id.*?\))'
    use_client_product_match = re.search(use_client_product_pattern, content, re.DOTALL)
    
    if use_client_product_match:
        print("找到use_client_product函数中的用户ID引用，准备修复...")
        old_code = use_client_product_match.group(1)
        
        # 修复g.user.id引用
        new_code = old_code.replace(
            "g.user.id", 
            "(g.user.id if hasattr(g, 'user') and g.user is not None else 1)"
        )
        
        # 替换函数
        content = content.replace(old_code, new_code)
        print("已修复use_client_product函数中的用户ID引用")
    else:
        print("未找到use_client_product函数中的用户ID引用，可能已修复")
    
    # 写回文件
    with open('app_simple.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已完成对app_simple.py的更新，请重启应用以应用更改")

if __name__ == "__main__":
    update_operator_routes() 