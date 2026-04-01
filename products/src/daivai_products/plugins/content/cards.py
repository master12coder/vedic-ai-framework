"""Social media card text generator for rashifal content.

Transforms SignRashifal data into compact, share-ready card text
for Telegram channels, Instagram stories, and blog posts. Each card
has a Hindi headline, star rating, one-liner prediction, color, and mantra.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from daivai_products.plugins.content.rashifal import DailyRashifal, SignRashifal


# Hindi digits for number conversion
_DIGITS_HI = str.maketrans("0123456789", "०१२३४५६७८९")

# Hindi sign headlines (Sign name — today's day)
_HEADLINES: dict[str, str] = {
    "Aries": "मेष राशि — आज का दिन",
    "Taurus": "वृषभ राशि — आज का दिन",
    "Gemini": "मिथुन राशि — आज का दिन",
    "Cancer": "कर्क राशि — आज का दिन",
    "Leo": "सिंह राशि — आज का दिन",
    "Virgo": "कन्या राशि — आज का दिन",
    "Libra": "तुला राशि — आज का दिन",
    "Scorpio": "वृश्चिक राशि — आज का दिन",
    "Sagittarius": "धनु राशि — आज का दिन",
    "Capricorn": "मकर राशि — आज का दिन",
    "Aquarius": "कुम्भ राशि — आज का दिन",
    "Pisces": "मीन राशि — आज का दिन",
}

# Rating-based Hindi one-liner templates
_RATING_ONELINERS: dict[int, str] = {
    1: "आज का दिन बहुत कठिन रहेगा। सावधानी बरतें।",
    2: "आज चुनौतियाँ आ सकती हैं। धैर्य रखें।",
    3: "मिश्रित फल मिलेंगे। सोच-समझकर काम करें।",
    4: "सामान्य दिन रहेगा। नियमित कार्य करें।",
    5: "दिन ठीक-ठाक रहेगा। कोई बड़ा बदलाव नहीं।",
    6: "अच्छा दिन है। काम में प्रगति होगी।",
    7: "शुभ दिन है। नये काम शुरू कर सकते हैं।",
    8: "बहुत अच्छा दिन! सफलता मिलेगी।",
    9: "उत्तम दिन! हर काम में लाभ होगा।",
    10: "सर्वोत्तम दिन! ग्रह आपके पक्ष में हैं।",
}


class ContentCard(BaseModel):
    """Social media card content for one sign."""

    model_config = ConfigDict(frozen=True)

    sign: str
    sign_hindi: str
    headline: str
    rating_stars: str
    one_liner: str
    color: str
    mantra: str


def _rating_to_stars(rating: int) -> str:
    """Convert numeric rating (1-10) to star string.

    Uses filled and empty star characters for visual display.
    """
    filled = min(rating, 10)
    empty = 10 - filled
    return "\u2b50" * filled + "\u2606" * empty


def generate_card(rashifal: SignRashifal) -> ContentCard:
    """Convert a SignRashifal into social-media-ready card text.

    Args:
        rashifal: Single sign rashifal data.

    Returns:
        ContentCard with headline, stars, one-liner, color, and mantra.
    """
    headline = _HEADLINES.get(
        rashifal.sign, f"{rashifal.sign_hindi} \u2014 \u0906\u091c \u0915\u093e \u0926\u093f\u0928"
    )
    stars = _rating_to_stars(rashifal.day_rating)
    one_liner = _RATING_ONELINERS.get(
        rashifal.day_rating,
        "\u0926\u093f\u0928 \u0920\u0940\u0915 \u0930\u0939\u0947\u0917\u093e\u0964",
    )

    return ContentCard(
        sign=rashifal.sign,
        sign_hindi=rashifal.sign_hindi,
        headline=headline,
        rating_stars=stars,
        one_liner=one_liner,
        color=rashifal.lucky_color,
        mantra=rashifal.mantra,
    )


def generate_all_cards(rashifal: DailyRashifal) -> list[ContentCard]:
    """Generate cards for all 12 signs.

    Args:
        rashifal: Complete daily rashifal with all signs.

    Returns:
        List of 12 ContentCards, one per sign.
    """
    return [generate_card(sign_data) for sign_data in rashifal.signs]


def format_card_text(card: ContentCard) -> str:
    """Format a ContentCard as shareable text for Telegram/social media.

    Args:
        card: Content card to format.

    Returns:
        Multi-line formatted string ready for posting.
    """
    lines = [
        f"\u2728 {card.headline} \u2728",
        "",
        f"{card.rating_stars}",
        "",
        card.one_liner,
        "",
        f"\ud83c\udfa8 \u0930\u0902\u0917: {card.color}",
        f"\ud83d\ude4f \u092e\u0928\u094d\u0924\u094d\u0930: {card.mantra}",
        "",
        "#\u0930\u093e\u0936\u093f\u0ab6\u0ab2 #DaivAI #Jyotish",
    ]
    return "\n".join(lines)


def format_all_cards_text(cards: list[ContentCard]) -> str:
    """Format all 12 cards into a single post (e.g., for a blog or channel).

    Args:
        cards: List of 12 content cards.

    Returns:
        Complete formatted text with all signs.
    """
    sections = [format_card_text(card) for card in cards]
    separator = "\n" + "\u2500" * 30 + "\n"
    return separator.join(sections)
