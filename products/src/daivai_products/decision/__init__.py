"""Decision Engine -- Layer 3: intelligence between computation and interpretation.

Reads FullChartAnalysis from engine and produces structured decision outputs
that guide the AI interpretation layer. This package never calls engine compute
modules directly -- it only consumes the pre-computed FullChartAnalysis model.

Submodules:
    models            -- Pydantic v2 models for all decision outputs
    chart_selector    -- Selects relevant divisional charts for a query type
    house_highlighter -- Highlights relevant houses and karakas for a query type
    cross_validator   -- D1 vs D9 consistency checks
    confidence        -- Per-section confidence scoring (0-100)
    gemstone_weight   -- 10-factor gemstone ratti recommendation engine
"""

from daivai_products.decision.chart_selector import select_charts
from daivai_products.decision.confidence import compute_confidence
from daivai_products.decision.cross_validator import validate_cross_chart
from daivai_products.decision.gemstone_weight import compute_gemstone_weights
from daivai_products.decision.house_highlighter import highlight_houses
from daivai_products.decision.models import (
    ChartSelection,
    ConfidenceReport,
    CrossChartCheck,
    CrossChartValidation,
    GemstoneReport,
    GemstoneWeight,
    HouseHighlight,
    SectionConfidence,
)


__all__ = [
    "ChartSelection",
    "ConfidenceReport",
    "CrossChartCheck",
    "CrossChartValidation",
    "GemstoneReport",
    "GemstoneWeight",
    "HouseHighlight",
    "SectionConfidence",
    "compute_confidence",
    "compute_gemstone_weights",
    "highlight_houses",
    "select_charts",
    "validate_cross_chart",
]
