/**
 * 预约通知管理模块
 * 用于管理预约通知、轮询新预约和更新界面
 */

class AppointmentNotificationManager {
    constructor(config) {
        // 默认配置
        this.config = {
            checkInterval: 30000, // 默认30秒检查一次
            notificationSound: null,
            badgeElement: null,
            appointmentTableElement: null,
            apiBasePath: '/appointment-manager',
            ...config
        };

        // 状态变量
        this.notificationEnabled = true;
        this.lastCheckedTime = new Date().toISOString();
        this.notificationTimer = null;
        
        // 初始化
        this.requestNotificationPermission();
    }

    /**
     * 启用或禁用通知
     * @param {boolean} enabled - 是否启用通知
     */
    setNotificationEnabled(enabled) {
        this.notificationEnabled = enabled;
        
        if (enabled) {
            this.startNotificationCheck();
        } else {
            clearTimeout(this.notificationTimer);
        }
        
        return this.notificationEnabled;
    }

    /**
     * 切换通知状态
     * @returns {boolean} - 切换后的状态
     */
    toggleNotification() {
        return this.setNotificationEnabled(!this.notificationEnabled);
    }

    /**
     * 检查新预约
     * @returns {Promise} - 返回包含新预约数量的Promise
     */
    checkNewAppointments() {
        return fetch(`${this.config.apiBasePath}/check-new-appointments`)
            .then(response => response.json())
            .then(data => {
                if (data.new_appointments > 0 && this.notificationEnabled) {
                    // 播放通知音效
                    if (this.config.notificationSound) {
                        this.config.notificationSound.play().catch(e => console.log('自动播放受限:', e));
                    }
                    
                    // 显示新预约数量
                    if (this.config.badgeElement) {
                        this.config.badgeElement.textContent = data.new_appointments;
                        this.config.badgeElement.classList.remove('d-none');
                    }
                    
                    // 更新预约列表
                    this.fetchLatestAppointments();
                    
                    // 创建桌面通知
                    this.createDesktopNotification(`有 ${data.new_appointments} 个新预约等待处理`);
                }
                
                // 更新最后检查时间
                this.lastCheckedTime = data.current_time;
                
                // 安排下一次检查
                if (this.notificationEnabled) {
                    this.notificationTimer = setTimeout(() => this.checkNewAppointments(), this.config.checkInterval);
                }
                
                return data;
            })
            .catch(error => {
                console.error('检查新预约时出错:', error);
                this.notificationTimer = setTimeout(() => this.checkNewAppointments(), this.config.checkInterval);
                throw error;
            });
    }
    
    /**
     * 获取最新预约
     * @param {number} limit - 获取的预约数量
     * @returns {Promise} - 返回包含预约列表的Promise
     */
    fetchLatestAppointments(limit = 10) {
        return fetch(`${this.config.apiBasePath}/get-latest-appointments?limit=${limit}`)
            .then(response => response.json())
            .then(data => {
                if (data.appointments && data.appointments.length > 0 && this.config.appointmentTableElement) {
                    // 这里可以添加更详细的逻辑来更新表格内容
                    // 例如，比较ID，只添加新的预约
                }
                return data;
            })
            .catch(error => {
                console.error('获取最新预约时出错:', error);
                throw error;
            });
    }
    
    /**
     * 创建桌面通知
     * @param {string} message - 通知消息内容
     */
    createDesktopNotification(message) {
        if (Notification && Notification.permission === "granted") {
            new Notification("新预约提醒", {
                body: message,
                icon: "/static/images/logo.png"
            });
        }
    }
    
    /**
     * 请求通知权限
     */
    requestNotificationPermission() {
        if (Notification && Notification.permission !== "granted") {
            Notification.requestPermission();
        }
    }
    
    /**
     * 开始通知检查
     */
    startNotificationCheck() {
        // 清除现有定时器
        clearTimeout(this.notificationTimer);
        
        // 立即执行一次检查
        this.checkNewAppointments();
    }
    
    /**
     * 确认预约
     * @param {number} appointmentId - 预约ID
     * @param {string} csrfToken - CSRF Token
     * @returns {Promise} - 返回操作结果Promise
     */
    confirmAppointment(appointmentId, csrfToken) {
        return fetch(`${this.config.apiBasePath}/confirm/${appointmentId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('确认预约失败');
            }
            return response;
        });
    }
    
    /**
     * 完成预约
     * @param {number} appointmentId - 预约ID
     * @param {string} csrfToken - CSRF Token
     * @returns {Promise} - 返回操作结果Promise
     */
    completeAppointment(appointmentId, csrfToken) {
        return fetch(`${this.config.apiBasePath}/complete/${appointmentId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('标记预约完成失败');
            }
            return response;
        });
    }
    
    /**
     * 取消预约
     * @param {number} appointmentId - 预约ID
     * @param {string} reason - 取消原因
     * @param {string} csrfToken - CSRF Token
     * @returns {Promise} - 返回操作结果Promise
     */
    cancelAppointment(appointmentId, reason, csrfToken) {
        return fetch(`${this.config.apiBasePath}/cancel/${appointmentId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ reason: reason })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('取消预约失败');
            }
            return response;
        });
    }
} 