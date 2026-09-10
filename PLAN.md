# DocuCite 计划

先把 conda 环境和切片/引用的数据约定定住，再写解析与检索，最后才接 FastAPI 和 Vue。前端脚手架已经有了，但现在还调不到后端。

## 现状

已完成：

- conda 环境约定：`docu-cite` / Python 3.12
- 后端空包：`docucite/{ingest,chunking,index,chain,api}`
- 前端脚手架：Vue 3 + Vite，`element-plus` 已进 `package.json`
- `requirements.txt`、`.env.example`、`.gitignore`

未完成：

- 解析、切块、FAISS、问答链全是空的
- FastAPI 还没写
- 前端还是 Vite 默认页；Element Plus 未注册，`/api` 代理未配

## 0. 先做：本机环境

没有环境和 Key，后面都跑不起来。

1. 确认 conda 环境存在并激活：

   ```powershell
   conda create -n docu-cite python=3.12 -y
   conda activate docu-cite
   python -m pip install -U pip
   pip install -r requirements.txt
   ```

2. 复制 `.env.example` 为 `.env`，填入模型与 Embedding 的 API Key。
3. 确认 Node.js 20+（前端稍后用）。`frontend/` 里依赖若已装过可跳过 `npm install`。

这一步不写业务代码。

## 1. 数据约定（后端第一行代码）

在写解析器之前，先定 **一块切片长什么样**。后面 ingest / chunking / index / chain / API / 前端都吃同一份结构。

每块至少包含：

| 字段 | 含义 |
|------|------|
| `doc_id` | 文档 id |
| `filename` | 原始文件名（引用要展示） |
| `page` | 页码；Markdown 可为空或按标题层级 |
| `kind` | `text` 或 `table` |
| `text` | 用于 embedding 和展示的正文 |
| `header` | 表格块的表头；文本块可空 |

约定：

- 表格一行（或一个逻辑单元）一块，`text` 里带上表头，避免检索糊掉。
- 无检索命中时问答链必须拒绝作答，不编造。
- 索引用 FAISS 落盘；原文与 metadata 另存（不要只把向量丢进 index）。

建议落点：`docucite` 里一个小的 schema / dataclass，API 响应也沿用，避免前后端各写一套。

## 2. 解析（`docucite/ingest`）

按格式拆开，输出「文本 + 表格 + 页码」，不要在这里切块。

- PDF：正文 `pypdf`，表格 `pdfplumber`（保留页码）
- Word：`python-docx`（段落 + 表格；无页码时用段落序号或节）
- Markdown：按标题/段落；表格按 GitHub 风格表解析

先用 `data/` 里一两份样例文件手工跑通，确认能抽出表和页码。

## 3. 切块（`docucite/chunking`）

- 文本：按标题/段落切，不要把表当普通段落切开
- 表格：表头 + 行 → 一块
- 输出必须符合第 1 步的字段

## 4. 索引（`docucite/index`）

- Embedding 写入 FAISS，`faiss.write_index` 落到 `data/indexes/`
- metadata（`doc_id` / 文件名 / 页码 / 原文）另存
- 提供：写入、加载、按向量检索 Top-K

## 5. 问答链（`docucite/chain`）

- 问句 → 检索 Top-K → LangChain LCEL 作答
- 答案必须能指回证据块（文件名 + 页码 + 原文片段）
- 无命中或依据不足：明确说不知道

可用脚本在命令行先问几句，确认引用对，再写 HTTP。

## 6. FastAPI（`docucite/api`）

给 Vue 的最小接口即可，例如：

- `POST /api/documents`：上传 PDF / docx / md → 解析 → 切块 → 入索引
- `GET /api/documents`：已入索引的文件列表
- `POST /api/ask`：问题 → `{ answer, citations: [{ filename, page, snippet }] }`

启动（实现后写入 README）：

```powershell
conda activate docu-cite
uvicorn docucite.api.app:app --reload --host 127.0.0.1 --port 8000
```

用 curl / 浏览器先打通上传和提问，再动前端。

## 7. 前端对接（`frontend/`）

后端三个接口能跑之后再做：

1. `src/main.js` 注册 Element Plus
2. `vite.config.js` 把 `/api` 代理到 `http://127.0.0.1:8000`
3. 去掉 HelloWorld，做成一页：上传 | 提问 | 答案 + 引用列表
4. 封装 `src/api` 调 `/api/documents`、`/api/ask`

开发：仓库根目录起 FastAPI，`frontend/` 里 `npm run dev`。

## 不要提前做

- 不要在解析/检索还没通时先堆 Vue 页面（只能对着空 API）
- 不要上用户系统、多租户、云向量库
- 不要把表格和正文混切
- 不要用 Streamlit（已定前后端分离）

## 建议顺序（一句话）

**环境 → 切片 schema → ingest → chunking → FAISS → 带引用的 chain → FastAPI → Vue 对接。**

下一步动手：第 0 步配环境（若还没配），然后第 1 步写出切片数据结构。
