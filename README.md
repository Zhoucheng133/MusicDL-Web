# MusicDL Web

🏗️ 开发中 | Undeer development

sudo docker run -d --restart always -p <端口>:80 \
-v <缓存位置>:/app/cache \
-v <下载目录>:/app/downloads \
-v <用户数据>:/app/db \
zhouc1230/musicdl:latest