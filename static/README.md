# 禾燃客户管理系统静态资源

本目录包含禾燃客户管理系统所需的静态资源文件。

## 必需的静态文件

系统需要以下CSS和JavaScript文件：

### CSS 文件
- `css/bootstrap.min.css` (Bootstrap 4.5.2或更高版本)
- `css/custom.css` (自定义样式)

### JavaScript 文件
- `js/jquery-3.5.1.min.js` (jQuery 3.5.1或更高版本)
- `js/bootstrap.bundle.min.js` (Bootstrap JS包含Popper.js)

## 获取必要文件

您可以通过以下方式获取所需的库文件：

### 方法1：从CDN下载
1. Bootstrap CSS: https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/css/bootstrap.min.css
2. jQuery: https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.min.js
3. Bootstrap JS: https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js

### 方法2：使用包管理器
如果您使用npm或yarn，可以运行以下命令：

```bash
npm install bootstrap@4.5.2 jquery@3.5.1
# 或者
yarn add bootstrap@4.5.2 jquery@3.5.1
```

然后从`node_modules`目录复制相应文件到此静态目录。

## 目录结构

```
static/
  ├── css/
  │   ├── bootstrap.min.css
  │   └── custom.css
  ├── js/
  │   ├── jquery-3.5.1.min.js
  │   └── bootstrap.bundle.min.js
  ├── images/
  │   ├── logo.png
  │   └── default-logo.png
  └── README.md
```

## 临时解决方案

如果您暂时无法获取以上文件，可以在模板中使用CDN链接：

```html
<!-- 在<head>中添加 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/css/bootstrap.min.css">

<!-- 在</body>前添加 -->
<script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
```

## 自定义样式

`custom.css`包含系统专用样式，请勿删除或替换此文件。

## 音频资源

- `sounds/new_appointment_notification.mp3` - 新预约通知声音
  - 这是一个占位符文件，需要替换为实际的MP3格式音频文件
  - 建议使用清晰、友好的提示音，文件大小应小于100KB

## 替换音频文件

要替换预约通知音频，请准备一个MP3格式的音频文件，并将其命名为`new_appointment_notification.mp3`，然后放置在`/static/sounds/`目录下。

## 自定义其他静态资源

可以按需添加或修改其他静态资源，例如：

- 添加自定义CSS样式表
- 添加自定义JavaScript脚本
- 添加系统图标或图像

添加后，可以在模板中通过`{{ url_for('static', filename='path/to/file') }}`引用这些资源。 