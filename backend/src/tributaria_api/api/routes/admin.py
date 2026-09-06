from fastapi import APIRouter
from tax_engine.rule_lifecycle import RuleLifecycleStatus

from tributaria_api.api.auth_dependencies import (
    ApproverContext,
    CuratorContext,
    PublisherContext,
    ReadContext,
)
from tributaria_api.api.dependencies import GovernanceServiceDep, RepositoryDep
from tributaria_api.application.governance import GovernanceService
from tributaria_api.application.security import AuthContext
from tributaria_api.contracts.admin import (
    LegalSourceCreate,
    LegalSourceView,
    LifecycleCommand,
    RuleSetCreate,
    RuleSetPublish,
    RuleSetView,
    TaxRuleIdentityCreate,
    TaxRuleIdentityView,
    TaxRuleVersionCreate,
    TaxRuleVersionDraftUpdate,
    TaxRuleVersionView,
)

router = APIRouter(prefix="/admin", tags=["experimental-admin"])


@router.post("/legal-sources", response_model=LegalSourceView, status_code=201)
def create_legal_source(
    request: LegalSourceCreate, service: GovernanceServiceDep, context: CuratorContext
) -> dict[str, object]:
    data = request.model_dump(mode="python")
    data.update(
        official_url=str(request.official_url),
        created_by=context.user_id,
        organization_id=context.organization_id,
    )
    return service.create_legal_source(data)


@router.post("/tax-rules", response_model=TaxRuleIdentityView, status_code=201)
def create_tax_rule(
    request: TaxRuleIdentityCreate, service: GovernanceServiceDep, context: CuratorContext
) -> dict[str, object]:
    data = request.model_dump(mode="python")
    data.update(created_by=context.user_id, organization_id=context.organization_id)
    return service.create_rule_identity(data)


@router.post(
    "/tax-rules/{identity_id}/versions", response_model=TaxRuleVersionView, status_code=201
)
def create_tax_rule_version(
    identity_id: str,
    request: TaxRuleVersionCreate,
    service: GovernanceServiceDep,
    context: CuratorContext,
) -> dict[str, object]:
    data = request.model_dump(mode="python")
    data.update(rule_identity_id=identity_id, created_by=context.user_id)
    return service.create_rule_version(data)


@router.post("/tax-rule-versions/{version_id}/draft", response_model=TaxRuleVersionView)
def update_draft(
    version_id: str,
    request: TaxRuleVersionDraftUpdate,
    service: GovernanceServiceDep,
    context: CuratorContext,
) -> dict[str, object]:
    return service.update_draft_version(
        version_id,
        content=request.content,
        metadata=request.metadata,
        occurred_at=request.occurred_at,
        actor_id=context.user_id,
        correlation_id=request.correlation_id,
    )


def _transition(
    version_id: str,
    request: LifecycleCommand,
    status: RuleLifecycleStatus,
    service: GovernanceService,
    context: AuthContext,
) -> dict[str, object]:
    return service.transition(
        version_id,
        target=status,
        event_id=request.event_id,
        occurred_at=request.occurred_at,
        actor_id=context.user_id,
        reason=request.reason,
        correlation_id=request.correlation_id,
        related_version=request.related_version,
    )


@router.post("/tax-rule-versions/{version_id}/submit-review", response_model=TaxRuleVersionView)
def submit_review(
    version_id: str,
    request: LifecycleCommand,
    service: GovernanceServiceDep,
    context: CuratorContext,
) -> dict[str, object]:
    return _transition(version_id, request, RuleLifecycleStatus.IN_REVIEW, service, context)


@router.post("/tax-rule-versions/{version_id}/approve", response_model=TaxRuleVersionView)
def approve(
    version_id: str,
    request: LifecycleCommand,
    service: GovernanceServiceDep,
    context: ApproverContext,
) -> dict[str, object]:
    return _transition(version_id, request, RuleLifecycleStatus.APPROVED, service, context)


@router.post("/tax-rule-versions/{version_id}/publish", response_model=TaxRuleVersionView)
def publish(
    version_id: str,
    request: LifecycleCommand,
    service: GovernanceServiceDep,
    context: PublisherContext,
) -> dict[str, object]:
    return _transition(version_id, request, RuleLifecycleStatus.PUBLISHED, service, context)


@router.post("/tax-rule-versions/{version_id}/supersede", response_model=TaxRuleVersionView)
def supersede(
    version_id: str,
    request: LifecycleCommand,
    service: GovernanceServiceDep,
    context: PublisherContext,
) -> dict[str, object]:
    return _transition(version_id, request, RuleLifecycleStatus.SUPERSEDED, service, context)


@router.post("/tax-rule-versions/{version_id}/withdraw", response_model=TaxRuleVersionView)
def withdraw(
    version_id: str,
    request: LifecycleCommand,
    service: GovernanceServiceDep,
    context: PublisherContext,
) -> dict[str, object]:
    return _transition(version_id, request, RuleLifecycleStatus.WITHDRAWN, service, context)


@router.post("/rulesets", response_model=RuleSetView, status_code=201)
def create_ruleset(
    request: RuleSetCreate, service: GovernanceServiceDep, context: CuratorContext
) -> dict[str, object]:
    data = request.model_dump(mode="python", exclude={"rule_version_ids"})
    data.update(
        created_by=context.user_id,
        organization_id=context.organization_id,
        status="DRAFT",
        fingerprint=None,
        published_at=None,
        published_by=None,
    )
    return service.create_ruleset(data, request.rule_version_ids)


@router.post("/rulesets/{ruleset_id}/publish", response_model=RuleSetView)
def publish_ruleset(
    ruleset_id: str,
    request: RuleSetPublish,
    service: GovernanceServiceDep,
    context: PublisherContext,
) -> dict[str, object]:
    return service.publish_ruleset(
        ruleset_id,
        actor_id=context.user_id,
        occurred_at=request.occurred_at,
        correlation_id=request.correlation_id,
    )


@router.get("/tax-rules/{identity_id}", response_model=TaxRuleIdentityView)
def get_tax_rule(
    identity_id: str, repository: RepositoryDep, context: ReadContext
) -> dict[str, object]:
    value = repository.get_rule_identity(identity_id)
    if value.get("organization_id") != context.organization_id:
        from tributaria_api.application.errors import NotFoundError

        raise NotFoundError("Tax rule identity not found")
    return value


@router.get("/tax-rule-versions", response_model=list[TaxRuleVersionView])
def list_tax_rule_versions(
    repository: RepositoryDep, context: ReadContext
) -> list[dict[str, object]]:
    return [
        item
        for item in repository.list_rule_versions()
        if item.get("organization_id") == context.organization_id
    ]


@router.get("/rulesets/{ruleset_id}", response_model=RuleSetView)
def get_ruleset(
    ruleset_id: str, repository: RepositoryDep, context: ReadContext
) -> dict[str, object]:
    value = repository.get_ruleset(ruleset_id)
    if value.get("organization_id") != context.organization_id:
        from tributaria_api.application.errors import NotFoundError

        raise NotFoundError("Ruleset not found")
    return value
