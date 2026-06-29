"""Unit tests for the YouTube playlist ETL pipeline.

Tests parsing RSS feeds XML, formatting markdown transcript files, checking safety
contracts, and validating pipeline history helper methods.
"""

from __future__ import annotations

from pathlib import Path

from ingestion.youtube_etl import (
    FeedVideo,
    TranscriptSegment,
    YouTubeETLPipeline,
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
    assert "`/ingest-youtube`" in markdown


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
        failures={"sem-legenda": RuntimeError("transcript unavailable")},
        transcripts={"ok": [TranscriptSegment("conteudo processado")]},
    )
    writer = _FakeTranscriptWriter()
    pipeline = YouTubeETLPipeline(feed_reader, transcript_fetcher, writer)

    created = pipeline.run()

    assert created == [Path("youtube-ok.md")]
    assert transcript_fetcher.fetched_ids == ["sem-legenda", "ok"]
    assert writer.written_video_ids == ["ok"]
    assert writer.processed_ids == {"ok"}


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
