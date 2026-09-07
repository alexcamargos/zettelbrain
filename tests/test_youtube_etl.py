"""Unit tests for the YouTube playlist ETL pipeline.

Tests parsing RSS feeds XML, formatting markdown transcript files, checking safety
contracts, and validating pipeline history helper methods.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from youtube_transcript_api import CouldNotRetrieveTranscript

from ingestion.youtube_etl import (
    FeedVideo,
    TranscriptSegment,
    YouTubeETLPipeline,
    _fetch_raw_transcript,
    load_processed_ids,
    parse_youtube_feed,
    render_transcript_markdown,
    slugify,
    write_transcript_artifact,
)


def test_parse_youtube_feed_extracts_video_metadata() -> None:
    """Test that parse_youtube_feed extracts the correct video metadata.

    Returns:
        None

    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
          xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <yt:videoId>abc123</yt:videoId>
        <title>Video de Teste</title>
        <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
        <published>2026-06-04T10:00:00+00:00</published>
      </entry>
    </feed>
    """

    videos = parse_youtube_feed(xml)

    assert videos == [
        FeedVideo(
            video_id="abc123",
            title="Video de Teste",
            url="https://www.youtube.com/watch?v=abc123",
            published_at="2026-06-04T10:00:00+00:00",
        )
    ]


def test_render_transcript_markdown_has_ingest_article_contract() -> None:
    """Test that render_transcript_markdown contains required metadata fields.

    Returns:
        None

    """
    video = FeedVideo("abc123", 'Titulo "Especial"', "https://youtube.test/watch?v=abc123")
    transcript = [
        TranscriptSegment("Primeira fala", start=3),
        TranscriptSegment("Segunda fala"),
    ]

    markdown = render_transcript_markdown(video, transcript)

    assert "source_kind: youtube_transcript" in markdown
    assert "video_id: abc123" in markdown
    assert '# Titulo "Especial"' in markdown
    assert "[00:03] Primeira fala" in markdown
    assert "Segunda fala" in markdown
    assert "`/youtube`" in markdown


def test_write_transcript_artifact_and_history_helpers(tmp_path: Path) -> None:
    """Test writing the transcript file and using the history logs helper methods.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None

    """
    video = FeedVideo("abc123", "Meu Video de Teste", "https://youtube.test/watch?v=abc123")
    output = write_transcript_artifact(tmp_path, video, [TranscriptSegment("conteudo")])

    assert output.name == f"youtube-abc123-{slugify('Meu Video de Teste')}.md"
    assert output.exists()

    history = tmp_path / "historico.txt"
    history.write_text("abc123\n\nxyz789\n", encoding="utf-8")
    assert load_processed_ids(history) == {"abc123", "xyz789"}


def test_youtube_etl_continues_after_individual_transcript_failure() -> None:
    """Test that a transcript failure does not abort later videos in the batch."""
    first_video = FeedVideo("sem-legenda", "Sem legenda", "https://youtube.test/watch?v=1")
    second_video = FeedVideo("ok", "Com legenda", "https://youtube.test/watch?v=2")
    feed_reader = _FakeFeedReader([first_video, second_video])
    transcript_fetcher = _FakeTranscriptFetcher(
        failures={"sem-legenda": CouldNotRetrieveTranscript("sem-legenda")},
        transcripts={"ok": [TranscriptSegment("conteudo processado")]},
    )
    writer = _FakeTranscriptWriter()
    pipeline = YouTubeETLPipeline(feed_reader, transcript_fetcher, writer)

    created = pipeline.run()

    assert created == [Path("youtube-ok.md")]
    assert transcript_fetcher.fetched_ids == ["sem-legenda", "ok"]
    assert writer.written_video_ids == ["ok"]
    assert writer.processed_ids == {"ok"}


def test_youtube_etl_does_not_catch_unexpected_exceptions() -> None:
    """Test that unexpected programming exceptions (e.g., TypeError) are not swallowed."""
    video = FeedVideo("erro-inesperado", "Erro", "https://youtube.test/watch?v=1")
    feed_reader = _FakeFeedReader([video])
    transcript_fetcher = _FakeTranscriptFetcher(
        failures={"erro-inesperado": TypeError("unexpected type error")},
        transcripts={},
    )
    writer = _FakeTranscriptWriter()
    pipeline = YouTubeETLPipeline(feed_reader, transcript_fetcher, writer)

    with pytest.raises(TypeError, match="unexpected type error"):
        pipeline.run()


def test_fetch_raw_transcript_supports_legacy_class_method_api() -> None:
    """Test transcript fetching with youtube-transcript-api 0.x style API."""
    raw_segments = _fetch_raw_transcript(_LegacyTranscriptApi, "abc123", ("pt", "en"))

    assert raw_segments == [{"text": "conteudo", "start": 1.5, "duration": 2.0}]
    assert _LegacyTranscriptApi.calls == [("abc123", ["pt", "en"])]


def test_fetch_raw_transcript_supports_current_instance_api() -> None:
    """Test transcript fetching with youtube-transcript-api 1.x style API."""
    raw_segments = _fetch_raw_transcript(_CurrentTranscriptApi, "abc123", ("pt", "en"))

    assert raw_segments == [{"text": "conteudo", "start": 1.5, "duration": 2.0}]
    assert _CurrentTranscriptApi.instances[0].calls == [("abc123", ["pt", "en"])]


class _FakeFeedReader:
    def __init__(self, videos: list[FeedVideo]) -> None:
        self.videos = videos

    def fetch_videos(self) -> list[FeedVideo]:
        return self.videos


class _FakeTranscriptFetcher:
    def __init__(
        self,
        *,
        failures: dict[str, Exception],
        transcripts: dict[str, list[TranscriptSegment]],
    ) -> None:
        self.failures = failures
        self.transcripts = transcripts
        self.fetched_ids: list[str] = []

    def fetch(self, video_id: str) -> list[TranscriptSegment]:
        self.fetched_ids.append(video_id)
        if video_id in self.failures:
            raise self.failures[video_id]
        return self.transcripts[video_id]


class _FakeTranscriptWriter:
    def __init__(self) -> None:
        self.processed_ids: set[str] = set()
        self.written_video_ids: list[str] = []

    def load_processed_ids(self) -> set[str]:
        return self.processed_ids

    def write(self, video: FeedVideo, transcript: list[TranscriptSegment]) -> Path:
        self.written_video_ids.append(video.video_id)
        return Path(f"youtube-{video.video_id}.md")

    def append_processed_id(self, video_id: str) -> None:
        self.processed_ids.add(video_id)


class _LegacyTranscriptApi:
    calls: list[tuple[str, list[str]]] = []

    @classmethod
    def get_transcript(cls, video_id: str, languages: list[str]) -> list[dict[str, float | str]]:
        cls.calls.append((video_id, languages))
        return [{"text": "conteudo", "start": 1.5, "duration": 2.0}]


class _CurrentTranscriptApi:
    instances: list[_CurrentTranscriptApi] = []

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []
        self.instances.append(self)

    def fetch(self, video_id: str, languages: list[str]) -> _FetchedTranscript:
        self.calls.append((video_id, languages))
        return _FetchedTranscript()


class _FetchedTranscript:
    def to_raw_data(self) -> list[dict[str, float | str]]:
        return [{"text": "conteudo", "start": 1.5, "duration": 2.0}]
