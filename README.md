# 滚动感知站（数据查询平台）

新闻事件动态更新的查询平台，需要搭配数据库 使用   
测试阶段，需要访问链接请联系作者  
![alt text](image.png)


## 项目功能

  - **未来事件**：展示未来两周的预测事件，支持按描述、时间范围和热点等级筛选。
  - **动态新闻**：展示当天的新闻数据，支持内容和标签检索。
  - **实时分析**：从“冲突性、名人效应、突发性、经济敏感议题、社会/文化热点、科技突破、外交动态”七个维度计算热点等级。
  - **交互**：分页、自动刷新（5分钟）、删除事件（标记为不重要）。

## 更新日志
- 2024年3月14日：实现新闻滚动更新

## 技术栈

- **前端**：Vue.js + Element Plus + Axios + Day.js
- **后端**：FastAPI + Python + Uvicorn + mysql-connector-python
- **数据库**：MySQL
- **服务器**：Nginx（反向代理和静态文件服务）

## 目录结构
data_query_platform/  
├── backend.py          # 后端 API 服务  
├── fast_frontend/      # 前端 Vue 项目  
│   ├── src/           # 源代码  
│   │   ├── config.js  # API 路径配置  
│   │   ├── views/  
│   │   │   ├── FutureEvents.vue  # 未来事件页面  
│   │   │   └── News.vue          # 新闻页面  
│   └── dist/          # 构建后的静态文件  
└── README.md          # 项目说明  


## 安装与运行

### 前提条件
- **本地环境**：
  - Python 3.8+
  - Node.js 16+ 和 npm
  - MySQL 5.7+
- **服务器环境**：
  - Nginx
  - 开放端口：80（前端）、8000（后端）

### 本地开发

1. **后端**：
    ```bash
    cd data_query_platform
    pip install fastapi uvicorn mysql-connector-python
    python backend.py
    ```
    默认运行在 http://localhost:8000

2. **前端**：
   ```bash
    cd fast_frontend
    npm install
    npm run serve
   ```
    默认运行在 http://localhost:8080。

### 服务器部署
1. **后端**： 
- 安装依赖：
    ```bash
    pip3 install fastapi uvicorn mysql-connector-python
    ```

- 后台运行：
  ```bash
  nohup uvicorn backend:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
  ```

2. **前端**：  
- 构建项目：
  ```bash
  cd fast_frontend
  npm run build
  ```
- 上传 dist 到服务器：
  ```bash
  /www/wwwroot/data_query_platform/dist
  ```

3. **Nginx 配置**：  
- 示例配置（/etc/nginx/conf.d/data_query_platform.conf）：
  ```nginx
    server {
        listen 80;
        server_name 8.134.57.200;
        root /www/wwwroot/data_query_platform/dist;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api/ {
            proxy_pass http://127.0.0.1:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    ```

- 检查并重载：
  ```bash
    nginx -t
    nginx -s reload
  ```

4. **防火墙（如需外部访问后端）**：  

    ```bash
    firewall-cmd --add-port=8000/tcp --permanent
    firewall-cmd --reload
    ```


## 注意事项
- 数据库配置：修改 backend.py 中的 db_config 以匹配你的 MySQL 设置。  
- 前端 API 路径：确保 src/config.js 配置正确，开发环境用 localhost:8000，生产环境用 /api。  
- 日志：后端运行日志在 backend.log 中，可用 tail -f backend.log 查看。