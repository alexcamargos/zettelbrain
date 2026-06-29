"""Testes unitários para o linter de integridade do ZettelBrain (src/zettelbrain_lint.py).

Garante a precisão e robustez das regras de validação estrutural do cofre.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from zettelbrain_lint import (
    ZettelLinter,
    parse_frontmatter_and_body,
    run_linter,
    slugify,
)


def test_slugify() -> None:
    """Valida a conversão de termos em slugs amigáveis para nomes de arquivos."""
    assert slugify("Regressão Linear") == "regressao-linear"
    assert slugify("Algoritmo de Dijkstra!") == "algoritmo-de-dijkstra"
    assert slugify("  Termo   com Espaços  ") == "termo-com-espacos"
    assert slugify("Variável_Estatística") == "variavel-estatistica"


def test_parse_frontmatter_and_body() -> None:
    """Garante o parsing correto de frontmatter YAML simples e corpo de nota."""
    content = (
        "---\n"
        "type: permanent\n"
        "id: 202606060800\n"
        "tags: [estatistica, machine-learning]\n"
        "sources: [[nota-literatura-1], [nota-literatura-2]]\n"
        "confidence: high\n"
        "deprecated: false\n"
        "---\n"
        "Este é o corpo da nota.\n"
        "Ele contém várias linhas."
    )

    frontmatter, body = parse_frontmatter_and_body(content)

    assert frontmatter["type"] == "permanent"
    assert frontmatter["id"] == "202606060800"
    assert frontmatter["tags"] == ["estatistica", "machine-learning"]
    assert frontmatter["sources"] == ["nota-literatura-1", "nota-literatura-2"]
    assert frontmatter["confidence"] == "high"
    assert frontmatter["deprecated"] is False
    assert body == "Este é o corpo da nota.\nEle contém várias linhas."


def test_parse_frontmatter_and_body_supports_indented_yaml_lists() -> None:
    """Garante suporte a listas YAML convencionais com hífens recuados."""
    content = (
        "---\n"
        "type: permanent\n"
        "id: 202606060801\n"
        "tags:\n"
        "  - risco\n"
        "  - credito\n"
        "sources:\n"
        '  - "[[nota-literatura-1]]"\n'
        '  - "[[nota-literatura-2]]"\n'
        "deprecated: false\n"
        "---\n"
        "Corpo com [[nota-relacionada]]."
    )

    frontmatter, body = parse_frontmatter_and_body(content)

    assert frontmatter["type"] == "permanent"
    assert frontmatter["id"] == "202606060801"
    assert frontmatter["tags"] == ["risco", "credito"]
    assert frontmatter["sources"] == ["[[nota-literatura-1]]", "[[nota-literatura-2]]"]
    assert frontmatter["deprecated"] is False
    assert body == "Corpo com [[nota-relacionada]]."


@pytest.fixture
def mock_zettel_vault(tmp_path: Path) -> Generator[Path, None, None]:
    """Fixture que cria uma estrutura temporária de ZettelBrain populada para testes.

    Args:
        tmp_path: Fixture nativa do pytest para diretórios temporários.

    Yields:
        Path: O caminho do diretório temporário zettelbrain.

    """
    zettel_dir = tmp_path / "zettelbrain"
    zettel_dir.mkdir()

    # Cria subpastas
    (zettel_dir / "literature").mkdir()
    (zettel_dir / "permanent").mkdir()
    (zettel_dir / "syntheses").mkdir()

    # Cria nota de literatura válida
    lit_file = zettel_dir / "literature" / "lit-linear-regression.md"
    lit_file.write_text(
        "---\n"
        "type: literature\n"
        "id: 202606060001\n"
        'title: "Linear Regression Basics"\n'
        "---\n"
        "Explica conceitos de **Regressão Linear** e **Gradiente Descendente**.\n"
        "Veja também a nota [[perm-linear-regression]].",
        encoding="utf-8",
    )

    # Cria nota permanente ativa
    perm_file = zettel_dir / "permanent" / "perm-linear-regression.md"
    perm_file.write_text(
        "---\n"
        "type: permanent\n"
        "id: 202606060002\n"
        "sources:\n"
        '  - "[[lit-linear-regression]]"\n'
        "---\n"
        "Regressão linear é uma técnica estatística.\n"
        "Ela busca encontrar a relação de **Regressão Linear** entre variáveis.\n"
        "Contém links para [[perm-gradient-descent]] e [[link-morto]].",
        encoding="utf-8",
    )

    # Cria outra nota permanente ativa (com ligação mínima e orfã)
    perm_orphan = zettel_dir / "permanent" / "perm-gradient-descent.md"
    perm_orphan.write_text(
        "---\n"
        "type: permanent\n"
        "id: 202606060003\n"
        "deprecated: false\n"
        "---\n"
        "**Gradiente Descendente** é um otimizador.\n"
        "Ele minimiza a função de custo usando **Regressão Linear**.\n"
        "Possui apenas um link de saída: [[perm-linear-regression]].",
        encoding="utf-8",
    )

    # Cria nota deprecada
    perm_dep = zettel_dir / "permanent" / "perm-deprecated-note.md"
    perm_dep.write_text(
        "---\n"
        "type: permanent\n"
        "id: 202606060004\n"
        "deprecated: true\n"
        "superseded_by: [[perm-linear-regression]]\n"
        "---\n"
        "Esta nota antiga foi deprecada.",
        encoding="utf-8",
    )

    # Nota ativa apontando para a deprecada para gerar aviso
    perm_ref_dep = zettel_dir / "permanent" / "perm-refers-deprecated.md"
    perm_ref_dep.write_text(
        "---\n"
        "type: permanent\n"
        "id: 202606060005\n"
        "---\n"
        "Esta nota ativamente aponta para [[perm-deprecated-note]].\n"
        "E também para [[perm-linear-regression]] para não cair na ligação mínima.",
        encoding="utf-8",
    )

    # Arquivo de índice do cofre
    index_file = zettel_dir / "index.md"
    index_file.write_text(
        "# Índice\n- [[lit-linear-regression]]\n- [[perm-linear-regression]]",
        encoding="utf-8",
    )

    yield zettel_dir


def test_linter_validation_rules(mock_zettel_vault: Path) -> None:
    """Verifica se todas as regras de integridade do linter operam corretamente."""
    linter = ZettelLinter(mock_zettel_vault)
    linter.scan_vault()
    result = linter.run()

    # Total de arquivos md mapeados no cofre (6 arquivos)
    assert result.total_notes == 6
    assert result.literature_count == 1
    assert result.permanent_count == 4
    assert result.other_count == 1

    # 1. Links Mortos
    # 'perm-linear-regression.md' contém link para [[link-morto]]
    dead_links = [e for e in result.errors if e.type == "dead_link"]
    assert len(dead_links) == 1
    assert dead_links[0].details["target"] == "link-morto"
    assert "perm-linear-regression.md" in dead_links[0].file_path.replace("\\", "/")

    # 2. Notas Órfãs (grafo conceitual)
    # A nota 'perm-refers-deprecated' e 'lit-linear-regression' não têm links
    # conceituais de entrada.
    # 'perm-gradient-descent' recebe link de 'perm-linear-regression',
    # 'perm-linear-regression' recebe de 'lit-linear-regression'
    orphans = [w for w in result.warnings if w.type == "orphan_note"]
    orphan_slugs = [Path(w.file_path).stem for w in orphans]
    assert "perm-refers-deprecated" in orphan_slugs
    # lit-linear-regression não é órfã pois é referenciada nas sources de perm-linear-regression
    assert "lit-linear-regression" not in orphan_slugs

    # 3. Ligação Mínima ao Grafo
    # 'perm-gradient-descent' possui apenas [[perm-linear-regression]] (1 link de saída no corpo)
    minimal = [w for w in result.warnings if w.type == "minimal_connection"]
    assert len(minimal) == 1
    assert "perm-gradient-descent.md" in minimal[0].file_path.replace("\\", "/")

    # 4. Referência a nota deprecada
    # 'perm-refers-deprecated' aponta para 'perm-deprecated-note' (que tem deprecated: true)
    dep_refs = [w for w in result.warnings if w.type == "deprecated_reference"]
    assert len(dep_refs) == 1
    assert "perm-deprecated-note.md" in dep_refs[0].file_path.replace("\\", "/")
    assert "perm-deprecated-note" in dep_refs[0].message

    # 5. Padrões Emergentes
    # O termo "Regressão Linear" (ou "Regressao Linear") aparece em 3 notas distintas:
    # - lit-linear-regression ("Regressão Linear")
    # - perm-linear-regression ("Regressão Linear")
    # - perm-gradient-descent ("Regressão Linear")
    # Mas o slug 'regressao-linear' não existe no cofre.
    # O termo "Gradiente Descendente" aparece em:
    # - lit-linear-regression
    # - perm-gradient-descent
    # (apenas 2 notas, portanto não atinge a frequência mínima de 3)
    assert "Regressão Linear" in result.emergent_patterns
    assert "Gradiente Descendente" not in result.emergent_patterns


def test_linter_sources_with_alias_do_not_create_false_dead_links(tmp_path: Path) -> None:
    """Garante que wikilinks com alias em `sources` sejam normalizados corretamente."""
    zettel_dir = tmp_path / "zettelbrain"
    literature_dir = zettel_dir / "literature"
    permanent_dir = zettel_dir / "permanent"
    literature_dir.mkdir(parents=True)
    permanent_dir.mkdir(parents=True)

    (literature_dir / "nota-base.md").write_text(
        '---\ntitle: "Nota Base"\n---\nConteudo.',
        encoding="utf-8",
    )
    (permanent_dir / "nota-principal.md").write_text(
        '---\nsources:\n  - "[[nota-base|Resumo]]"\n---\nCorpo sem links extras.',
        encoding="utf-8",
    )

    linter = ZettelLinter(zettel_dir)
    linter.scan_vault()
    result = linter.run()

    dead_link_targets = [
        error.details.get("target") for error in result.errors if error.type == "dead_link"
    ]
    assert "nota-base|Resumo" not in dead_link_targets
    assert "nota-base" not in dead_link_targets


def test_linter_normalizes_permanent_sources_for_obsidian(tmp_path: Path) -> None:
    """Garante que sources ambíguas sejam reescritas como wikilinks literais."""
    zettel_dir = tmp_path / "zettelbrain"
    literature_dir = zettel_dir / "literature"
    permanent_dir = zettel_dir / "permanent"
    literature_dir.mkdir(parents=True)
    permanent_dir.mkdir(parents=True)

    (literature_dir / "nota-base.md").write_text(
        "---\ntype: literature\n---\nConteudo.",
        encoding="utf-8",
    )
    permanent_file = permanent_dir / "nota-principal.md"
    permanent_file.write_text(
        "---\n"
        "type: permanent\n"
        "sources: [[nota-base]]\n"
        "---\n"
        "Corpo com [[nota-base]] e [[nota-base]].",
        encoding="utf-8",
    )

    result = run_linter(zettel_dir)

    content = permanent_file.read_text(encoding="utf-8")
    assert 'sources:\n  - "[[nota-base]]"' in content
    assert [fix for fix in result.fixes if fix.type == "permanent_sources_format"]
    dead_link_targets = [
        error.details.get("target") for error in result.errors if error.type == "dead_link"
    ]
    assert "nota-base" not in dead_link_targets


def test_linter_warns_about_unsafe_permanent_sources_without_fix(tmp_path: Path) -> None:
    """Garante aviso quando sources não está em formato resolvível pelo Obsidian."""
    zettel_dir = tmp_path / "zettelbrain"
    literature_dir = zettel_dir / "literature"
    permanent_dir = zettel_dir / "permanent"
    literature_dir.mkdir(parents=True)
    permanent_dir.mkdir(parents=True)

    (literature_dir / "nota-base.md").write_text(
        "---\ntype: literature\n---\nConteudo.",
        encoding="utf-8",
    )
    permanent_file = permanent_dir / "nota-principal.md"
    permanent_file.write_text(
        "---\n"
        "type: permanent\n"
        "sources: [[nota-base]]\n"
        "---\n"
        "Corpo com [[nota-base]] e [[outra-nota]].",
        encoding="utf-8",
    )

    result = run_linter(zettel_dir, fix_sources=False)

    warnings = [
        warning for warning in result.warnings if warning.type == "permanent_sources_format"
    ]
    assert len(warnings) == 1
    assert "sources: [[nota-base]]" in permanent_file.read_text(encoding="utf-8")


def test_linter_warns_about_literature_filename_pattern_without_fix(tmp_path: Path) -> None:
    """Verifica a regra de nomes para notas de literatura sem aplicar correção."""
    zettel_dir = tmp_path / "zettelbrain"
    literature_dir = zettel_dir / "literature"
    literature_dir.mkdir(parents=True)

    (literature_dir / "lit-youtube-derivada.md").write_text(
        "---\n"
        "type: literature\n"
        "source_kind: youtube_transcript\n"
        'title: "O que é uma Derivada?"\n'
        "authors: [Canal Matematica]\n"
        "---\n"
        "Conteudo.",
        encoding="utf-8",
    )

    result = run_linter(zettel_dir, fix_filenames=False)

    filename_warnings = [
        warning for warning in result.warnings if warning.type == "literature_filename_pattern"
    ]
    assert len(filename_warnings) == 1
    assert filename_warnings[0].details["expected_filename"] == (
        "youtube-canal-matematica-o-que-e-uma-derivada.md"
    )
    assert not result.fixes


def test_linter_renames_youtube_literature_and_updates_wikilinks(tmp_path: Path) -> None:
    """Garante correção automática do nome e dos wikilinks para notas do YouTube."""
    zettel_dir = tmp_path / "zettelbrain"
    literature_dir = zettel_dir / "literature"
    permanent_dir = zettel_dir / "permanent"
    literature_dir.mkdir(parents=True)
    permanent_dir.mkdir()

    old_note = literature_dir / "lit-youtube-derivada.md"
    old_note.write_text(
        "---\n"
        "type: literature\n"
        "source_kind: youtube_transcript\n"
        'title: "O que é uma Derivada?"\n'
        "authors: [Canal Matematica]\n"
        "---\n"
        "Conteudo.",
        encoding="utf-8",
    )
    index_file = zettel_dir / "index.md"
    index_file.write_text("- [[lit-youtube-derivada]]\n", encoding="utf-8")
    permanent_file = permanent_dir / "perm-derivada.md"
    permanent_file.write_text(
        "---\n"
        "type: permanent\n"
        "sources:\n"
        '  - "[[lit-youtube-derivada|Video]]"\n'
        "---\n"
        "Texto com [[lit-youtube-derivada]].",
        encoding="utf-8",
    )

    result = run_linter(zettel_dir)

    new_slug = "youtube-canal-matematica-o-que-e-uma-derivada"
    new_note = literature_dir / f"{new_slug}.md"
    assert not old_note.exists()
    assert new_note.exists()
    assert len(result.fixes) == 1
    assert result.fixes[0].details["old_slug"] == "lit-youtube-derivada"
    assert result.fixes[0].details["new_slug"] == new_slug
    assert result.fixes[0].details["updated_references"] == 3
    assert f"[[{new_slug}]]" in index_file.read_text(encoding="utf-8")
    permanent_content = permanent_file.read_text(encoding="utf-8")
    assert f"[[{new_slug}|Video]]" in permanent_content
    assert f"[[{new_slug}]]" in permanent_content
    assert not [w for w in result.warnings if w.type == "literature_filename_pattern"]


def test_linter_renames_article_literature(tmp_path: Path) -> None:
    """Garante correção automática do nome para artigos web."""
    zettel_dir = tmp_path / "zettelbrain"
    literature_dir = zettel_dir / "literature"
    literature_dir.mkdir(parents=True)

    old_note = literature_dir / "lit-web-artigo.md"
    old_note.write_text(
        "---\n"
        "type: literature\n"
        "source_kind: web_article\n"
        'title: "Título do Artigo"\n'
        "---\n"
        "Conteudo.",
        encoding="utf-8",
    )

    result = run_linter(zettel_dir)

    assert not old_note.exists()
    assert (literature_dir / "article-titulo-do-artigo.md").exists()
    assert len(result.fixes) == 1
    assert result.fixes[0].details["new_slug"] == "article-titulo-do-artigo"
