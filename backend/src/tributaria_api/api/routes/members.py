from datetime import UTC, datetime

from fastapi import APIRouter

from tributaria_api.api.auth_dependencies import (
    CorrelationId,
    IdentityRepositoryDep,
    MembershipManagerContext,
)
from tributaria_api.contracts.identity import MembershipUpdate, MembershipView

router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.get("", response_model=list[MembershipView])
def list_memberships(
    context: MembershipManagerContext, repository: IdentityRepositoryDep
) -> list[dict[str, object]]:
    return repository.list_memberships(context.organization_id)


@router.patch("/{membership_id}", response_model=MembershipView)
def update_membership(
    membership_id: str,
    request: MembershipUpdate,
    context: MembershipManagerContext,
    repository: IdentityRepositoryDep,
    correlation_id: CorrelationId,
) -> dict[str, object]:
    now = datetime.now(UTC)
    record = repository.update_membership(
        context.organization_id,
        membership_id,
        role=request.role.value if request.role else None,
        status=request.status,
        now=now,
    )
    repository.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="membership",
        entity_id=record.id,
        action="MEMBERSHIP_CHANGED",
        occurred_at=now,
        correlation_id=correlation_id,
        metadata={
            "role": record.role,
            "status": record.status,
        },
    )
    repository.session.commit()
    return (
        repository.list_memberships(context.organization_id)[0]
        if False
        else {
            **next(
                item
                for item in repository.list_memberships(context.organization_id)
                if item["id"] == record.id
            )
        }
    )
