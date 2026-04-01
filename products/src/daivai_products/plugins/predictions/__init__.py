PLUGIN_NAME = "predictions"
DESCRIPTION = (
    "Prediction tracking, accuracy dashboard, life event logging, and dasha-event matching"
)
COMMANDS = {
    "events": {"help": "Life event tracking", "handler": "run_events"},
    "dashboard": {"help": "Prediction accuracy dashboard", "handler": "run_dashboard"},
    "match": {"help": "Match life events to dasha periods", "handler": "run_match"},
    "accuracy": {"help": "Compute prediction accuracy and credibility", "handler": "run_accuracy"},
}
