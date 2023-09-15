# 打包命令
pyinstaller -i yk.ico -F -w --add-binary MyLib;MyLib  --add-data resource;resource main.py

# 脚本功能
作者的CSDN主页：https://blog.csdn.net/EXIxiaozhou；

此款脚本仅针对云创学习网平台定制的；

网站首页地址：https://yk.myunedu.com

实现了自动答题：单选题、多选题、判断题；

实现了自动上传：pdf、word、img、文本；

导入账号文件参数说明：分别点击浏览选择导入的账户文件，账号格式为:账户,密码\n；

导入答案目录参数说明：答案的目录名称要与学习平台的科目名称一一对应；

自动答题：导入账户文件和答案目录点击开始运行按钮即可；

答题数据查询：点击查询完成作业按钮、点击查询失败作业，即可显示账户作业的完成情况和失败情况；
