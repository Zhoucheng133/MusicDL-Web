# MusicDL Web

🏗️ 开发中 | Undeer development

sudo docker run -d --restart always -p 10123:80 \
-v /DATA/AppData/musicdl/cache:/app/cache \
-v /DATA/AppData/musicdl/downloads:/app/downloads \
-v /DATA/AppData/musicdl/db:/app/db \
--name musicdl musicdl