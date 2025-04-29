@echo off
echo 正在修复app_simple.py文件的编码问题...

python -c "with open('app_simple.py', 'r', encoding='utf-8', errors='replace') as f: content = f.read(); content = content.replace('浠庤〃鍗曡幏鍙栨暟鎹', '从表单获取数据').replace('楗涔犳儻', '饮食习惯').replace('韬綋鐘跺喌', '身体状况').replace('浣撻噸鐩稿叧', '体重相关').replace('鍏宠仈鎿嶄綔鍛', '关联操作员').replace('楠岃瘉鏁版嵁', '验证数据'); with open('app_simple.py', 'w', encoding='utf-8') as f: f.write(content)"

echo 正在检查540行附近的缩进问题...
python -c "with open('app_simple.py', 'r', encoding='utf-8') as f: lines = f.readlines(); lines[539] = '        gender = request.form.get(\'gender\', \'\')\n'; with open('app_simple.py', 'w', encoding='utf-8') as f: f.writelines(lines)"

echo 修复完成！
pause 