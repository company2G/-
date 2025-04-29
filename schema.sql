/* 数据库结构定义 */

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    name TEXT,
    phone TEXT,
    email TEXT,
    client_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 客户表
CREATE TABLE IF NOT EXISTS client (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT UNIQUE,
    email TEXT,
    address TEXT,
    birthday TEXT,
    gender TEXT,
    height INTEGER,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES user (id),
    balance REAL DEFAULT 0.0,
    discount REAL DEFAULT 1.0
);

-- 产品表
CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL,
    description TEXT,
    type TEXT CHECK(type IN ('count', 'period')),
    category TEXT,
    sessions INTEGER,
    validity_days INTEGER,
    default_count INTEGER,
    default_days INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 客户产品关联表
CREATE TABLE IF NOT EXISTS client_product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    purchase_date TEXT,
    start_date TEXT,
    remaining_count INTEGER,
    expiry_date TEXT,
    status TEXT CHECK(status IN ('active', 'expired', 'used_up')),
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES client (id),
    FOREIGN KEY (product_id) REFERENCES product (id),
    payment_method TEXT DEFAULT 'cash',  -- 'cash'现金，'balance'储值
    discount_rate REAL DEFAULT 1.0,  -- 折扣率，1.0表示无折扣
    original_price REAL,  -- 原价
    actual_paid REAL
);

-- 产品使用记录表
CREATE TABLE IF NOT EXISTS product_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_product_id INTEGER NOT NULL,
    usage_date TEXT NOT NULL,
    count_used INTEGER DEFAULT 1,
    appointment_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_product_id) REFERENCES client_product (id),
    FOREIGN KEY (appointment_id) REFERENCES appointment (id)
);

-- 体重记录表
CREATE TABLE IF NOT EXISTS weight_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    record_date TEXT NOT NULL,
    weight REAL NOT NULL,
    daily_change REAL,
    total_change REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES client (id)
);

-- 体重管理计划表
CREATE TABLE IF NOT EXISTS weight_management (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    target_weight REAL,
    start_weight REAL,
    current_weight REAL,
    status TEXT CHECK(status IN ('active', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES client (id)
);

-- 预约表
CREATE TABLE IF NOT EXISTS appointment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    service_type TEXT,
    client_product_id INTEGER,
    status TEXT CHECK(status IN ('pending', 'confirmed', 'completed', 'cancelled')) DEFAULT 'pending',
    confirmed_time TEXT,
    completed_at TEXT,
    cancelled_at TEXT,
    cancel_reason TEXT,
    additional_notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES client (id),
    FOREIGN KEY (client_product_id) REFERENCES client_product (id)
);

-- 创建一个初始管理员账户 (用户名: admin, 密码: admin123)
INSERT INTO user (username, password_hash, role) 
VALUES ('admin', 'pbkdf2:sha256:260000$qvh2IQq1d80NNR76$bb9d7c26ec5c4be68cd1ffa97a5126a84ac4ba91e851fdfbab4eba64b56e4a37', 'admin');

-- 插入预设产品
INSERT INTO product (name, description, type, default_count, default_days, category, details, price) 
VALUES 
('体验卡', '体验卡', 'count', 3, NULL, '体验卡', NULL, 99),
('全身热敷1次', '全身热敷次数卡', 'count', 1, NULL, '热敷', '全身', 68),
('全身热敷2次', '全身热敷次数卡', 'count', 2, NULL, '热敷', '全身', 128),
('塑形6选1', '塑形6选一次数卡', 'count', 1, NULL, '塑形', '腹、臀、背、大腿、小腿、胳膊', 128),
('肩颈疏通+热敷', '肩颈疏通+热敷 60分钟次数卡', 'count', 1, NULL, '疏通', '肩颈', 158),
('小套塑形10次', '小套塑形次数卡', 'count', 10, NULL, '塑形套餐', '全身可选', 1280),
('小套塑形20次', '小套塑形次数卡', 'count', 20, NULL, '塑形套餐', '全身可选', 2280),
('大套塑形30次', '大套塑形次数卡', 'count', 30, NULL, '塑形套餐', '全身可选', 3280),
('大套塑形60次', '大套塑形次数卡', 'count', 60, NULL, '塑形套餐', '全身可选', 5980),
('全身热敷30天', '全身热敷周期卡', 'period', NULL, 30, '热敷', '全身', 580),
('周卡热敷', '一周热敷周期卡', 'period', NULL, 7, '热敷', '全身', 198),
('月卡热敷', '全月热敷周期卡', 'period', NULL, 90, '热敷', '全身', 980);

-- 添加字段到用户表：增加客服角色
UPDATE user SET role = 'user' WHERE role IS NULL;

-- 创建初始管理员账户
INSERT OR IGNORE INTO user (username, password_hash, role)
VALUES ('admin', 'pbkdf2:sha256:150000$lFJVVAXa$8dd8fe5bfdfc105e8e41fe9b31a16bb4a5228876e39bdd57ac6d10f91e2b4f01', 'admin');

-- 客户表
CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  creator_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  age INTEGER,
  gender TEXT,
  phone TEXT UNIQUE NOT NULL,
  email TEXT,
  address TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  password TEXT,
  FOREIGN KEY (creator_id) REFERENCES user (id)
);

