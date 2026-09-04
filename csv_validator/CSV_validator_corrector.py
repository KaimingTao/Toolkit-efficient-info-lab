"""CSV validator and corrector workflow.

Purpose: validate CSV compatibility and optionally write a corrected file.
Usage: python CSV_validator_corrector.py <input.csv>; see
CSV_validator_corrector.md for full options and examples.
Substeps: detect encoding and formatting issues, validate rows, compare the
target format, then report or write corrected output.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - depends on local environment
    yaml = None


CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass
class Issue:
    severity: str
    message: str


@dataclass
class OutputFormatConfig:
    delimiter: str = ","
    line_terminator: str = "\n"
    encoding: str = "utf-8"
    quote_style: str = "minimal"
    bom: bool = False


@dataclass
class ValidationResult:
    issues: list[Issue]
    delimiter: str
    rows: list[list[str]]
    encoding: str
    newline_style: str


def detect_encoding(raw: bytes) -> tuple[str, list[Issue]]:
    issues: list[Issue] = []
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        issues.append(
            Issue("warning", "UTF-16 BOM detected; some CSV tools expect UTF-8.")
        )
        return "utf-16", issues
    if raw.startswith(b"\xef\xbb\xbf"):
        issues.append(
            Issue(
                "warning",
                "UTF-8 BOM detected; first header may be misread by weak parsers.",
            )
        )
        return "utf-8-sig", issues
    try:
        raw.decode("utf-8")
        return "utf-8", issues
    except UnicodeDecodeError:
        issues.append(
            Issue("warning", "File is not valid UTF-8; decoding as Latin-1 fallback.")
        )
        return "latin-1", issues


def detect_newline_issues(raw: bytes) -> list[Issue]:
    issues: list[Issue] = []
    has_crlf = b"\r\n" in raw
    has_lf = b"\n" in raw
    has_cr = b"\r" in raw

    if has_crlf and raw.replace(b"\r\n", b"").find(b"\r") != -1:
        issues.append(Issue("warning", "Mixed CRLF and CR newline styles detected."))
    elif has_crlf and raw.replace(b"\r\n", b"").find(b"\n") != -1:
        issues.append(Issue("warning", "Mixed CRLF and LF newline styles detected."))
    elif has_cr and not has_crlf:
        issues.append(
            Issue(
                "warning",
                "CR-only line endings detected; many tools expect LF or CRLF.",
            )
        )

    if b"\r" in raw:
        issues.append(
            Issue(
                "info",
                "Carriage return characters are present; some tools may show these as ^M.",
            )
        )

    if raw and not raw.endswith((b"\n", b"\r")):
        issues.append(
            Issue(
                "info",
                "File does not end with a newline; most parsers accept this, but partial exports may look similar.",
            )
        )

    if raw.endswith((b"\n\n", b"\r\n\r\n")):
        issues.append(Issue("info", "Trailing blank line detected."))

    if not has_lf and not has_cr:
        issues.append(
            Issue(
                "warning",
                "No line terminators detected; file may be a single row or malformed export.",
            )
        )

    return issues


def detect_newline_style(raw: bytes) -> str:
    has_crlf = b"\r\n" in raw
    has_lf = b"\n" in raw.replace(b"\r\n", b"")
    has_cr = b"\r" in raw.replace(b"\r\n", b"")

    styles = []
    if has_crlf:
        styles.append("crlf")
    if has_lf:
        styles.append("lf")
    if has_cr:
        styles.append("cr")

    if len(styles) > 1:
        return "mixed"
    if styles:
        return styles[0]
    return "none"


def choose_delimiter(sample: str) -> tuple[str, list[Issue]]:
    issues: list[Issue] = []
    candidates = [",", ";", "\t", "|"]
    counts = {candidate: sample.count(candidate) for candidate in candidates}
    best = max(counts, key=counts.get)

    if counts[best] == 0:
        issues.append(
            Issue(
                "warning",
                "Could not confidently detect a delimiter; defaulting to comma.",
            )
        )
        return ",", issues

    non_zero = [delimiter for delimiter, count in counts.items() if count > 0]
    if len(non_zero) > 1:
        issues.append(
            Issue(
                "info",
                "Multiple possible delimiters found in sample; parser is using the most frequent candidate "
                f"({best!r}).",
            )
        )
    return best, issues


def sniff_quote_balance(text: str) -> list[Issue]:
    issues: list[Issue] = []
    odd_quote_lines = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if line.count('"') % 2 == 1:
            odd_quote_lines.append(idx)
    if odd_quote_lines:
        preview = ", ".join(str(i) for i in odd_quote_lines[:5])
        issues.append(
            Issue("warning", f"Lines with odd double-quote counts detected: {preview}.")
        )
    return issues


def parse_rows(text: str, delimiter: str) -> tuple[list[list[str]], list[Issue]]:
    try:
        return list(csv.reader(text.splitlines(), delimiter=delimiter)), []
    except csv.Error as exc:
        return [], [Issue("error", f"CSV parser error: {exc}")]


def validate_rows(rows: list[list[str]]) -> list[Issue]:
    issues: list[Issue] = []

    if not rows:
        return [Issue("error", "File is empty.")]

    header = rows[0]
    expected_columns = len(header)

    if expected_columns == 0:
        issues.append(Issue("error", "Header row is empty."))
        return issues

    normalized_header = []
    seen_headers = set()
    for idx, name in enumerate(header, start=1):
        if name == "":
            issues.append(Issue("warning", f"Header column {idx} is empty."))
        if name != name.strip():
            issues.append(
                Issue(
                    "warning",
                    f"Header column {idx} has leading or trailing whitespace.",
                )
            )
        lowered = name.strip().lower()
        if lowered in seen_headers and lowered:
            issues.append(
                Issue("warning", f"Duplicate header name detected: {name!r}.")
            )
        seen_headers.add(lowered)
        normalized_header.append(name.strip())

    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != expected_columns:
            issues.append(
                Issue(
                    "error",
                    f"Row {row_number} has {len(row)} columns; expected {expected_columns}.",
                )
            )

        for col_number, value in enumerate(row, start=1):
            if value != value.strip():
                issues.append(
                    Issue(
                        "info",
                        f"Row {row_number}, column {col_number} has leading or trailing whitespace.",
                    )
                )
            if CONTROL_CHAR_PATTERN.search(value):
                issues.append(
                    Issue(
                        "warning",
                        f"Row {row_number}, column {col_number} contains control characters.",
                    )
                )
            if value.startswith(("=", "+", "-", "@")):
                issues.append(
                    Issue(
                        "warning",
                        f"Row {row_number}, column {col_number} may trigger spreadsheet formula interpretation.",
                    )
                )
            if value.isdigit() and len(value) > 1 and value.startswith("0"):
                issues.append(
                    Issue(
                        "warning",
                        f"Row {row_number}, column {col_number} has leading zeros that spreadsheet tools may strip.",
                    )
                )
            if value.isdigit() and len(value) >= 16:
                issues.append(
                    Issue(
                        "warning",
                        f"Row {row_number}, column {col_number} is a long integer that may lose precision in spreadsheets.",
                    )
                )

    if len(rows) == 1:
        issues.append(
            Issue("warning", "Only one row detected; file may contain header only.")
        )

    return issues


def compare_with_expected_format(
    result: ValidationResult, config: OutputFormatConfig
) -> list[Issue]:
    issues: list[Issue] = []

    if result.delimiter != config.delimiter:
        issues.append(
            Issue(
                "warning",
                f"Detected delimiter {result.delimiter!r} does not match expected {config.delimiter!r}.",
            )
        )

    expected_newline_style = {
        "\n": "lf",
        "\r\n": "crlf",
        "\r": "cr",
    }.get(config.line_terminator)
    if expected_newline_style and result.newline_style not in {
        "mixed",
        "none",
        expected_newline_style,
    }:
        issues.append(
            Issue(
                "warning",
                f"Detected newline style {result.newline_style!r} does not match expected {expected_newline_style!r}.",
            )
        )

    expected_encoding = (
        "utf-8-sig" if config.bom and config.encoding == "utf-8" else config.encoding
    )
    if result.encoding != expected_encoding:
        issues.append(
            Issue(
                "warning",
                f"Detected encoding {result.encoding!r} does not match expected {expected_encoding!r}.",
            )
        )

    return issues


def load_config(path: Path) -> OutputFormatConfig:
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required for --config support. Install it with: pip install pyyaml"
        )

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    output_format = data.get("expected_output_format", {})

    delimiter = output_format.get("delimiter", ",")
    if delimiter not in {",", ";", "\t", "|"}:
        raise ValueError(
            "expected_output_format.delimiter must be one of ',', ';', '\\t', '|'."
        )

    line_terminator = output_format.get("line_terminator", "\n")
    if line_terminator not in {"\n", "\r\n", "\r"}:
        raise ValueError(
            "expected_output_format.line_terminator must be one of '\\n', '\\r\\n', '\\r'."
        )

    quote_style = output_format.get("quote_style", "minimal")
    if quote_style not in {"minimal", "all"}:
        raise ValueError(
            "expected_output_format.quote_style must be 'minimal' or 'all'."
        )

    encoding = output_format.get("encoding", "utf-8")
    if encoding not in {"utf-8", "latin-1", "utf-16"}:
        raise ValueError(
            "expected_output_format.encoding must be 'utf-8', 'latin-1', or 'utf-16'."
        )

    bom = bool(output_format.get("bom", False))
    if bom and encoding != "utf-8":
        raise ValueError(
            "expected_output_format.bom is only supported with utf-8 output."
        )

    return OutputFormatConfig(
        delimiter=delimiter,
        line_terminator=line_terminator,
        encoding=encoding,
        quote_style=quote_style,
        bom=bom,
    )


def write_corrected_csv(
    rows: list[list[str]], output_path: Path, config: OutputFormatConfig
) -> None:
    quoting = csv.QUOTE_ALL if config.quote_style == "all" else csv.QUOTE_MINIMAL
    output_encoding = (
        "utf-8-sig" if config.bom and config.encoding == "utf-8" else config.encoding
    )
    with output_path.open("w", encoding=output_encoding, newline="") as handle:
        writer = csv.writer(
            handle,
            delimiter=config.delimiter,
            lineterminator=config.line_terminator,
            quoting=quoting,
        )
        writer.writerows(rows)


def print_report(
    path: Path,
    issues: list[Issue],
    delimiter: str,
    config: OutputFormatConfig | None = None,
) -> int:
    print(f"File: {path}")
    print(f"Detected delimiter: {delimiter!r}")
    if config is not None:
        print(
            "Expected output format: "
            f"delimiter={config.delimiter!r}, "
            f"line_terminator={config.line_terminator.encode('unicode_escape').decode('ascii')}, "
            f"encoding={'utf-8-sig' if config.bom and config.encoding == 'utf-8' else config.encoding}, "
            f"quote_style={config.quote_style}"
        )
    if not issues:
        print("No issues found.")
        return 0

    severity_rank = {"error": 0, "warning": 1, "info": 2}
    sorted_issues = sorted(
        issues, key=lambda issue: (severity_rank.get(issue.severity, 9), issue.message)
    )

    print("Issues:")
    for issue in sorted_issues:
        print(f"- [{issue.severity}] {issue.message}")

    return 1 if any(issue.severity == "error" for issue in issues) else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a CSV file and optionally rewrite it into a configured output format."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to validate.")
    parser.add_argument(
        "--config",
        default="corrector_config.yaml",
        help="Path to the YAML config describing the expected output format. Default: corrector_config.yaml",
    )
    parser.add_argument(
        "--write-corrected",
        help="Write a corrected CSV using the configured output format to this path.",
    )
    args = parser.parse_args()

    path = Path(args.csv_file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    raw = path.read_bytes()
    encoding, issues = detect_encoding(raw)
    newline_style = detect_newline_style(raw)
    issues.extend(detect_newline_issues(raw))

    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        print(f"Failed to decode file using {encoding}: {exc}", file=sys.stderr)
        return 2

    delimiter, delimiter_issues = choose_delimiter("\n".join(text.splitlines()[:10]))
    issues.extend(delimiter_issues)
    issues.extend(sniff_quote_balance(text))
    rows, row_parse_issues = parse_rows(text, delimiter)
    issues.extend(row_parse_issues)
    issues.extend(validate_rows(rows))

    config: OutputFormatConfig | None = None
    config_path = Path(args.config)
    if args.config:
        try:
            config = load_config(config_path)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        issues.extend(
            compare_with_expected_format(
                ValidationResult(
                    issues=issues,
                    delimiter=delimiter,
                    rows=rows,
                    encoding=encoding,
                    newline_style=newline_style,
                ),
                config,
            )
        )

    if args.write_corrected:
        if config is None:
            print(
                "A valid --config file is required when using --write-corrected.",
                file=sys.stderr,
            )
            return 2
        if any(issue.severity == "error" for issue in issues):
            print(
                "Cannot write corrected CSV because parsing errors are present.",
                file=sys.stderr,
            )
            return 2
        write_corrected_csv(rows, Path(args.write_corrected), config)

    return print_report(path, issues, delimiter, config)


if __name__ == "__main__":
    raise SystemExit(main())
