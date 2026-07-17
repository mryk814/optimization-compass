from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from optimization_compass import __version__
from optimization_compass.agent_service import (
    AgentCapabilitiesResponse,
    DatasetVersionMismatch,
    DeterministicGuidanceService,
    UnsupportedLanguage,
)
from optimization_compass.db import KnowledgeRepository
from optimization_compass.models import (
    Question,
    RecommendationRequest,
    RecommendationResponse,
    VerificationResult,
)
from optimization_compass.web import CANONICAL_ATLAS_URL, SERVICE_LANDING_HTML

repository = KnowledgeRepository()
service = DeterministicGuidanceService(repository)

app = FastAPI(
    title="Optimization Compass",
    version=__version__,
    description="Traceable guidance for optimization methods and implementations.",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> HTMLResponse:
    return HTMLResponse(
        content=SERVICE_LANDING_HTML,
        headers={"Link": f'<{CANONICAL_ATLAS_URL}>; rel="canonical"'},
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    capabilities = service.get_capabilities()
    return {
        "status": "ok",
        "app_version": __version__,
        "dataset_version": capabilities.metadata.dataset_version,
    }


@app.get("/v1/capabilities", response_model=AgentCapabilitiesResponse)
def capabilities(expected_dataset_version: str | None = None) -> AgentCapabilitiesResponse:
    try:
        return service.get_capabilities(expected_dataset_version=expected_dataset_version)
    except DatasetVersionMismatch as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/v1/questions", response_model=list[Question])
def questions(language: str = "ja", expected_dataset_version: str | None = None) -> list[Question]:
    try:
        response = service.list_diagnose_questions(
            language=language,
            expected_dataset_version=expected_dataset_version,
        )
    except UnsupportedLanguage as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DatasetVersionMismatch as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return list(response.questions)


@app.post("/v1/recommendations", response_model=RecommendationResponse)
def recommendations(
    request: RecommendationRequest,
    expected_dataset_version: str | None = None,
) -> RecommendationResponse:
    try:
        response = service.recommend_methods(
            request,
            expected_dataset_version=expected_dataset_version,
        )
        return response.recommendation
    except DatasetVersionMismatch as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/methods/{method_id}")
def method(method_id: str) -> dict[str, object]:
    row = repository.method(method_id)
    if row is None:
        raise HTTPException(status_code=404, detail="method not found")
    return row


@app.get("/v1/implementations/{implementation_id}")
def implementation(implementation_id: str) -> dict[str, object]:
    row = repository.implementation(implementation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="implementation not found")
    return row


@app.get("/v1/sources/{source_id}")
def source(source_id: str) -> dict[str, object]:
    row = repository.source(source_id)
    if row is None:
        raise HTTPException(status_code=404, detail="source not found")
    return row


@app.get("/v1/data/verify", response_model=VerificationResult)
def verify_data() -> dict[str, object]:
    return repository.verify()
