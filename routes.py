from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from models import User, Client, WeightRecord, WeightManagement
from datetime import datetime

# 添加用户加载函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def register_routes(app):
    # 首页
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    # 用户注册
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            user = User.query.filter_by(username=username).first()
            
            if user:
                flash('用户名已存在，请选择其他用户名', 'danger')
            elif password != confirm_password:
                flash('两次密码输入不一致', 'danger')
            else:
                new_user = User(username=username, password_hash=generate_password_hash(password))
                db.session.add(new_user)
                db.session.commit()
                flash('注册成功，现在可以登录了', 'success')
                return redirect(url_for('login'))
                
        return render_template('register.html')
    
    # 用户登录
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                flash('请检查您的用户名和密码并重试', 'danger')
                return redirect(url_for('login'))
                
            login_user(user, remember=remember)
            return redirect(url_for('dashboard'))
            
        return render_template('login.html')
    
    # 用户登出
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    # 控制面板
    @app.route('/dashboard')
    @login_required
    def dashboard():
        clients = Client.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', clients=clients)
    
    # 添加客户
    @app.route('/client/add', methods=['GET', 'POST'])
    @login_required
    def add_client():
        if request.method == 'POST':
            # 基本信息
            name = request.form.get('name')
            gender = request.form.get('gender')
            age = request.form.get('age')
            phone = request.form.get('phone')
            address = request.form.get('address')
            workplace = request.form.get('workplace')
            
            # 饮食情况
            breakfast = request.form.get('breakfast')
            lunch = request.form.get('lunch')
            dinner = request.form.get('dinner')
            night_snack = request.form.get('night_snack')
            cold_food = request.form.get('cold_food')
            sweet_food = request.form.get('sweet_food')
            meat = request.form.get('meat')
            alcohol = request.form.get('alcohol')
            
            # 身体状况
            constitution = ','.join(request.form.getlist('constitution'))
            water_drinking = ','.join(request.form.getlist('water_drinking'))
            sleep = ','.join(request.form.getlist('sleep'))
            defecation = ','.join(request.form.getlist('defecation'))
            gynecology = request.form.get('gynecology')
            
            # 体型数据
            weight = request.form.get('weight')
            height = request.form.get('height')
            waist = request.form.get('waist')
            hip = request.form.get('hip')
            leg = request.form.get('leg')
            
            # 计算标准体重和超重
            standard_weight = (float(height) - 105) if height else None
            overweight = (float(weight) - standard_weight) if weight and standard_weight else None
            
            new_client = Client(
                name=name,
                gender=gender,
                age=age,
                phone=phone,
                address=address,
                workplace=workplace,
                breakfast=breakfast,
                lunch=lunch,
                dinner=dinner,
                night_snack=night_snack,
                cold_food=cold_food,
                sweet_food=sweet_food,
                meat=meat,
                alcohol=alcohol,
                constitution=constitution,
                water_drinking=water_drinking,
                sleep=sleep,
                defecation=defecation,
                gynecology=gynecology,
                weight=weight,
                height=height,
                waist=waist,
                hip=hip,
                leg=leg,
                standard_weight=standard_weight,
                overweight=overweight,
                user_id=current_user.id
            )
            
            db.session.add(new_client)
            db.session.commit()
            flash('客户信息已添加成功', 'success')
            return redirect(url_for('view_client', client_id=new_client.id))
            
        return render_template('add_client.html')
    
    # 查看客户信息
    @app.route('/client/<int:client_id>')
    @login_required
    def view_client(client_id):
        client = Client.query.get_or_404(client_id)
        
        # 确保只能查看自己管理的客户
        if client.user_id != current_user.id:
            flash('无权访问此客户信息', 'danger')
            return redirect(url_for('dashboard'))
            
        return render_template('view_client.html', client=client)
    
    # 编辑客户信息
    @app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_client(client_id):
        client = Client.query.get_or_404(client_id)
        
        # 确保只能编辑自己管理的客户
        if client.user_id != current_user.id:
            flash('无权编辑此客户信息', 'danger')
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            # 基本信息
            client.name = request.form.get('name')
            client.gender = request.form.get('gender')
            client.age = request.form.get('age')
            client.phone = request.form.get('phone')
            client.address = request.form.get('address')
            client.workplace = request.form.get('workplace')
            
            # 饮食情况
            client.breakfast = request.form.get('breakfast')
            client.lunch = request.form.get('lunch')
            client.dinner = request.form.get('dinner')
            client.night_snack = request.form.get('night_snack')
            client.cold_food = request.form.get('cold_food')
            client.sweet_food = request.form.get('sweet_food')
            client.meat = request.form.get('meat')
            client.alcohol = request.form.get('alcohol')
            
            # 身体状况
            client.constitution = ','.join(request.form.getlist('constitution'))
            client.water_drinking = ','.join(request.form.getlist('water_drinking'))
            client.sleep = ','.join(request.form.getlist('sleep'))
            client.defecation = ','.join(request.form.getlist('defecation'))
            client.gynecology = request.form.get('gynecology')
            
            # 体型数据
            client.weight = request.form.get('weight')
            client.height = request.form.get('height')
            client.waist = request.form.get('waist')
            client.hip = request.form.get('hip')
            client.leg = request.form.get('leg')
            
            # 计算标准体重和超重
            client.standard_weight = (float(client.height) - 105) if client.height else None
            client.overweight = (float(client.weight) - client.standard_weight) if client.weight and client.standard_weight else None
            
            db.session.commit()
            flash('客户信息已更新成功', 'success')
            return redirect(url_for('view_client', client_id=client.id))
            
        return render_template('edit_client.html', client=client)
    
    # 删除客户
    @app.route('/client/<int:client_id>/delete', methods=['POST'])
    @login_required
    def delete_client(client_id):
        client = Client.query.get_or_404(client_id)
        
        # 确保只能删除自己管理的客户
        if client.user_id != current_user.id:
            flash('无权删除此客户信息', 'danger')
            return redirect(url_for('dashboard'))
            
        db.session.delete(client)
        db.session.commit()
        flash('客户信息已删除', 'success')
        return redirect(url_for('dashboard'))
    
    # 添加减脂记录
    @app.route('/client/<int:client_id>/weight_record/add', methods=['GET', 'POST'])
    @login_required
    def add_weight_record(client_id):
        client = Client.query.get_or_404(client_id)
        
        # 确保只能为自己管理的客户添加记录
        if client.user_id != current_user.id:
            flash('无权为此客户添加记录', 'danger')
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d').date()
            morning_weight = request.form.get('morning_weight')
            breakfast = request.form.get('breakfast')
            lunch = request.form.get('lunch')
            dinner = request.form.get('dinner')
            defecation = True if request.form.get('defecation') == 'on' else False
            
            # 计算体重变化
            daily_change = None
            total_change = None
            
            # 获取前一天的记录
            prev_record = WeightRecord.query.filter_by(client_id=client_id).order_by(WeightRecord.record_date.desc()).first()
            
            if prev_record and morning_weight:
                daily_change = float(morning_weight) - prev_record.morning_weight
                
            if client.weight and morning_weight:
                total_change = float(morning_weight) - client.weight
            
            new_record = WeightRecord(
                record_date=record_date,
                morning_weight=morning_weight,
                breakfast=breakfast,
                lunch=lunch,
                dinner=dinner,
                defecation=defecation,
                daily_change=daily_change,
                total_change=total_change,
                client_id=client_id
            )
            
            db.session.add(new_record)
            db.session.commit()
            flash('减脂记录已添加成功', 'success')
            return redirect(url_for('view_client', client_id=client_id))
            
        return render_template('add_weight_record.html', client=client)
    
    # 查看所有减脂记录
    @app.route('/client/<int:client_id>/weight_records')
    @login_required
    def view_weight_records(client_id):
        client = Client.query.get_or_404(client_id)
        
        # 确保只能查看自己管理的客户的记录
        if client.user_id != current_user.id:
            flash('无权查看此客户的记录', 'danger')
            return redirect(url_for('dashboard'))
            
        records = WeightRecord.query.filter_by(client_id=client_id).order_by(WeightRecord.record_date.desc()).all()
        return render_template('weight_records.html', client=client, records=records)
    
    # 添加体重管理记录
    @app.route('/client/<int:client_id>/weight_management/add', methods=['GET', 'POST'])
    @login_required
    def add_weight_management(client_id):
        client = Client.query.get_or_404(client_id)
        
        # 确保只能为自己管理的客户添加记录
        if client.user_id != current_user.id:
            flash('无权为此客户添加记录', 'danger')
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            # 获取最新的序号
            last_record = WeightManagement.query.filter_by(client_id=client_id).order_by(WeightManagement.sequence.desc()).first()
            sequence = 1 if not last_record else last_record.sequence + 1
            
            record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d').date()
            before_weight = request.form.get('before_weight')
            after_weight = request.form.get('after_weight')
            measurements = request.form.get('measurements')
            notes = request.form.get('notes')
            
            new_management = WeightManagement(
                sequence=sequence,
                record_date=record_date,
                before_weight=before_weight,
                after_weight=after_weight,
                measurements=measurements,
                notes=notes,
                client_id=client_id
            )
            
            db.session.add(new_management)
            db.session.commit()
            flash('体重管理记录已添加成功', 'success')
            return redirect(url_for('view_client', client_id=client_id))
            
        return render_template('add_weight_management.html', client=client)
    
    # 查看所有体重管理记录
    @app.route('/client/<int:client_id>/weight_managements')
    @login_required
    def view_weight_managements(client_id):
        client = Client.query.get_or_404(client_id)
        
        # 确保只能查看自己管理的客户的记录
        if client.user_id != current_user.id:
            flash('无权查看此客户的记录', 'danger')
            return redirect(url_for('dashboard'))
            
        managements = WeightManagement.query.filter_by(client_id=client_id).order_by(WeightManagement.sequence.asc()).all()
        return render_template('weight_managements.html', client=client, managements=managements) 