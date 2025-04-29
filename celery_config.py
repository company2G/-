#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery配置 - 禾燃客户管理系统异步任务处理
"""

from celery import Celery
from celery.schedules import crontab

def make_celery(app):
    """创建与Flask应用集成的Celery应用实例"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    # 配置定时任务
    celery.conf.beat_schedule = {
        'send-appointment-reminders-daily': {
            'task': 'app.send_appointment_reminders',
            'schedule': crontab(hour=18, minute=0),  # 每天下午6点发送预约提醒
        },
        'generate-daily-statistics': {
            'task': 'app.generate_daily_statistics',
            'schedule': crontab(hour=1, minute=0),  # 每天凌晨1点生成统计报告
        },
    }

    class ContextTask(celery.Task):
        """确保任务在Flask应用上下文中运行"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery 