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

需要本机已安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda。

```powershell
conda create -n docu-cite python=3.12 -y
conda activate docu-cite
python -m pip install -U pip
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填入模型 API Key。

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

需要本机已安装 Node.js（建议 20+）：

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的本地地址（默认 `http://localhost:5173`）。更细的说明见 [frontend/README.md](frontend/README.md)。

## 目录结构

```text
DocuCite/
  docucite/
    ingest/        # pdf / docx / md 解析
    chunking/      # 文本切块 + 表格切块
    index/         # embedding + FAISS 读写
    chain/         # 检索 + 问答
    api/           # FastAPI，给前端调用
  data/            # 原文、上传文件与索引
  frontend/        # Vue 3 + Vite + Element Plus
  requirements.txt
  .env.example
```

## 设计取舍

- **FAISS 本地即可**：适合个人项目；索引用 `faiss.write_index` 落盘，原文与 `doc_id / 文件名 / 页码` 另存 metadata。
- **表格不跟正文混切**：一行（或一个逻辑单元）一块，并附带表头，否则检索和引用都会糊。
- **引用是功能，不是装饰**：回答必须能指回证据块；无命中则拒绝作答。
- **前后端分离**：后端只提供解析 / 检索 / 问答 API；页面用 Vue + Element Plus，不使用 Streamlit。

## 许可证

MIT
