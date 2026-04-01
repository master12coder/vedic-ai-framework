PLUGIN_NAME = "content"
DESCRIPTION = "Content automation — daily rashifal for 12 signs, social media cards"
COMMANDS = {
    "rashifal": {
        "help": "Generate daily rashifal for all 12 signs",
        "handler": "generate_rashifal",
    },
    "card": {"help": "Generate social media card text for a sign", "handler": "generate_card"},
}
