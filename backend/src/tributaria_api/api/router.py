from fastapi import APIRouter

from tributaria_api.api.routes.admin import router as admin_router
from tributaria_api.api.routes.assisted_classification import router as assisted_router
from tributaria_api.api.routes.auth import router as auth_router
from tributaria_api.api.routes.companies import router as companies_router
from tributaria_api.api.routes.coverage import router as coverage_router
from tributaria_api.api.routes.health import router as health_router
from tributaria_api.api.routes.members import router as members_router
from tributaria_api.api.routes.persisted_classifications import (
    router as classifications_router,
)
from tributaria_api.api.routes.products import router as products_router
from tributaria_api.api.routes.tax_rule_specifications import (
    router as tax_rule_specifications_router,
)
from tributaria_api.api.routes.taxonomy import admin_router as taxonomy_admin_router
from tributaria_api.api.routes.taxonomy import router as taxonomy_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(coverage_router)
api_router.include_router(members_router)
api_router.include_router(admin_router)
api_router.include_router(classifications_router)
api_router.include_router(assisted_router)
api_router.include_router(products_router)
api_router.include_router(taxonomy_router)
api_router.include_router(taxonomy_admin_router)
api_router.include_router(tax_rule_specifications_router)
