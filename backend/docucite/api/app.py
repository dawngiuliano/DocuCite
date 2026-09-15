"""DocuCite FastAPI 应用。"""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .models import AskRequest, AskResponse, DocumentSummary, UploadResponse
from .service import DocumentService


def create_app(service: DocumentService | None = None) -> FastAPI:
    """创建应用，允许测试时注入假的 DocumentService。"""
    document_service = service or DocumentService()
    app = FastAPI(title="DocuCite API", version="0.1.0")
    app.state.document_service = document_service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/documents", response_model=UploadResponse)
    async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
        if not file.filename:
            raise HTTPException(status_code=400, detail="上传文件必须有文件名")
        content = await file.read()
        try:
            return document_service.upload(file.filename, content)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except (ModuleNotFoundError, RuntimeError) as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.get("/api/documents", response_model=list[DocumentSummary])
    def list_documents() -> list[DocumentSummary]:
        try:
            return document_service.list_documents()
        except (FileNotFoundError, ValueError) as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.post("/api/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        try:
            return document_service.ask(
                request.question,
                top_k=request.top_k,
                min_score=request.min_score,
            )
        except (FileNotFoundError, ModuleNotFoundError) as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"模型或索引服务调用失败: {error}") from error

    return app


app = create_app()
