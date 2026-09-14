# DocuCite

多格式文档问答：解析 PDF / Word / Markdown，表格单独切片，回答附带文件名与页码引用。

**Docu** = Document（文档），**Cite** = Citation（引用）。不是只生成答案，而是标出依据来自哪份文件、哪一页。

## 能做什么

- **多格式解析**：PDF、Word（`.docx`）、Markdown
- **表格结构化**：用 pdfplumber / python-docx 抽表，按表头 + 行切块，而不是当普通段落切开
- **向量检索问答**：切片 → Embedding → FAISS → LangChain 检索增强生成
- **带引用回答**：答案附带 `文件名` + `页码`；检索不到依据时明确说不知道，不编造

## 技术栈

| 用途 | 选型 |
|------|------|
| 语言 | Python **3.12**（`>=3.11,<3.13`） |
| 环境 | Conda 环境 `docu-cite` |
| 编排 / 问答 | LangChain（LCEL） |
| 向量检索 | FAISS |
| PDF 文本 | pypdf |
| PDF 表格 | pdfplumber |
| Word | python-docx |
| 后端 API | FastAPI |
| 前端 | Vue 3 + Vite + Element Plus（`frontend/` 已初始化） |

不用 3.13+：`faiss-cpu` 等包经常没有对应轮子。

## 处理流程

```text
上传 PDF / Word / Markdown
  → 解析文本与表格
  → 文本按标题/段落切片，表格按行切片并带上表头
  → Embedding 写入 FAISS，原文与页码写入 metadata
  → 提问 → 混合检索 Top-K → 大模型作答
  → 展示答案 + 引用片段
```

## 环境

需要本机已安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda。以下命令从仓库根目录执行：

```powershell
conda create -n docu-cite python=3.12 -y
conda activate docu-cite
python -m pip install -U pip
cd backend
pip install -r requirements.txt
```

复制 `backend/.env.example` 为 `backend/.env`，填入模型 API Key（已进入 `backend/` 时执行 `Copy-Item .env.example .env`）。

聊天模型使用 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`；向量模型使用独立的 `EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL`，可连接不同的中转站。后续调用代码需分别读取并显式传入各自的 Key、URL 和模型名称。

后端 FastAPI 还没写，conda 环境配好即可；API 启动命令等实现后再补。

## 前端

界面在 `frontend/`，**Vue 3 + Vite + Element Plus**，与后端 FastAPI 分离。脚手架和 `element-plus` 依赖已就绪；页面、API 对接、Element Plus 注册、Vite `/api` 代理都还没接。

| 项 | 约定 |
|----|------|
| 目录 | `frontend/` |
| 构建 | Vite |
| 框架 | Vue 3（Composition API + `<script setup>`） |
| UI | Element Plus |
| 开发代理 | Vite `server.proxy` 把 `/api` 转到 `http://127.0.0.1:8000` |
| 页面 | 上传文档、提问、展示答案与引用（文件名 / 页码 / 原文片段） |

需要本机已安装 Node.js（建议 20+）。另开终端，从仓库根目录执行：

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的本地地址（默认 `http://localhost:5173`）。更细的说明见 [frontend/README.md](frontend/README.md)。

## 目录结构

```text
DocuCite/
  backend/         # 后端工程，安装依赖与启动的工作目录
    docucite/      # Python 包，导入名为 docucite
      __init__.py
      schemas.py   # 文档、原文块、检索切片及位置和表格结构
      ingest/      # pdf / docx / md 解析
      chunking/    # 文本切块 + 表格切块
      index/       # embedding + FAISS 读写
      chain/       # 检索 + 问答
      api/         # FastAPI，给前端调用
    requirements.txt
    .env.example
    tests/         # 数据约定的校验测试
  data/            # 原文、上传文件与索引
  frontend/        # Vue 3 + Vite + Element Plus
  .gitignore
  README.md
  PLAN.md
```

后端路径约定：环境配置放在 `backend/.env`，数据仍放在仓库根目录的 `data/`。后续实现配置加载时，应根据配置模块的 `__file__` 定位这些目录，避免依赖当前工作目录；从 `backend/` 手工访问数据时，相对路径为 `../data/`。

## 设计取舍

数据约定已实现，详细字段和约束见 [PLAN.md](PLAN.md#1-数据约定已实现)。安装后端依赖后，在 `backend/` 执行 `python -m unittest discover -s tests -v` 验证，无需调用模型接口。

- **FAISS 本地即可**：适合个人项目；索引用 `faiss.write_index` 落盘，原文与 `doc_id / 文件名 / 页码` 另存 metadata。
- **表格不跟正文混切**：一行（或一个逻辑单元）一块，并附带表头，否则检索和引用都会糊。
- **引用是功能，不是装饰**：回答必须能指回证据块；无命中则拒绝作答。
- **前后端分离**：后端只提供解析 / 检索 / 问答 API；页面用 Vue + Element Plus，不使用 Streamlit。

## 许可证

MIT
