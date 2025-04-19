from flask_login import UserMixin
from datetime import datetime
from app import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    clients = db.relationship('Client', backref='manager', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    workplace = db.Column(db.String(200))
    
    # 饮食情况
    breakfast = db.Column(db.String(20), default='正常')  # 早餐
    lunch = db.Column(db.String(20), default='正常')  # 中餐
    dinner = db.Column(db.String(20), default='正常')  # 晚餐
    night_snack = db.Column(db.String(20), default='极少')  # 夜宵
    cold_food = db.Column(db.String(20), default='正常')  # 食物寒凉
    sweet_food = db.Column(db.String(20), default='正常')  # 甜食
    meat = db.Column(db.String(20), default='正常')  # 肉类
    alcohol = db.Column(db.String(20), default='正常')  # 饮酒
    
    # 身体状况
    constitution = db.Column(db.String(100))  # 个人体质：怕冷、怕热、发冷、发热、怕风
    water_drinking = db.Column(db.String(100))  # 饮水情况：热饮、冷饮、不渴、量多、量少
    sleep = db.Column(db.String(100))  # 睡眠情况：易睡、多梦、失眠、嗜睡
    defecation = db.Column(db.String(100))  # 大便情况：正常、便秘、拉稀、多次
    gynecology = db.Column(db.Text)  # 妇科情况
    
    # 体型数据
    weight = db.Column(db.Float)  # 体重(kg)
    height = db.Column(db.Float)  # 身高(cm)
    waist = db.Column(db.Float)  # 腰围(cm)
    hip = db.Column(db.Float)  # 臀围(cm)
    leg = db.Column(db.Float)  # 腿围(cm)
    standard_weight = db.Column(db.Float)  # 标准体重
    overweight = db.Column(db.Float)  # 超重
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 关联减脂记录和体重管理
    weight_records = db.relationship('WeightRecord', backref='client', lazy=True)
    weight_managements = db.relationship('WeightManagement', backref='client', lazy=True)
    
    def __repr__(self):
        return f'<Client {self.name}>'

class WeightRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.Date, nullable=False)
    morning_weight = db.Column(db.Float)  # 早晨体重
    breakfast = db.Column(db.Text)  # 早餐
    lunch = db.Column(db.Text)  # 中餐
    dinner = db.Column(db.Text)  # 晚餐
    defecation = db.Column(db.Boolean, default=False)  # 是否排便
    daily_change = db.Column(db.Float)  # 与前一日对比
    total_change = db.Column(db.Float)  # 与减肥前对比
    
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<WeightRecord {self.record_date}>'

class WeightManagement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sequence = db.Column(db.Integer, nullable=False)  # 次数序号
    record_date = db.Column(db.Date, nullable=False)
    before_weight = db.Column(db.Float)  # 前体重
    after_weight = db.Column(db.Float)  # 后体重
    measurements = db.Column(db.Text)  # 围度
    notes = db.Column(db.Text)  # 备注
    
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<WeightManagement {self.sequence}>' 