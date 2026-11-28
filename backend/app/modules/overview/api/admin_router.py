from typing import Optional, cast

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Query

from app.api.dependencies.admin import require_admin_user
from app.core.types import TimeZoneName
from app.modules.overview.api.schemas import (
    AttentionResponse,
    ClientAppsResponse,
    HourlyOnlineResponse,
    NodesOverviewResponse,
    OnlineChartResponse,
    OverviewPeriodDays,
    OverviewResponse,
    RecapResponse,
    RevenueChartResponse,
)
from app.modules.overview.dto import GetOverviewChartDto, GetOverviewDto, OverviewDays
from app.modules.overview.usecases import (
    GetAttentionUseCase,
    GetClientAppsUseCase,
    GetHourlyOnlineUseCase,
    GetNodesOverviewUseCase,
    GetOnlineChartUseCase,
    GetOverviewUseCase,
    GetRecapUseCase,
    GetRevenueChartUseCase,
)
from app.modules.users import UserDto

router = APIRouter(prefix="/overview", tags=["overview"])


def _chart_dto(days: OverviewPeriodDays, tz: Optional[str]) -> GetOverviewChartDto:
    return GetOverviewChartDto(days=cast(OverviewDays, int(days)), tz=tz)


@router.get("", response_model=OverviewResponse)
@inject
async def get_overview(
    use_case: FromDishka[GetOverviewUseCase],
    actor: UserDto = Depends(require_admin_user),
    tz: Optional[TimeZoneName] = Query(None, max_length=64),
) -> OverviewResponse:
    overview = await use_case(actor, GetOverviewDto(tz=tz))
    return OverviewResponse.model_validate(overview, from_attributes=True)


@router.get("/recap", response_model=RecapResponse)
@inject
async def get_overview_recap(
    use_case: FromDishka[GetRecapUseCase],
    actor: UserDto = Depends(require_admin_user),
) -> RecapResponse:
    recap = await use_case(actor)
    return RecapResponse.model_validate(recap, from_attributes=True)


@router.get("/revenue", response_model=RevenueChartResponse)
@inject
async def get_overview_revenue(
    use_case: FromDishka[GetRevenueChartUseCase],
    actor: UserDto = Depends(require_admin_user),
    days: OverviewPeriodDays = OverviewPeriodDays.SEVEN,
    tz: Optional[TimeZoneName] = Query(None, max_length=64),
) -> RevenueChartResponse:
    chart = await use_case(actor, _chart_dto(days, tz))
    return RevenueChartResponse.model_validate(chart, from_attributes=True)


@router.get("/online", response_model=OnlineChartResponse)
@inject
async def get_overview_online(
    use_case: FromDishka[GetOnlineChartUseCase],
    actor: UserDto = Depends(require_admin_user),
    days: OverviewPeriodDays = OverviewPeriodDays.SEVEN,
    tz: Optional[TimeZoneName] = Query(None, max_length=64),
) -> OnlineChartResponse:
    chart = await use_case(actor, _chart_dto(days, tz))
    return OnlineChartResponse.model_validate(chart, from_attributes=True)


@router.get("/online/hourly", response_model=HourlyOnlineResponse)
@inject
async def get_overview_online_hourly(
    use_case: FromDishka[GetHourlyOnlineUseCase],
    actor: UserDto = Depends(require_admin_user),
) -> HourlyOnlineResponse:
    chart = await use_case(actor)
    return HourlyOnlineResponse.model_validate(chart, from_attributes=True)


@router.get("/nodes", response_model=NodesOverviewResponse)
@inject
async def get_overview_nodes(
    use_case: FromDishka[GetNodesOverviewUseCase],
    actor: UserDto = Depends(require_admin_user),
) -> NodesOverviewResponse:
    nodes = await use_case(actor)
    return NodesOverviewResponse.model_validate(nodes, from_attributes=True)


@router.get("/client-apps", response_model=ClientAppsResponse)
@inject
async def get_overview_client_apps(
    use_case: FromDishka[GetClientAppsUseCase],
    actor: UserDto = Depends(require_admin_user),
) -> ClientAppsResponse:
    apps = await use_case(actor)
    return ClientAppsResponse.model_validate(apps, from_attributes=True)


@router.get("/attention", response_model=AttentionResponse)
@inject
async def get_overview_attention(
    use_case: FromDishka[GetAttentionUseCase],
    actor: UserDto = Depends(require_admin_user),
) -> AttentionResponse:
    attention = await use_case(actor)
    return AttentionResponse.model_validate(attention, from_attributes=True)
