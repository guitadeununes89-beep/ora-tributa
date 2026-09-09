import io
import zipfile

import pytest
from openpyxl import Workbook
from tributaria_importers.batch_workbook import (
    BatchImportError,
    extra_attributes_from_raw,
    parse_batch_workbook,
)


def _xlsx_bytes(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _csv_bytes(text: str, encoding: str = "utf-8-sig") -> bytes:
    return text.encode(encoding)


def test_valid_xlsx_file_is_parsed() -> None:
    content = _xlsx_bytes(
        [
            ["Código Interno", "Descrição", "NCM", "Data da Operação"],
            ["SKU-1", "Heparina e seus sais", "30019010", "05/01/2026"],
        ]
    )

    parsed = parse_batch_workbook(content, "lote.xlsx", max_rows=500)

    assert len(parsed.rows) == 1
    row = parsed.rows[0]
    assert row.internal_code == "SKU-1"
    assert row.description == "Heparina e seus sais"
    assert row.ncm == "30019010"
    assert row.operation_date.isoformat() == "2026-01-05"
    assert row.date_error is False
    assert parsed.truncated is False


def test_valid_csv_file_is_parsed() -> None:
    content = _csv_bytes(
        "Codigo Interno;Descricao;NCM;Data da Operacao\n"
        "SKU-2;Produto teste;30019010;2026-01-05\n"
    )

    parsed = parse_batch_workbook(content, "lote.csv", max_rows=500)

    assert len(parsed.rows) == 1
    row = parsed.rows[0]
    assert row.internal_code == "SKU-2"
    assert row.ncm == "30019010"
    assert row.operation_date.isoformat() == "2026-01-05"


def test_missing_columns_are_tolerated() -> None:
    content = _xlsx_bytes(
        [
            ["Descrição", "NCM"],
            ["Produto sem código nem data", "30019010"],
        ]
    )

    parsed = parse_batch_workbook(content, "lote.xlsx", max_rows=500)

    assert len(parsed.rows) == 1
    row = parsed.rows[0]
    assert row.internal_code is None
    assert row.operation_date is None
    assert row.date_error is False


def test_unknown_headers_are_reported_but_do_not_block_the_file() -> None:
    content = _xlsx_bytes(
        [
            ["NCM", "Coluna Desconhecida", "buyer.health_entity_status"],
            ["30019010", "valor qualquer", "HEALTH_ENTITY"],
        ]
    )

    parsed = parse_batch_workbook(content, "lote.xlsx", max_rows=500)

    assert "Coluna Desconhecida" in parsed.unknown_headers
    assert "buyer.health_entity_status" in parsed.unknown_headers
    row = parsed.rows[0]
    assert row.extra_attributes["buyer.health_entity_status"] == "HEALTH_ENTITY"


def test_invalid_date_is_flagged_without_raising() -> None:
    content = _xlsx_bytes(
        [
            ["NCM", "Data da Operação"],
            ["30019010", "não é uma data"],
        ]
    )

    parsed = parse_batch_workbook(content, "lote.xlsx", max_rows=500)

    row = parsed.rows[0]
    assert row.operation_date is None
    assert row.date_error is True


def test_row_limit_truncates_and_reports_it() -> None:
    content = _xlsx_bytes(
        [["NCM"], *[["30019010"] for _ in range(5)]]
    )

    parsed = parse_batch_workbook(content, "lote.xlsx", max_rows=3)

    assert len(parsed.rows) == 3
    assert parsed.truncated is True
    assert parsed.total_row_count == 5


def test_object_kind_is_normalized() -> None:
    content = _xlsx_bytes(
        [
            ["Tipo de Objeto", "NCM", "NBS"],
            ["Mercadoria", "30019010", ""],
            ["Serviço", "", "1.01"],
        ]
    )

    parsed = parse_batch_workbook(content, "lote.xlsx", max_rows=500)

    assert parsed.rows[0].object_kind == "GOOD"
    assert parsed.rows[1].object_kind == "SERVICE"


@pytest.mark.parametrize("extension", [".xlsm", ".xlsb", ".xls"])
def test_macro_carrying_extensions_are_rejected(extension: str) -> None:
    content = _xlsx_bytes([["NCM"], ["30019010"]])

    with pytest.raises(BatchImportError, match="segurança"):
        parse_batch_workbook(content, f"lote{extension}", max_rows=500)


def test_xlsx_with_embedded_macro_is_rejected() -> None:
    base = _xlsx_bytes([["NCM"], ["30019010"]])
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(base)) as source, zipfile.ZipFile(
        buffer, "w", zipfile.ZIP_DEFLATED
    ) as target:
        for item in source.infolist():
            target.writestr(item, source.read(item.filename))
        target.writestr("xl/vbaProject.bin", b"fake macro payload")

    with pytest.raises(BatchImportError, match="macro"):
        parse_batch_workbook(buffer.getvalue(), "lote.xlsx", max_rows=500)


def test_unsupported_extension_is_rejected() -> None:
    with pytest.raises(BatchImportError):
        parse_batch_workbook(b"whatever", "lote.txt", max_rows=500)


def test_empty_sheet_is_rejected() -> None:
    content = _xlsx_bytes([])

    with pytest.raises(BatchImportError, match="vazia"):
        parse_batch_workbook(content, "lote.xlsx", max_rows=500)


def test_extra_attributes_from_raw_excludes_known_columns() -> None:
    raw = {
        "NCM": "30019010",
        "Descrição": "Produto",
        "buyer.health_entity_status": "HEALTH_ENTITY",
    }

    attributes = extra_attributes_from_raw(raw)

    assert attributes == {"buyer.health_entity_status": "HEALTH_ENTITY"}
