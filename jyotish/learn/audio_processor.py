"""Whisper integration for Hindi audio transcription and correction extraction."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from jyotish.learn.corrections import PanditCorrection


@dataclass
class TranscriptionResult:
    """Result of audio transcription via Whisper."""

    text: str
    language: str
    duration_seconds: float


def transcribe_audio(
    audio_path: str | Path,
    method: str = "groq",
) -> TranscriptionResult:
    """Transcribe audio file to text.

    Args:
        audio_path: Path to audio file (mp3, wav, m4a, etc.)
        method: 'groq' (free API) or 'local' (whisper.cpp)
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if method == "groq":
        return _transcribe_groq(audio_path)
    elif method == "local":
        return _transcribe_local(audio_path)
    else:
        raise ValueError(f"Unknown transcription method: {method}. Use 'groq' or 'local'.")


def _transcribe_groq(audio_path: Path) -> TranscriptionResult:
    """Transcribe using Groq's free Whisper API."""
    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("Groq package not installed. Run: pip install groq")

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set. Get one at https://console.groq.com")

    client = Groq(api_key=api_key)

    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(audio_path.name, f),
            model="whisper-large-v3",
            language="hi",
            response_format="verbose_json",
        )

    return TranscriptionResult(
        text=transcription.text,
        language=getattr(transcription, "language", "hi"),
        duration_seconds=getattr(transcription, "duration", 0.0),
    )


def _transcribe_local(audio_path: Path) -> TranscriptionResult:
    """Transcribe using local Whisper model."""
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "Whisper not installed. Run: pip install openai-whisper\n"
            "Also needs ffmpeg: brew install ffmpeg"
        )

    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path), language="hi")

    return TranscriptionResult(
        text=result["text"],
        language=result.get("language", "hi"),
        duration_seconds=sum(s["end"] - s["start"] for s in result.get("segments", [])),
    )


def extract_corrections_from_transcript(
    transcript: str,
    chart_name: str,
    pandit_name: str = "Pandit Ji",
) -> list[PanditCorrection]:
    """Extract structured corrections from a transcribed audio session.

    This uses pattern matching for common Hindi astrological phrases.
    For full LLM-based extraction, use the interpret layer.
    """
    corrections: list[PanditCorrection] = []

    # Simple keyword-based extraction for common patterns
    # In production, this would use an LLM to extract structured data
    lines = transcript.split("।")  # Split on Hindi purna viram
    if len(lines) <= 1:
        lines = transcript.split(".")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for correction patterns
        correction_keywords = [
            "नहीं", "गलत", "mat pahno", "avoid", "don't",
            "instead", "बल्कि", "correction", "actually",
        ]
        is_correction = any(kw.lower() in line.lower() for kw in correction_keywords)

        if is_correction:
            corrections.append(PanditCorrection(
                pandit_name=pandit_name,
                chart_name=chart_name,
                category="general",
                ai_said="",  # Needs manual review
                pandit_said=line,
                pandit_reasoning="",
                correction_type="override",
                status="pending",
                confidence=0.0,
                transcript=line,
            ))

    return corrections


def process_audio_session(
    audio_path: str | Path,
    chart_name: str,
    pandit_name: str = "Pandit Ji",
    method: str = "groq",
) -> tuple[TranscriptionResult, list[PanditCorrection]]:
    """Full pipeline: transcribe audio → extract corrections.

    Returns: (transcription_result, list_of_corrections)
    All corrections have status='pending' for human review.
    """
    result = transcribe_audio(audio_path, method=method)
    corrections = extract_corrections_from_transcript(
        result.text, chart_name, pandit_name
    )
    return result, corrections
