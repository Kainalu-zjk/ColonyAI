<p align="center">
  <img src="./frontend/src/assets/icon.png" alt="Colony AI Logo" width="120"/>
</p>
<h1 align="center">🧬 Colony AI · 智衍</h1>
<p align="center">
  <b>多智能体协作平台</b><br>
  <i>Multi-Agent Collaboration Platform — 让复杂工作流变得简单</i>
</p>

<p align="center">
  <a href="#-architecture">架构</a> •
  <a href="#-features">特性</a> •
  <a href="#-getting-started">快速开始</a> •
  <a href="#-configuration">配置</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/backend-Python%203.11%2B-blue?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/frontend-Vue%203-4FC08D?logo=vue.js" alt="Vue 3"/>
  <img src="https://img.shields.io/badge/LLM-Agnostic-FF6F00" alt="LLM Agnostic"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License"/>
</p>

---

## 🌟 简介

**Colony AI** 是一个**多智能体协作平台**，通过编排多个专业 AI Agent（协调者、建模手、代码手、论文手）协同工作，自动化完成复杂的端到端任务。

最初聚焦于数学建模竞赛场景——从问题分析、数学建模、代码编写到论文生成，全流程自动化。但架构设计通用，可扩展至任何需要多步 AI 协作的场景。

### 与上游项目的区别

| 维度 | MathModelAgent (上游) | Colony AI (本分支) |
|------|----------------------|-------------------|
| 🎨 品牌 | MathModelAgent | **Colony AI / 智衍** |
| 🌐 国际化 | 仅中文 | **全栈中英文i18n** |
| 📋 模板 | 2套 | **4套（国赛/美赛/华数杯/华为杯）** |
| 🔗 文献引用 | footnotes始终为空 | **OpenAlex → APA/GB7714 正确引用** |
| 🖥 WebUI | 基本版 | **品牌重塑 + 历史任务面板** |
| 💻 CLI | 无 | **完整CLI（交互/单次/headless模式）** |
| 🔌 Redis | 必需 | **可选（无Redis自动降级文件模式）** |
| 🛡 重试保护 | 无限死循环 | **10次上限 + 错误传播** |

---

## 🏗 架构

```
输入题目 → CoordinatorAgent(拆解问题)
         → ModelerAgent(制定建模方案)
         → CoderAgent(代码实现 + 本地Jupyter执行)
         → WriterAgent(论文撰写 + 文献引用)
         → UserOutput(拼接 → res.md)
```

### 4 个 Agent

| Agent | 职责 |
|-------|------|
| **Coordinator** | 拆解问题、分发任务 |
| **Modeler** | 模型选择、方案设计 |
| **Coder** | 代码生成、执行、反思纠错 |
| **Writer** | 论文撰写、文献引用 |

---

## ✨ 特性

### 多智能体协作
- 4 个专业 Agent 流水线协作
- 每个 Agent 可独立配置不同 LLM 模型

### LLM 无关
- 支持 OpenAI / Anthropic / 任意兼容 API
- 四种 API 类型：`openai-chat` / `openai-responses` / `anthropic`

### 代码执行
- 本地 Jupyter 内核
- E2B 云端沙箱（可选）

### 论文模板
- **国赛模板** — 中文竞赛标准格式
- **美赛模板** — MCM/ICM 英文，APA 引用
- **华数杯模板** — 侧重数据处理与综合评价
- **华为杯模板** — 侧重工程与算法优化

### 文献引用
- OpenAlex 学术搜索
- APA 7th / GB/T 7714 格式
- 跨章节去重、顺序编号

### WebUI
- 品牌 Bento Grid 首屏
- 历史任务侧边栏面板
- 实时 WebSocket 推送（Redis / 文件轮询）
- 工作区文件浏览与下载

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Redis（可选，无 Redis 自动降级）

### 1. 克隆并安装

```bash
git clone https://github.com/Kainalu-zjk/ColonyAI.git
cd ColonyAI

# 后端
cd backend
pip install uv
uv sync

# 前端
cd ../frontend
npm install -g pnpm
pnpm i
```

### 2. 配置

```bash
cp backend/.env.example backend/.env.dev
# 编辑 backend/.env.dev — 设置 API Key 和模型 ID
```

### 3. 启动

```bash
# 后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（新终端）
cd frontend
pnpm run dev
```

打开 **http://localhost:5173**

### CLI 模式

```bash
# 交互模式
python -m app.main cli --mode interactive

# 单文件模式
python -m app.main cli --file problem.txt --template china --output markdown

# 美赛（英文）
python -m app.main cli --file problem.txt --template american --lang en
```

---

## ⚙ 配置

### API Key

在 `backend/.env.dev` 中配置各 Agent 的 LLM：

| 变量 | 说明 |
|------|------|
| `COORDINATOR_API_KEY` | 协调者 API Key |
| `COORDINATOR_MODEL` | 模型 ID（如 `gpt-4o`, `deepseek-chat`） |
| `COORDINATOR_API_TYPE` | API 类型 |
| `COORDINATOR_BASE_URL` | API 地址 |
| *(MODELER / CODER / WRITER 同此模式)* | |

---

## 🗂 项目结构

```
ColonyAI/
├── backend/
│   └── app/
│       ├── core/
│       │   ├── agents/          # 4 个 Agent 实现
│       │   ├── prompts/         # i18n 提示词模板
│       │   ├── llm/             # LLM 驱动工厂
│       │   ├── workflow.py      # 主流水线
│       │   └── flows.py         # 任务流定义
│       ├── routers/             # FastAPI 路由
│       ├── schemas/             # Pydantic 模型
│       ├── models/              # 输出管理
│       ├── services/            # Redis / WebSocket
│       ├── tools/               # 代码解释器 / 学术搜索
│       ├── locales/             # i18n 中英文 JSON
│       └── config/              # 设置与模板文件
├── frontend/
│   └── src/
│       ├── components/          # Vue 组件
│       ├── pages/               # 页面
│       ├── stores/              # Pinia 状态
│       ├── i18n/                # 前端国际化
│       └── apis/                # API 客户端
└── docs/                        # 文档与截图
```

---

## 📄 License

基于 [MathModelAgent](https://github.com/jihe520/MathModelAgent) 修改，在相同许可条款下提供。

---

<p align="center">
  <b>Colony AI · 智衍</b> — 让协作更智能<br>
  <sub><i>Multi-Agent Collaboration, Amplified.</i></sub>
</p>
