# DaivAI Product Roadmap

Version 1.0 | March 2026 | Manish Chaurasia

## 9 Execution Phases

### Phase 1: Complete Computation Engine
- **Scope:** All 9 HIGH + 8 MEDIUM priority calculations. Every Jyotish computation a Pandit expects. Pydantic models for every result.
- **Target:** 650+ tests (ACHIEVED: 3643 tests, 100 modules, FullChartAnalysis v5.1)
- **Depends on:** None
- **Status:** DONE (March 2026)

### Phase 2: Unified Data Model
- **Scope:** FullChartAnalysis master Pydantic model. Single orchestrator function. JSON serialize to DB. Versioned.
- **Target:** One model = one truth
- **Depends on:** Phase 1
- **Status:** DONE (FullChartAnalysis v5.1, 67 fields, compute_full_analysis() orchestrator)

### Phase 3: Decision Engine
- **Scope:** Chart Selector (query + age + flags = which charts). House Highlighter. Cross-Chart Validator (D1 vs D9). Confidence Scorer (0-100). Progressive input.
- **Depends on:** Phase 2
- **Status:** NOT STARTED

### Phase 4: AI Interpretation
- **Scope:** Structured prompt templates per domain. Groq free tier as default. Validation: AI cannot contradict computation. Caching. Fallback chain.
- **Depends on:** Phase 2
- **Status:** PARTIAL (14 prompt templates exist, LLM backends coded, validator exists, not fully wired)

### Phase 5: Learning System
- **Scope:** Pandit correction form. 6-layer validation pipeline. Approved corrections injected into prompts. Trust scoring.
- **Depends on:** Phase 4
- **Status:** PARTIAL (PanditCorrectionStore exists, basic trust scoring)

### Phase 6: Web UI Rebuild
- **Scope:** Responsive (390-1440px). Reusable Jinja2 macros. 7 product pages. End user / Pandit toggle. Swipeable charts. Dasha Chakra. Gem SVG icons.
- **Depends on:** Phases 2-4
- **Status:** NOT STARTED (basic templates exist from earlier)

### Phase 7: Predictions
- **Scope:** Life event input. Dasha-event matching. Accuracy dashboard. Prediction tracking. Credibility engine.
- **Depends on:** Phase 2
- **Status:** PARTIAL (PredictionTracker + LifeEventsDB exist)

### Phase 8: Deployment Hardening
- **Scope:** systemd, Nginx/Caddy, SSL, domain, Google OAuth real setup, log rotation, monitoring.
- **Depends on:** Any time
- **Status:** PARTIAL (live on Oracle VM at 92.4.89.82)

### Phase 9: Content Automation
- **Scope:** Daily rashifal (12 signs). WhatsApp/Telegram image cards. Blog auto-publish. SEO pages. PWA.
- **Depends on:** Phase 4
- **Status:** NOT STARTED

## Session Execution Plan

| # | Phase | What Gets Built | Target Tests |
|---|-------|----------------|-------------|
| 1-2 | Phase 1 | All HIGH + MEDIUM computations | 650+ |
| 3 | Phase 2 | FullChartAnalysis + orchestrator | 660+ |
| 4 | Phase 3 | Chart selector + cross-validator + confidence | 680+ |
| 5-6 | Phase 4 | Prompt templates + AI interpretation for all 7 products | 700+ |
| 7-10 | Phase 6 | Design system + 7 product pages + Pandit view | 720+ |
| 11 | Phase 7 | Life events + predictions + accuracy engine | 740+ |
| 12 | Phase 5 | Pandit learning system + corrections | 750+ |
| 13 | Phase 8 | Deployment hardening (SSL, systemd, domain) | 750+ |
| 14 | Phase 9 | Content automation (rashifal, Telegram, SEO) | 755+ |

## Success Metrics

| Milestone | Metric | Target |
|-----------|--------|--------|
| After Phase 1 | All Jyotish calculations complete | 650+ tests |
| After Phase 6 | Active users | 50+ |
| After Phase 7 | Average life events per user | 5+ |
| After Phase 9 | Daily organic visitors | 100+ |
| December 2026 | Total registered users | 500+ |
| 2028 (Venus antardasha) | Monthly revenue | 50,000+ INR |

## Future Product: Financial Timing (#8)

Appears naturally in Phase 4 (AI) + Phase 6 (UI). No new phase needed.

```
INPUT: Birth chart + "Should I invest now?"
OUTPUT:
├── Current dasha financial rating (1-10)
├── 2nd/11th house activation: YES/NO
├── Double transit on wealth houses: ACTIVE/INACTIVE
├── Best months for investment in next 12 months
├── Avoid financial risk periods (8th lord active)
├── Personal golden period for wealth
└── Disclaimer: "यह व्यक्तिगत समय विश्लेषण है, बाजार भविष्यवाणी नहीं।"
```

## Notes

- Multi-ayanamsha comparison, tropical-internal architecture, birth time rectification → Phase 2/7 features, not engine layer
- Engine (Phase 1) is FROZEN after completion — no new computations unless they're universal
