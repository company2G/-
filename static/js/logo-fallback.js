/**
 * logo-fallback.js
 * 当logo图像无法加载时，提供文本替代
 */
document.addEventListener('DOMContentLoaded', function() {
    // 查找可能的logo图像
    const logoImages = document.querySelectorAll('.logo-image, .navbar-brand img, header img[alt*="logo" i]');
    
    logoImages.forEach(img => {
        // 检查图片是否已完成加载
        if (img.complete && img.naturalWidth === 0) {
            // 图片已加载但无效
            replaceWithTextLogo(img);
        } else if (!img.complete) {
            // 图片尚未加载完，添加错误处理
            img.addEventListener('error', function() {
                replaceWithTextLogo(img);
            });
        }
    });
    
    // 尝试查找特定ID的logo
    const specificLogo = document.getElementById('site-logo');
    if (specificLogo && specificLogo.tagName === 'IMG') {
        if (specificLogo.complete && specificLogo.naturalWidth === 0) {
            replaceWithTextLogo(specificLogo);
        } else if (!specificLogo.complete) {
            specificLogo.addEventListener('error', function() {
                replaceWithTextLogo(specificLogo);
            });
        }
    }
    
    /**
     * 将图像元素替换为文本logo
     * @param {HTMLImageElement} imgElement - 要替换的图像元素
     */
    function replaceWithTextLogo(imgElement) {
        // 尝试加载默认logo
        const defaultLogo = new Image();
        defaultLogo.src = '/static/images/default-logo.png';
        
        defaultLogo.onload = function() {
            // 如果默认logo存在且有效，使用它
            imgElement.src = defaultLogo.src;
        };
        
        defaultLogo.onerror = function() {
            // 创建文本logo
            const textLogo = document.createElement('span');
            textLogo.className = 'text-logo';
            textLogo.innerHTML = '<span style="color:#4CAF50">禾燃</span>客户管理';
            textLogo.style.fontFamily = '"Microsoft YaHei", "微软雅黑", "Heiti SC", "黑体-简", Arial, sans-serif';
            textLogo.style.fontSize = '1.5rem';
            textLogo.style.fontWeight = 'bold';
            textLogo.style.whiteSpace = 'nowrap';
            textLogo.style.display = 'inline-block';
            
            // 替换图像元素
            const parent = imgElement.parentNode;
            parent.replaceChild(textLogo, imgElement);
            
            // 如果父元素是链接，确保链接样式正确
            if (parent.tagName === 'A') {
                parent.style.textDecoration = 'none';
                parent.style.color = 'inherit';
            }
        };
    }
}); 