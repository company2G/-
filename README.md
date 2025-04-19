# 禾燃客户管理系统

这是一个基于Flask的客户信息录入和管理系统，专为体重管理与健康咨询服务设计。该版本经过特别优化，兼容Python 3.13。

## 功能特点

- 用户注册和登录
- 客户档案管理
  - 基本信息录入（姓名、性别、年龄、联系方式等）
  - 饮食习惯记录
  - 身体状况记录
  - 体型数据记录
- 减脂记录档案
  - 日常饮食记录
  - 体重变化追踪
  - 排便情况记录
- 体重管理档案
  - 周期性体重管理记录
  - 身体围度变化记录

## 安装步骤

1. 克隆项目到本地

2. 创建并激活虚拟环境（可选）
```
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖
```
pip install -r requirements.txt
```

4. 运行应用（两种方式）

   a. 直接运行启动脚本（推荐）:
   ```
   python run_app.py
   ```
   
   b. 或者手动运行应用:
   ```
   python app_simple.py
   ```

5. 在浏览器中访问
```
http://127.0.0.1:5000/
```

## Python 3.13 兼容性说明

本系统提供了两个版本：

1. **原始SQLAlchemy版本** (app.py) - 需要Python 3.10/3.11运行
2. **兼容Python 3.13的SQLite版本** (app_simple.py) - 完全保留所有功能，但使用原生SQLite替代了SQLAlchemy

如果您使用的是Python 3.13，请通过`run_app.py`启动应用，它会自动使用兼容Python 3.13的版本。

## 系统要求

- Python 3.8+ (推荐使用3.10或3.11)
- Python 3.13兼容性已支持
- 现代浏览器（Chrome、Firefox、Edge等）

## 开发技术

- 后端：Flask、Flask-Login
- 前端：Bootstrap 5、Bootstrap Icons
- 数据库：SQLite 