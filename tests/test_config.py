from pathlib import Path

from lab.config import _read_key_file


def test_reads_first_code_block(tmp_path: Path) -> None:
    f = tmp_path / "CHAVE-API.md"
    f.write_text("# Chave\n\nVer nota.\n\n```\nexemplo-falso-12345678\n```\n", encoding="utf-8")
    assert _read_key_file(f) == "exemplo-falso-12345678"


def test_missing_file_gives_empty(tmp_path: Path) -> None:
    assert _read_key_file(tmp_path / "nao-existe.md") == ""
