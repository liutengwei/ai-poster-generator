# AI 宣传素材智能生成系统 - 部署文档

## 一、项目简介

基于 AI 的党政宣传素材智能排版生成系统，支持海报、公众号推文、内部简报三种素材类型的一键生成与导出。

**GitHub 仓库**：https://github.com/liutengwei/ai-poster-generator

---

## 二、技术栈

| 端 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + TypeScript + TailwindCSS + Pinia |
| 后端 | Python 3.11 + FastAPI + OpenAI SDK + ReportLab + Playwright |
| AI 模型 | MiniMax-M2.7 |

---

## 三、项目结构

```
ai-poster-generator/
├── src/                          # 前端源码
│   ├── api/
│   │   └── generate.ts          # API 请求封装
│   ├── components/
│   │   ├── InputForm.vue        # 表单输入组件
│   │   └── PreviewPanel.vue     # 预览与导出组件
│   ├── stores/
│   │   └── generate.ts         # 状态管理
│   ├── views/
│   │   ├── Create.vue           # 创作页面
│   │   └── History.vue          # 历史记录页面
│   ├── router/
│   │   └── index.ts            # 路由配置
│   ├── App.vue
│   ├── main.ts
│   └── style.css
├── backend/
│   ├── routers/
│   │   └── generate.py         # 生成排版/导出接口
│   ├── templates/               # HTML 导出模板
│   │   ├── poster_formal.html
│   │   ├── article_wechat.html
│   │   └── poster_lively.html
│   ├── main.py                 # FastAPI 入口
│   └── requirements.txt        # Python 依赖
├── public/
├── package.json
├── vite.config.ts
└── DEPLOY.md
```

---

## 四、快速部署

### 4.1 前端部署

```bash
# 克隆项目
git clone https://github.com/liutengwei/ai-poster-generator.git
cd ai-poster-generator

# 安装依赖
npm install

# 开发模式启动（前端 http://localhost:5173）
npm run dev
```

### 4.2 后端部署

```bash
# 进入后端目录
cd backend

# 安装 Python 依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入自己的 MINIMAX_API_KEY

# 启动服务（后端 http://localhost:8000）
py main.py
# 或使用 uvicorn
py -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)"
```

---

## 五、环境变量配置

在后端目录创建 `backend/.env` 文件，内容如下：

```env
# MiniMax API Key（必填）
# 申请地址：https://www.minimaxi.com/
MINIMAX_API_KEY=你的MiniMax_API密钥
```

**重要**：`.env` 文件不要提交到 Git，已在 `.gitignore` 中忽略。

---

## 六、API 接口文档

### 6.1 生成排版方案

```
POST http://localhost:8000/api/generate/layout
Content-Type: application/json
```

**请求体示例**：

```json
{
  "type": "poster",
  "title": "党建工作年度报告",
  "content": "2024年，在上级党委的坚强领导下...",
  "image_count": 2,
  "image_sizes": [
    {"index": 0, "ratio": "landscape"},
    {"index": 1, "ratio": "portrait"}
  ]
}
```

**响应示例**：

```json
{
  "layout": [
    {"type": "text", "content": "党建工作年度报告", "style": "title"},
    {"type": "image", "image_index": 0, "position": "hero", "size": "full", "caption": ""},
    {"type": "text", "content": "2024年，在上级党委的坚强领导下...", "style": "body"},
    {"type": "image", "image_index": 1, "position": "inline", "size": "half", "caption": "图注"}
  ],
  "reasoning": "首图横向全宽展示，正文分段清晰..."
}
```

### 6.2 导出 Word

```
POST http://localhost:8000/api/export/word
Content-Type: application/json
```

**请求体示例**：

```json
{
  "title": "标题",
  "content": "正文内容",
  "layout": [
    {"type": "text", "content": "标题", "style": "title"},
    {"type": "image", "image_index": 0, "position": "hero", "size": "full"}
  ],
  "images": [
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA..."
  ]
}
```

**响应**：返回 `.docx` 文件（Blob）

### 6.3 导出 PDF

```
POST http://localhost:8000/api/export/pdf
Content-Type: application/json
```

**请求体**：同 Word

**响应**：返回 `.pdf` 文件（Blob）

### 6.4 健康检查

```
GET http://localhost:8000/health
```

**响应**：`{"status": "ok"}`

### 6.5 API 文档

启动后端后访问：http://localhost:8000/docs （Swagger UI）

---

## 七、前后端联调

### 开发时序

1. 启动后端：`py main.py`（端口 8000）
2. 启动前端：`npm run dev`（端口 5173）
3. 浏览器打开 http://localhost:5173

### 前端请求代理

前端 Vite 配置了代理，将 `/api` 请求转发到后端：

```ts
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

---

## 八、生产部署

### 8.1 前端打包

```bash
npm run build
# 构建产物在 dist/ 目录
```

### 8.2 后端启动

```bash
cd backend
py main.py
```

### 8.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/ai-poster-generator/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8.4 使用 HTTPS

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        root /path/to/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

### 8.5 systemd 守护进程（后端）

创建 `/etc/systemd/system/ai-poster-backend.service`：

```ini
[Unit]
Description=AI Poster Backend
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/ai-poster-generator/backend
ExecStart=py main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ai-poster-backend
sudo systemctl start ai-poster-backend
```

---

## 九、Python 依赖说明

| 包 | 版本 | 用途 |
|---|---|---|
| fastapi | 最新 | Web 框架 |
| uvicorn | 最新 | ASGI 服务 |
| python-dotenv | 最新 | 环境变量读取 |
| openai | 最新 | MiniMax API 调用 |
| python-docx | 最新 | Word 文档生成 |
| reportlab | 最新 | PDF 文档生成 |
| playwright | 最新 | HTML 转图片截图 |
| PyYAML | 最新 | YAML 解析 |

---

## 十、常见问题

### Q1：导出 Word 没有图片？

**排查步骤**：

1. 打开浏览器 F12 控制台，点击导出 Word，确认 `images:` 数组有值且是 `data:image` 开头
2. 确认 `layout:` 数组有 `type: "image"` 的项
3. 检查后端控制台是否有 `[WORD] adding image` 日志

### Q2：AI 生成报 "token plan not support model"？

检查 `.env` 中 `MINIMAX_API_KEY` 是否正确，模型名称应为 `MiniMax-M2.7`。如果密钥不支持此模型，可尝试在 `backend/routers/generate.py` 中更换为 `MiniMax-M2.5` 等支持的模型。

### Q3：JSON 解析失败？

可能是 `max_tokens` 设置太小，导致 AI 输出被截断。可在 `generate.py` 中增大该值：

```python
max_tokens=4096  # 默认 4096，可按需调整
```

### Q4：localStorage 存满？

如果历史记录存储失败且报错 `QuotaExceededError`，说明 localStorage 满了（base64 图片很占空间）。这是浏览器限制，可手动清理部分历史记录。

---

## 十一、本地目录映射参考

| 端 | 本地路径 |
|---|---|
| 前端 | `C:\Users\Lenovo\Desktop\宣传素材智能生成\ai-poster-generator\` |
| 后端 | `C:\Users\Lenovo\Desktop\宣传素材智能生成\ai-poster-generator\backend\` |
| Python | `C:\Users\Lenovo\AppData\Local\Programs\Python\Python311\` |

---

## 十二、版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-05-01 | 初始版本，支持海报/推文/简报生成与导出 |
