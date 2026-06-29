from __future__ import annotations

from models.ai import AIProviderMeta
from models.stock import StockAIExplanationResponse
from providers.llm import get_llm_provider
from services.ai_service import AIInsightsService
from services.fundamentals_service import (
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_SUCCESS,
    STATUS_UNSUPPORTED,
    find_active_fundamentals_job,
    get_latest_fundamentals_by_code,
)
from services.stock_data_service import StockDataService


def build_stock_ai_explanation(
    *,
    db,
    user_id: int,
    stock_code: str,
    screening_result,
    request_id: str | None,
) -> StockAIExplanationResponse:
    normalized_code = StockDataService.normalize_stock_code(stock_code)
    latest_fundamentals = get_latest_fundamentals_by_code(db, {normalized_code}).get(normalized_code)
    active_job = find_active_fundamentals_job(db, user_id=user_id, stock_code=normalized_code)

    if latest_fundamentals is None:
        return StockAIExplanationResponse(
            status="sync_required",
            stock_code=normalized_code,
            message="Fundamentals data is not available yet. Please sync first.",
            explanation=None,
            can_sync=True,
            request_id=request_id,
        )

    if latest_fundamentals.status == STATUS_UNSUPPORTED:
        return StockAIExplanationResponse(
            status="unsupported",
            stock_code=normalized_code,
            message="Fundamentals data is not available for this market/provider.",
            explanation=None,
            can_sync=False,
            request_id=request_id,
        )

    if latest_fundamentals.status == STATUS_PENDING or active_job is not None:
        return StockAIExplanationResponse(
            status="sync_queued",
            stock_code=normalized_code,
            message="Fundamentals sync has been queued. Please retry later.",
            explanation=None,
            can_sync=True,
            job_id=getattr(active_job, "id", None),
            request_id=request_id,
        )

    if latest_fundamentals.status == STATUS_FAILED:
        return StockAIExplanationResponse(
            status="sync_required",
            stock_code=normalized_code,
            message="Fundamentals sync failed. Please resync and retry AI explanation.",
            explanation=None,
            can_sync=True,
            request_id=request_id,
        )

    if latest_fundamentals.status != STATUS_SUCCESS:
        return StockAIExplanationResponse(
            status="sync_required",
            stock_code=normalized_code,
            message="Fundamentals data is not ready yet. Please sync and retry.",
            explanation=None,
            can_sync=True,
            request_id=request_id,
        )

    service = AIInsightsService(get_llm_provider())
    metrics = {
        "pe_ratio": float(latest_fundamentals.pe_ratio) if latest_fundamentals.pe_ratio is not None else None,
        "pb_ratio": float(latest_fundamentals.pb_ratio) if latest_fundamentals.pb_ratio is not None else None,
        "dividend_yield": (
            float(latest_fundamentals.dividend_yield) if latest_fundamentals.dividend_yield is not None else None
        ),
        "revenue_growth": (
            float(latest_fundamentals.revenue_growth) if latest_fundamentals.revenue_growth is not None else None
        ),
        "eps": float(latest_fundamentals.eps) if latest_fundamentals.eps is not None else None,
    }
    ai_result = service.stock_explanation(
        stock_code=normalized_code,
        passed=screening_result.passed,
        fail_reasons=screening_result.fail_reasons,
        metrics=metrics,
    )
    return StockAIExplanationResponse(
        status="ready",
        stock_code=normalized_code,
        message=None,
        explanation=ai_result.text,
        can_sync=True,
        request_id=request_id,
        meta=AIProviderMeta(provider=ai_result.provider, is_fallback=ai_result.is_fallback, error=ai_result.error),
    )
