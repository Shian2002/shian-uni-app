# 时安解忧屋

八字命理、奇门遁甲、塔罗占卜等玄学综合服务平台。

## 项目结构

```
shian-uni-app/
├── frontend/ (根目录)     # uni-app Vue3 前端
│   ├── src/              # 前端源码（页面、组件、静态资源）
│   ├── index.html        # 入口 HTML
│   └── package.json      # 前端依赖
│
├── backend/              # Python Flask 后端
│   ├── app.py            # 主应用 + API 路由
│   ├── models.py         # SQLAlchemy 数据模型
│   ├── bazi_engine.py    # 八字排盘引擎
│   ├── tarot_engine.py   # 塔罗引擎
│   ├── ziwei_engine.py   # 紫微斗数引擎
│   ├── deepseek_service.py # DeepSeek AI 服务
│   ├── uploads/          # 本地开发上传目录（生产用 UPLOAD_FOLDER 指向 H5 静态目录）
│   └── requirements.txt  # Python 依赖
│
├── database/             # 数据库 Schema
│   └── schema.sql        # 完整建表 SQL
│
├── deploy/               # 部署脚本
│   ├── deploy-to-server.sh
│   └── scripts/
│
└── README.md
```

## 技术栈

- **前端**: uni-app / Vue3 / JavaScript
- **后端**: Python / Flask / SQLAlchemy
- **数据库**: SQLite
- **AI**: DeepSeek (SiliconFlow API)
