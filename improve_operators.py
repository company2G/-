from app_simple import app, get_db
import datetime

def upgrade_operators_system():
    with app.app_context():
        db = get_db()
        
        # 检查operators表的当前结构
        columns = db.execute("PRAGMA table_info(operators)").fetchall()
        column_names = [col[1] for col in columns]
        print("当前operators表结构:", column_names)
        
        # 如果需要，添加user_id列
        if 'user_id' not in column_names:
            print("添加user_id列到operators表...")
            try:
                db.execute('ALTER TABLE operators ADD COLUMN user_id INTEGER')
                db.execute('CREATE INDEX IF NOT EXISTS idx_operators_user_id ON operators(user_id)')
                print("成功添加user_id列")
            except Exception as e:
                print(f"添加列失败: {e}")
        
        # 查看系统中所有用户
        users = db.execute('SELECT id, username, role FROM user').fetchall()
        print(f"系统中有 {len(users)} 个用户")
        
        # 备份现有管理员路由
        print("\n正在更新操作人员管理功能...\n")
        
        # 创建operators/admin_operators.html模板
        create_admin_operators_template()
        
        # 创建operators/operator_form.html模板
        create_operator_form_template()
        
        print("\n完成! 请重启应用以应用更改。")

def create_admin_operators_template():
    """创建operators/admin_operators.html模板"""
    template = """{% extends 'base.html' %}

{% block header %}
  <h1>{% block title %}操作人员管理{% endblock %}</h1>
{% endblock %}

{% block content %}
  <div class="container">
    <div class="row mb-4">
      <div class="col">
        <a href="{{ url_for('add_operator') }}" class="btn btn-primary">添加操作人员</a>
      </div>
    </div>
    
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">操作人员列表</h5>
      </div>
      <div class="card-body">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>ID</th>
              <th>姓名</th>
              <th>职位</th>
              <th>系统用户</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {% for operator in operators %}
              <tr>
                <td>{{ operator['id'] }}</td>
                <td>{{ operator['name'] }}</td>
                <td>{{ operator['position'] }}</td>
                <td>
                  {% if operator['username'] %}
                    {{ operator['username'] }}
                    <span class="badge bg-{{ 'danger' if operator['role'] == 'admin' else 'info' }}">
                      {{ operator['role'] }}
                    </span>
                  {% else %}
                    <span class="text-muted">未关联用户</span>
                  {% endif %}
                </td>
                <td>{{ operator['created_at'] }}</td>
                <td>
                  <a href="{{ url_for('edit_operator', operator_id=operator['id']) }}" class="btn btn-sm btn-outline-primary">编辑</a>
                  <form action="{{ url_for('delete_operator', operator_id=operator['id']) }}" method="post" class="d-inline" onsubmit="return confirm('确定删除此操作人员吗？');">
                    <button type="submit" class="btn btn-sm btn-outline-danger">删除</button>
                  </form>
                </td>
              </tr>
            {% else %}
              <tr>
                <td colspan="6" class="text-center">暂无操作人员</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
{% endblock %}"""

    # 创建模板目录
    import os
    os.makedirs('templates/operators', exist_ok=True)
    
    # 写入模板文件
    with open('templates/operators/admin_operators.html', 'w', encoding='utf-8') as f:
        f.write(template)
    
    print("创建了operators/admin_operators.html模板")

def create_operator_form_template():
    """创建operators/operator_form.html模板"""
    template = """{% extends 'base.html' %}

{% block header %}
  <h1>{% block title %}{% if operator %}编辑操作人员{% else %}添加操作人员{% endif %}{% endblock %}</h1>
{% endblock %}

{% block content %}
  <div class="container">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">{% if operator %}编辑操作人员{% else %}添加操作人员{% endif %}</h5>
      </div>
      <div class="card-body">
        <form method="post">
          <div class="mb-3">
            <label for="name" class="form-label">姓名</label>
            <input type="text" class="form-control" id="name" name="name" value="{{ operator['name'] if operator else '' }}" required>
          </div>
          
          <div class="mb-3">
            <label for="position" class="form-label">职位</label>
            <input type="text" class="form-control" id="position" name="position" value="{{ operator['position'] if operator else '' }}">
          </div>
          
          <div class="mb-3">
            <label for="user_id" class="form-label">关联系统用户</label>
            <select class="form-control" id="user_id" name="user_id">
              <option value="">-- 不关联用户 --</option>
              {% for user in users %}
                <option value="{{ user['id'] }}" {% if operator and operator['user_id'] == user['id'] %}selected{% endif %}>
                  {{ user['username'] }} ({{ user['role'] }})
                </option>
              {% endfor %}
            </select>
            <small class="form-text text-muted">
              关联用户后，该用户可以被选为操作人员。
            </small>
          </div>
          
          <div class="d-flex justify-content-between">
            <a href="{{ url_for('admin_operators') }}" class="btn btn-secondary">返回</a>
            <button type="submit" class="btn btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
{% endblock %}"""

    # 写入模板文件
    with open('templates/operators/operator_form.html', 'w', encoding='utf-8') as f:
        f.write(template)
    
    print("创建了operators/operator_form.html模板")

if __name__ == "__main__":
    upgrade_operators_system() 