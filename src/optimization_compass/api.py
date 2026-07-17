from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from optimization_compass import __version__
from optimization_compass.agent_service import (
    AgentCapabilities,
    AgentEntityType,
    AgentService,
)
from optimization_compass.models import (
    Question,
    RecommendationRequest,
    RecommendationResponse,
    VerificationResult,
)
from optimization_compass.web import CANONICAL_ATLAS_URL, SERVICE_LANDING_HTML

service = AgentService()

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
        "dataset_version": capabilities.dataset_version,
    }


@app.get("/v1/capabilities", response_model=AgentCapabilities)
def capabilities() -> AgentCapabilities:
    return service.get_capabilities()


@app.get("/v1/questions", response_model=list[Question])
def questions(language: Literal["ja", "en"] = "ja") -> list[dict[str, object]]:
    return service.list_diagnose_questions(language)


@app.post("/v1/recommendations", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    try:
        return service.recommend_methods(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/methods/{method_id}")
def method(method_id: str) -> dict[str, object]:
    return _entity("method", method_id)


@app.get("/v1/implementations/{implementation_id}")
def implementation(implementation_id: str) -> dict[str, object]:
    return _entity("implementation", implementation_id)


@app.get("/v1/sources/{source_id}")
def source(source_id: str) -> dict[str, object]:
    return _entity("source", source_id)


@app.get("/v1/data/verify", response_model=VerificationResult)
def verify_data() -> dict[str, object]:
    return service.verify_data()


def _entity(entity_type: AgentEntityType, entity_id: str) -> dict[str, object]:
    try:
        return service.get_entity(entity_type, entity_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=f"{entity_type} not found") from exc
