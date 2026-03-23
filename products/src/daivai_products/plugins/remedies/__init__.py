PLUGIN_NAME = "remedies"
DESCRIPTION = (
    "Gemstone recommendations, multi-factor weight engine, weekly pooja plan, Lal Kitab remedies"
)
COMMANDS = {
    "remedies": {"help": "Get personalized remedy recommendations", "handler": "run_remedies"},
    "gemstone": {
        "help": "Compute gemstone weight with 10 chart factors",
        "handler": "run_gemstone",
    },
    "pooja": {"help": "Generate weekly pooja plan", "handler": "run_pooja"},
    "lal_kitab": {
        "help": "Lal Kitab planet assessment, debts (Rin), and remedies",
        "handler": "run_lal_kitab",
    },
}
