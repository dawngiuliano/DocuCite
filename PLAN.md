# DocuCite 计划

先把 conda 环境和切片/引用的数据约定定住，再写解析与检索，最后才接 FastAPI 和 Vue。前端脚手架已经有了，但现在还调不到后端。

## 现状

已完成：

- conda 环境约定：`docu-cite` / Python 3.12
- 后端空包：`backend/docucite/{ingest,chunking,index,chain,api}`
- 数据模型：`backend/docucite/schemas.py`，包含文档、原文块、检索切片及位置、表格校验
- 前端脚手架：Vue 3 + Vite，`element-plus` 已进 `package.json`
- `backend/requirements.txt`、`backend/.env.example`、根目录 `.gitignore`

未完成：

- 解析、切块、FAISS、问答链全是空的
- FastAPI 还没写
- 前端还是 Vite 默认页；Element Plus 未注册，`/api` 代理未配

## 0. 先做：本机环境

没有环境和 Key，后面都跑不起来。

1. 从仓库根目录执行，确认 conda 环境存在并激活：

   ```powershell
   conda create -n docu-cite python=3.12 -y
   conda activate docu-cite
   python -m pip install -U pip
   cd backend
   pip install -r requirements.txt
   ```

2. 在 `backend/` 下执行 `Copy-Item .env.example .env`，填入模型与 Embedding 的 API Key。
3. 确认 Node.js 20+（前端稍后用）。`frontend/` 里依赖若已装过可跳过 `npm install`。

这一步不写业务代码。

## 1. 数据约定（已实现）

在写解析器之前，先定 **一块切片长什么样**。后面 ingest / chunking / index / chain / API / 前端都吃同一份结构。

模型位于 `backend/docucite/schemas.py`，使用 Pydantic 2 校验并支持 JSON 序列化：

| 字段 | 含义 |
|------|------|
| `Document` | `doc_id`、`filename`、`file_type`（pdf / docx / md） |
| `ParsedBlock` | `block_id`、`doc_id`、`kind`、`text`、`table`、`location` |
| `Chunk` | `chunk_id`、`doc_id`、`filename`、`kind`、`text`、`table`、`location`、`source_block_ids` |
| `Location` | 页码范围、标题路径、段落序号、表格序号和数据行范围 |
| `TableData` | `header` 和矩形 `rows`；无表头用 None，空单元格用空字符串 |

约定：

- 表格一行（或一个逻辑单元）一块，`text` 里带上表头，避免检索糊掉。
- 所有位置编号从 1 开始，表格行号不含表头；未知页码保留 None，不能用段落序号充当页码。
- 位置至少提供页码、标题路径、段落序号或表格序号之一。跨页切片使用 `page` / `page_end`。
- 文档、原文块和切片 ID 默认生成 UUID；同一对象保存与加载时复用 ID，不重复生成。
- 切片保存非空且不重复的 `source_block_ids`；切块器需保证这些块存在、属于同一文档，并保持原文顺序。模型本身不查询外部存储。
- 表格块与表格切片必须保留结构化 `table`；文本块不能携带表格。切块器负责将表头（若有）和选中的数据行生成非空 `text`。
- 无检索命中时问答链必须拒绝作答，不编造。
- 索引用 FAISS 落盘；原文与 metadata 另存（不要只把向量丢进 index）。

验证：在 `backend/` 执行 `python -m unittest discover -s tests -v`，无需模型 Key 或联网。

## 2. 解析（`backend/docucite/ingest`）

按格式拆开，输出「文本 + 表格 + 页码」，不要在这里切块。

- PDF：正文 `pypdf`，表格 `pdfplumber`（保留页码）
- Word：`python-docx`（段落 + 表格；无页码时用段落序号或节）
- Markdown：按标题/段落；表格按 GitHub 风格表解析

先用仓库根目录 `data/` 里一两份样例文件手工跑通，确认能抽出表和页码。从 `backend/` 手工访问时使用 `../data/`；后续配置模块应根据自身 `__file__` 定位 `backend/.env` 和仓库根目录 `data/`，避免依赖当前工作目录。

## 3. 切块（`backend/docucite/chunking`）

- 文本：按标题/段落切，不要把表当普通段落切开
- 表格：表头 + 行 → 一块
- 输出必须符合第 1 步的字段

## 4. 索引（`backend/docucite/index`）

- Embedding 写入 FAISS，`faiss.write_index` 落到仓库根目录的 `data/indexes/`
- metadata（`doc_id` / 文件名 / 页码 / 原文）另存
- 提供：写入、加载、按向量检索 Top-K

## 5. 问答链（`backend/docucite/chain`）

- 问句 → 检索 Top-K → LangChain LCEL 作答
- 答案必须能指回证据块（文件名 + 页码 + 原文片段）
- 无命中或依据不足：明确说不知道

可用脚本在命令行先问几句，确认引用对，再写 HTTP。

## 6. FastAPI（`backend/docucite/api`）

给 Vue 的最小接口即可，例如：

- `POST /api/documents`：上传 PDF / docx / md → 解析 → 切块 → 入索引
- `GET /api/documents`：已入索引的文件列表
- `POST /api/ask`：问题 → `{ answer, citations: [{ filename, page, snippet }] }`

启动（API 实现后可用；从仓库根目录执行，届时写入 README）：

```powershell
conda activate docu-cite
cd backend
uvicorn docucite.api.app:app --reload --host 127.0.0.1 --port 8000
```

用 curl / 浏览器先打通上传和提问，再动前端。

## 7. 前端对接（`frontend/`）

后端三个接口能跑之后再做：

1. `src/main.js` 注册 Element Plus
2. `vite.config.js` 把 `/api` 代理到 `http://127.0.0.1:8000`
3. 去掉 HelloWorld，做成一页：上传 | 提问 | 答案 + 引用列表
4. 封装 `src/api` 调 `/api/documents`、`/api/ask`

开发：在 `backend/` 里启动 FastAPI，另开终端在 `frontend/` 里执行 `npm run dev`。

## 不要提前做

- 不要在解析/检索还没通时先堆 Vue 页面（只能对着空 API）
- 不要上用户系统、多租户、云向量库
- 不要把表格和正文混切
- 不要用 Streamlit（已定前后端分离）

## 建议顺序（一句话）

**环境 → 切片 schema → ingest → chunking → FAISS → 带引用的 chain → FastAPI → Vue 对接。**

下一步动手：第 2 步实现解析器，输出 `ParsedBlock`；本机环境若未配置，先完成第 0 步。
