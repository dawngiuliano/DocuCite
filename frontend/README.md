# DocuCite Frontend

DocuCite 的前端：上传 PDF / Word / Markdown，提问，展示带 **文件名 + 页码** 的引用。

**Vue 3** + **Vite** + **Element Plus**。后端是仓库根目录的 FastAPI（`http://127.0.0.1:8000`）。

## 技术栈

| 项 | 选型 |
|----|------|
| 框架 | Vue 3（Composition API + `<script setup>`） |
| 构建 | Vite |
| UI | Element Plus |
| 开发代理 | Vite `server.proxy` 把 `/api` 转到 `http://127.0.0.1:8000` |

当前脚手架已建好，`element-plus` 已在 `package.json` 中。页面和 API 对接还没写；Element Plus 也尚未在 `src/main.js` 里注册。

## 页面（规划）

- 上传文档（PDF / `.docx` / Markdown）
- 提问
- 展示答案与引用（文件名 / 页码 / 原文片段）

## 环境

需要本机已安装 Node.js（建议 20+）。在 `frontend/` 下：

```powershell
npm install
npm run dev
```

浏览器打开 Vite 提示的本地地址（默认 `http://localhost:5173`）。

其它命令：

```powershell
npm run build      # 生产构建
npm run preview    # 预览 dist
```

开发时前端走 `/api`，由 Vite 代理到后端。后端需先在仓库根目录用 conda 环境启动：

```powershell
conda activate docu-cite
```

后端启动命令等 FastAPI 实现后再补。`vite.config.js` 里的 proxy 也尚未配置，对接 API 时再加。

## 目录

```text
frontend/
  src/
    assets/
    components/
    App.vue
    main.js
    style.css
  index.html
  package.json
  vite.config.js
```

业务页面、API 封装、Element Plus 注册和 `/api` 代理都还没接，后续在 `src/` 里补。
