# 禾燃客户管理系统

禾燃客户管理系统是一个专为健康服务行业设计的客户管理解决方案，提供客户信息管理、产品管理、预约管理和统计报表等功能。

## 系统优化更新

系统进行了以下优化：

1. SQL查询优化，提高了统计功能的性能
2. 添加了异步任务处理，提高系统响应速度
3. 实现了统计报表生成功能
4. 添加了预约提醒自动/手动发送功能

## 安装依赖

```bash
pip install -r requirements.txt
```

## 初始化数据库

首次使用时需要初始化数据库：

```bash
python create_async_tables.py
python db_optimize.py
```

## 启动方式

### 1. 启动Redis（用于Celery消息队列）

在Windows系统上，推荐使用WSL或Docker运行Redis：

#### WSL方式：
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

#### Docker方式：
```bash
docker run -d -p 6379:6379 redis
```

### 2. 启动Celery Worker

```bash
celery -A app_simple.celery worker --loglevel=info
```

### 3. 启动Celery Beat（用于定时任务）

```bash
celery -A app_simple.celery beat --loglevel=info
```

### 4. 启动Web应用

```bash
python run_app_network.py
```

## 功能说明

### 统计报表生成

1. 访问【报表管理】页面
2. 选择报表类型和日期范围
3. 点击【生成报表】按钮
4. 等待报表生成完成后，点击【下载】按钮获取报表

### 预约提醒

系统会自动在每天下午6点发送第二天的预约提醒。管理员也可以在【预约管理】页面手动触发发送提醒。

## 注意事项

1. 确保Redis服务器正常运行，否则异步任务将无法执行
2. 定时任务依赖于Celery Beat服务，请确保它正常运行
3. 首次使用时，请创建reports目录用于存放生成的报表

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