-- 产品表
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  price REAL NOT NULL,
  type TEXT NOT NULL,  -- 'period'(周期卡) or 'sessions'(次数卡)
  category TEXT NOT NULL,
  validity_days INTEGER NOT NULL DEFAULT 0,  -- 有效期天数，0表示永久有效
  sessions INTEGER,  -- 可用次数，NULL表示不限次数
  description TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 客户产品关联表
CREATE TABLE IF NOT EXISTS client_products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  purchase_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expiry_date TIMESTAMP,
  remaining_sessions INTEGER,
  price REAL NOT NULL,  -- 实际购买价格
  status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'expired', 'used_up'
  FOREIGN KEY (client_id) REFERENCES clients (id),
  FOREIGN KEY (product_id) REFERENCES products (id)
);

-- 体重记录表
CREATE TABLE IF NOT EXISTS weight_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  record_date DATE NOT NULL,
  weight REAL NOT NULL,
  daily_change REAL,  -- 日变化量
  total_change REAL,  -- 总变化量
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (client_id) REFERENCES clients (id)
);

-- 服务项目表
CREATE TABLE IF NOT EXISTS services (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  duration INTEGER NOT NULL,  -- 单位: 分钟
  category TEXT NOT NULL,  -- 服务类别
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 预约表
CREATE TABLE IF NOT EXISTS appointments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  service_id INTEGER NOT NULL,
  appointment_time TIMESTAMP NOT NULL,  -- 预约时间
  status TEXT NOT NULL,  -- 'pending', 'confirmed', 'completed', 'cancelled'
  notes TEXT,  -- 客户备注
  admin_notes TEXT,  -- 管理员备注
  created_at TIMESTAMP NOT NULL,
  confirmed_by INTEGER,  -- 确认预约的用户ID
  confirmed_at TIMESTAMP,  -- 确认时间
  completed_at TIMESTAMP,  -- 完成时间
  cancelled_at TIMESTAMP,  -- 取消时间
  cancelled_reason TEXT,  -- 取消原因
  FOREIGN KEY (client_id) REFERENCES clients (id),
  FOREIGN KEY (service_id) REFERENCES services (id),
  FOREIGN KEY (confirmed_by) REFERENCES user (id)
);

-- 预约使用的产品记录
CREATE TABLE IF NOT EXISTS appointment_products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  appointment_id INTEGER NOT NULL,
  client_product_id INTEGER NOT NULL,
  sessions_used INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (appointment_id) REFERENCES appointments (id),
  FOREIGN KEY (client_product_id) REFERENCES client_products (id)
);

-- 通知记录表
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,  -- 'email', 'sms'
  recipient TEXT NOT NULL,  -- 邮箱地址或手机号
  subject TEXT,  -- 邮件主题
  content TEXT NOT NULL,  -- 通知内容
  status TEXT NOT NULL,  -- 'sent', 'failed'
  error_message TEXT,  -- 失败原因
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP  -- 发送时间
);

-- 创建储值记录表
CREATE TABLE IF NOT EXISTS balance_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    amount REAL NOT NULL,  -- 正数表示充值，负数表示消费
    transaction_type TEXT NOT NULL,  -- 'recharge'充值，'purchase'消费，'refund'退款
    description TEXT,
    before_balance REAL,
    after_balance REAL,
    operator_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES client (id),
    FOREIGN KEY (operator_id) REFERENCES user (id)
); 