"""FastAPI surface for Omega OS v7.0 / SugarCode AI."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from .registry import REGISTRY, SUBNETWORKS, module_slugs
from .health import module_health, compute_flux
from .search import biological_search


def create_app() -> FastAPI:
    app = FastAPI(title="SugarCode AI - Omega OS v7.0", version="0.1.0")

    @app.get("/modules")
    def list_modules(subnetwork: str | None = None):
        slugs = module_slugs(subnetwork)
        if subnetwork and not slugs:
            raise HTTPException(404, f"unknown subnetwork {subnetwork!r}")
        return [REGISTRY[s].__dict__ for s in slugs]

    @app.get("/subnetworks")
    def list_subnetworks():
        return [{"id": k, "description": v, "modules": module_slugs(k)}
                for k, v in SUBNETWORKS.items()]

    @app.get("/modules/{slug}")
    def get_module(slug: str):
        if slug not in REGISTRY:
            raise HTTPException(404, f"unknown module {slug!r}")
        return REGISTRY[slug].__dict__

    @app.get("/health")
    def health():
        return compute_flux()

    @app.get("/health/{slug}")
    def health_one(slug: str):
        if slug not in REGISTRY:
            raise HTTPException(404, f"unknown module {slug!r}")
        return module_health(slug)

    @app.get("/search")
    def search(q: str, limit: int = 10):
        return biological_search(q, limit)

    return app


app = create_app()
