const DEFAULT_CONFIG = {
  delimiter: ",",
  lineTerminator: "\n",
  encoding: "utf-8",
  quoteStyle: "minimal",
  bom: false,
};

const SEVERITY_RANK = { error: 0, warning: 1, info: 2 };
const CONTROL_CHAR_PATTERN = /[\x00-\x08\x0b\x0c\x0e-\x1f]/;

const state = {
  csvFileName: null,
  csvBytes: null,
  csvText: "",
  detectedEncoding: null,
  correctedCsv: "",
  analysis: null,
};

const elements = {
  csvFileInput: document.getElementById("csvFileInput"),
  delimiterSelect: document.getElementById("delimiterSelect"),
  lineTerminatorSelect: document.getElementById("lineTerminatorSelect"),
  encodingSelect: document.getElementById("encodingSelect"),
  quoteStyleSelect: document.getElementById("quoteStyleSelect"),
  bomCheckbox: document.getElementById("bomCheckbox"),
  analyzeButton: document.getElementById("analyzeButton"),
  downloadButton: document.getElementById("downloadButton"),
  resetConfigButton: document.getElementById("resetConfigButton"),
  csvFileName: document.getElementById("csvFileName"),
  detectedFormat: document.getElementById("detectedFormat"),
  targetFormat: document.getElementById("targetFormat"),
  rowCount: document.getElementById("rowCount"),
  columnCount: document.getElementById("columnCount"),
  issueCount: document.getElementById("issueCount"),
  issuesList: document.getElementById("issuesList"),
  outputPreview: document.getElementById("outputPreview"),
};

applyConfigToForm(DEFAULT_CONFIG);
syncBomAvailability();
renderEmptyIssues();

elements.csvFileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  state.csvFileName = file.name;
  state.csvBytes = new Uint8Array(await file.arrayBuffer());
  const decoded = decodeCsvBytes(state.csvBytes);
  state.csvText = decoded.text;
  state.detectedEncoding = decoded.encoding;
  elements.csvFileName.textContent = file.name;
});

elements.resetConfigButton.addEventListener("click", () => {
  applyConfigToForm(DEFAULT_CONFIG);
  syncBomAvailability();
});

elements.analyzeButton.addEventListener("click", () => {
  if (!state.csvText) {
    renderFatalIssue("Select a CSV file before running analysis.");
    return;
  }

  const configResult = readConfigFromForm();
  if (configResult.error) {
    renderFatalIssue(configResult.error);
    return;
  }

  const analysis = analyzeCsv(state.csvText, configResult.config, state.detectedEncoding ?? "utf-8");
  state.analysis = analysis;
  state.correctedCsv = buildCsv(analysis.rows, configResult.config);
  renderAnalysis(analysis, configResult.config);
});

elements.downloadButton.addEventListener("click", () => {
  if (!state.correctedCsv || !state.analysis) {
    return;
  }

  const configResult = readConfigFromForm();
  if (configResult.error) {
    renderFatalIssue(configResult.error);
    return;
  }

  const correctedCsv = buildCsv(state.analysis.rows, configResult.config);
  const blob = createDownloadBlob(correctedCsv, configResult.config);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;

  const baseName = state.csvFileName ? state.csvFileName.replace(/\.csv$/i, "") : "corrected";
  link.download = `${baseName}.corrected.csv`;
  link.click();
  URL.revokeObjectURL(url);
});

elements.encodingSelect.addEventListener("change", () => {
  syncBomAvailability();
});

function readConfigFromForm() {
  const config = {
    delimiter: elements.delimiterSelect.value,
    lineTerminator: elements.lineTerminatorSelect.value,
    encoding: elements.encodingSelect.value,
    quoteStyle: elements.quoteStyleSelect.value,
    bom: elements.bomCheckbox.checked,
  };

  if (![",", ";", "\t", "|"].includes(config.delimiter)) {
    return { error: "Delimiter must be one of ',', ';', '\\t', '|'." };
  }
  if (!["\n", "\r\n", "\r"].includes(config.lineTerminator)) {
    return { error: "Line terminator must be one of '\\n', '\\r\\n', '\\r'." };
  }
  if (!["utf-8", "latin-1", "utf-16"].includes(config.encoding)) {
    return { error: "Encoding must be utf-8, latin-1, or utf-16." };
  }
  if (!["minimal", "all"].includes(config.quoteStyle)) {
    return { error: "Quote style must be minimal or all." };
  }
  if (config.bom && config.encoding !== "utf-8") {
    return { error: "UTF-8 BOM output is only supported when encoding is utf-8." };
  }

  return { config };
}

function applyConfigToForm(config) {
  elements.delimiterSelect.value = config.delimiter;
  elements.lineTerminatorSelect.value = config.lineTerminator;
  elements.encodingSelect.value = config.encoding;
  elements.quoteStyleSelect.value = config.quoteStyle;
  elements.bomCheckbox.checked = config.bom;
}

function syncBomAvailability() {
  const bomSupported = elements.encodingSelect.value === "utf-8";
  if (!bomSupported) {
    elements.bomCheckbox.checked = false;
  }
  elements.bomCheckbox.disabled = !bomSupported;
}

function analyzeCsv(csvText, config, detectedEncoding) {
  const issues = [];
  const newlineStyle = detectNewlineStyle(csvText);
  issues.push(...detectNewlineIssues(csvText));

  const [delimiter, delimiterIssues] = chooseDelimiter(csvText.split(/\r\n|\n|\r/).slice(0, 10).join("\n"));
  issues.push(...delimiterIssues);
  issues.push(...sniffQuoteBalance(csvText));

  const parseResult = parseCsv(csvText, delimiter);
  issues.push(...parseResult.issues);

  const rows = parseResult.rows;
  issues.push(...validateRows(rows));
  issues.push(...compareWithExpectedFormat({ delimiter, newlineStyle, encoding: detectedEncoding }, config));

  issues.sort((a, b) => {
    const rank = (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9);
    return rank !== 0 ? rank : a.message.localeCompare(b.message);
  });

  return {
    delimiter,
    newlineStyle,
    detectedEncoding,
    rows,
    issues,
  };
}

function detectNewlineStyle(text) {
  const hasCrlf = /\r\n/.test(text);
  const stripped = text.replace(/\r\n/g, "");
  const hasLf = /\n/.test(stripped);
  const hasCr = /\r/.test(stripped);
  const styles = [];

  if (hasCrlf) {
    styles.push("crlf");
  }
  if (hasLf) {
    styles.push("lf");
  }
  if (hasCr) {
    styles.push("cr");
  }

  if (styles.length > 1) {
    return "mixed";
  }
  return styles[0] ?? "none";
}

function detectNewlineIssues(text) {
  const issues = [];
  const hasCrlf = /\r\n/.test(text);
  const withoutCrlf = text.replace(/\r\n/g, "");
  const hasLf = /\n/.test(withoutCrlf);
  const hasCr = /\r/.test(withoutCrlf);

  if (hasCrlf && hasCr) {
    issues.push(issue("warning", "Mixed CRLF and CR newline styles detected."));
  } else if (hasCrlf && hasLf) {
    issues.push(issue("warning", "Mixed CRLF and LF newline styles detected."));
  } else if (hasCr && !hasCrlf) {
    issues.push(issue("warning", "CR-only line endings detected; many tools expect LF or CRLF."));
  }

  if (/\r/.test(text)) {
    issues.push(issue("info", "Carriage return characters are present; some tools may show these as ^M."));
  }
  if (text && !/[\n\r]$/.test(text)) {
    issues.push(issue("info", "File does not end with a newline; most parsers accept this, but partial exports may look similar."));
  }
  if (text.endsWith("\n\n") || text.endsWith("\r\n\r\n")) {
    issues.push(issue("info", "Trailing blank line detected."));
  }
  if (!/[\n\r]/.test(text)) {
    issues.push(issue("warning", "No line terminators detected; file may be a single row or malformed export."));
  }

  return issues;
}

function chooseDelimiter(sample) {
  const candidates = [",", ";", "\t", "|"];
  const counts = Object.fromEntries(candidates.map((candidate) => [candidate, sample.split(candidate).length - 1]));
  const delimiter = candidates.reduce((best, candidate) => (counts[candidate] > counts[best] ? candidate : best), ",");
  const issues = [];

  if (counts[delimiter] === 0) {
    issues.push(issue("warning", "Could not confidently detect a delimiter; defaulting to comma."));
    return [",", issues];
  }

  const nonZero = candidates.filter((candidate) => counts[candidate] > 0);
  if (nonZero.length > 1) {
    issues.push(issue("info", `Multiple possible delimiters found in sample; parser is using the most frequent candidate (${JSON.stringify(delimiter)}).`));
  }

  return [delimiter, issues];
}

function sniffQuoteBalance(text) {
  const issues = [];
  const oddLines = text.split(/\r\n|\n|\r/).flatMap((line, index) => (line.split('"').length - 1) % 2 === 1 ? [index + 1] : []);
  if (oddLines.length) {
    issues.push(issue("warning", `Lines with odd double-quote counts detected: ${oddLines.slice(0, 5).join(", ")}.`));
  }
  return issues;
}

function parseCsv(text, delimiter) {
  const rows = [];
  const issues = [];
  let row = [];
  let value = "";
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const nextChar = text[index + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        value += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (!inQuotes && char === delimiter) {
      row.push(value);
      value = "";
      continue;
    }

    if (!inQuotes && (char === "\n" || char === "\r")) {
      if (char === "\r" && nextChar === "\n") {
        index += 1;
      }
      row.push(value);
      rows.push(row);
      row = [];
      value = "";
      continue;
    }

    value += char;
  }

  if (inQuotes) {
    issues.push(issue("error", "CSV parser error: unmatched quote in file."));
    return { rows: [], issues };
  }

  if (value !== "" || row.length) {
    row.push(value);
    rows.push(row);
  }

  return { rows, issues };
}

function validateRows(rows) {
  const issues = [];
  if (!rows.length) {
    return [issue("error", "File is empty.")];
  }

  const header = rows[0];
  const expectedColumns = header.length;
  if (!expectedColumns) {
    return [issue("error", "Header row is empty.")];
  }

  const seenHeaders = new Set();
  header.forEach((name, index) => {
    if (name === "") {
      issues.push(issue("warning", `Header column ${index + 1} is empty.`));
    }
    if (name !== name.trim()) {
      issues.push(issue("warning", `Header column ${index + 1} has leading or trailing whitespace.`));
    }
    const lowered = name.trim().toLowerCase();
    if (lowered && seenHeaders.has(lowered)) {
      issues.push(issue("warning", `Duplicate header name detected: ${JSON.stringify(name)}.`));
    }
    seenHeaders.add(lowered);
  });

  rows.slice(1).forEach((row, rowIndex) => {
    const rowNumber = rowIndex + 2;
    if (row.length !== expectedColumns) {
      issues.push(issue("error", `Row ${rowNumber} has ${row.length} columns; expected ${expectedColumns}.`));
    }

    row.forEach((value, colIndex) => {
      const colNumber = colIndex + 1;
      if (value !== value.trim()) {
        issues.push(issue("info", `Row ${rowNumber}, column ${colNumber} has leading or trailing whitespace.`));
      }
      if (CONTROL_CHAR_PATTERN.test(value)) {
        issues.push(issue("warning", `Row ${rowNumber}, column ${colNumber} contains control characters.`));
      }
      if (/^[=+\-@]/.test(value)) {
        issues.push(issue("warning", `Row ${rowNumber}, column ${colNumber} may trigger spreadsheet formula interpretation.`));
      }
      if (/^\d+$/.test(value) && value.length > 1 && value.startsWith("0")) {
        issues.push(issue("warning", `Row ${rowNumber}, column ${colNumber} has leading zeros that spreadsheet tools may strip.`));
      }
      if (/^\d+$/.test(value) && value.length >= 16) {
        issues.push(issue("warning", `Row ${rowNumber}, column ${colNumber} is a long integer that may lose precision in spreadsheets.`));
      }
    });
  });

  if (rows.length === 1) {
    issues.push(issue("warning", "Only one row detected; file may contain header only."));
  }

  return issues;
}

function compareWithExpectedFormat(result, config) {
  const issues = [];
  if (result.delimiter !== config.delimiter) {
    issues.push(issue("warning", `Detected delimiter ${JSON.stringify(result.delimiter)} does not match expected ${JSON.stringify(config.delimiter)}.`));
  }

  const expectedNewlineStyle = { "\n": "lf", "\r\n": "crlf", "\r": "cr" }[config.lineTerminator];
  if (expectedNewlineStyle && !["mixed", "none", expectedNewlineStyle].includes(result.newlineStyle)) {
    issues.push(issue("warning", `Detected newline style ${JSON.stringify(result.newlineStyle)} does not match expected ${JSON.stringify(expectedNewlineStyle)}.`));
  }

  const expectedEncoding = config.bom && config.encoding === "utf-8" ? "utf-8-sig" : config.encoding;
  if (result.encoding !== expectedEncoding) {
    issues.push(issue("warning", `Detected encoding ${JSON.stringify(result.encoding)} does not match expected ${JSON.stringify(expectedEncoding)}.`));
  }

  return issues;
}

function buildCsv(rows, config) {
  return rows
    .map((row) => row.map((value) => encodeCsvCell(value, config.delimiter, config.quoteStyle)).join(config.delimiter))
    .join(config.lineTerminator) + (rows.length ? config.lineTerminator : "");
}

function encodeCsvCell(value, delimiter, quoteStyle) {
  const mustQuote = quoteStyle === "all" || value.includes(delimiter) || /["\n\r]/.test(value);
  const escapedValue = value.replaceAll('"', '""');
  return mustQuote ? `"${escapedValue}"` : escapedValue;
}

function createDownloadBlob(correctedCsv, config) {
  if (config.encoding === "utf-16") {
    const bom = new Uint8Array([0xff, 0xfe]);
    const encoded = encodeUtf16Le(correctedCsv);
    return new Blob([bom, encoded], { type: "text/csv;charset=utf-16" });
  }

  if (config.encoding === "latin-1") {
    const bytes = new Uint8Array([...correctedCsv].map((char) => char.charCodeAt(0) & 0xff));
    return new Blob([bytes], { type: "text/csv;charset=iso-8859-1" });
  }

  const chunks = [];
  if (config.bom) {
    chunks.push(new Uint8Array([0xef, 0xbb, 0xbf]));
  }
  chunks.push(correctedCsv);
  return new Blob(chunks, { type: "text/csv;charset=utf-8" });
}

function renderAnalysis(analysis, config) {
  elements.detectedFormat.textContent = `delimiter ${JSON.stringify(analysis.delimiter)} | newline ${analysis.newlineStyle} | encoding ${analysis.detectedEncoding}`;
  elements.targetFormat.textContent = `delimiter ${JSON.stringify(config.delimiter)} | newline ${escapeNewline(config.lineTerminator)} | encoding ${config.bom ? "utf-8-sig" : config.encoding}`;
  elements.rowCount.textContent = String(analysis.rows.length);
  elements.columnCount.textContent = String(analysis.rows[0]?.length ?? 0);
  elements.issueCount.textContent = String(analysis.issues.length);
  elements.outputPreview.textContent = state.correctedCsv || "No corrected output generated.";
  elements.downloadButton.disabled = analysis.issues.some((current) => current.severity === "error");
  renderIssues(analysis.issues);
}

function renderIssues(issues) {
  elements.issuesList.innerHTML = "";
  if (!issues.length) {
    renderEmptyIssues();
    return;
  }

  for (const current of issues) {
    const item = document.createElement("li");
    const severity = document.createElement("span");
    severity.className = `severity-pill severity-${current.severity}`;
    severity.textContent = current.severity;

    const copy = document.createElement("div");
    copy.className = "issue-text";
    copy.textContent = current.message;

    item.append(severity, copy);
    elements.issuesList.append(item);
  }
}

function renderEmptyIssues() {
  elements.issuesList.innerHTML = "";
  const item = document.createElement("li");
  item.innerHTML = `<span class="severity-pill severity-info">ready</span><div class="issue-text">Load a CSV and run analysis to see validation results.</div>`;
  elements.issuesList.append(item);
}

function renderFatalIssue(message) {
  elements.detectedFormat.textContent = "Analysis failed";
  elements.targetFormat.textContent = "Fix the form settings and rerun analysis";
  elements.rowCount.textContent = "0";
  elements.columnCount.textContent = "0";
  elements.issueCount.textContent = "1";
  elements.outputPreview.textContent = "No corrected output generated.";
  elements.downloadButton.disabled = true;
  renderIssues([issue("error", message)]);
}

function escapeNewline(value) {
  return value.replace(/\r/g, "\\r").replace(/\n/g, "\\n");
}

function issue(severity, message) {
  return { severity, message };
}

function decodeCsvBytes(bytes) {
  if (bytes[0] === 0xff && bytes[1] === 0xfe) {
    return {
      encoding: "utf-16",
      text: new TextDecoder("utf-16le").decode(bytes),
    };
  }

  if (bytes[0] === 0xfe && bytes[1] === 0xff) {
    return {
      encoding: "utf-16",
      text: decodeUtf16Be(bytes.subarray(2)),
    };
  }

  if (bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    return {
      encoding: "utf-8-sig",
      text: new TextDecoder("utf-8").decode(bytes.subarray(3)),
    };
  }

  try {
    return {
      encoding: "utf-8",
      text: new TextDecoder("utf-8", { fatal: true }).decode(bytes),
    };
  } catch {
    return {
      encoding: "latin-1",
      text: new TextDecoder("iso-8859-1").decode(bytes),
    };
  }
}

function decodeUtf16Be(bytes) {
  const normalized = new Uint8Array(bytes.length);
  for (let index = 0; index < bytes.length; index += 2) {
    normalized[index] = bytes[index + 1];
    normalized[index + 1] = bytes[index];
  }
  return new TextDecoder("utf-16le").decode(normalized);
}

function encodeUtf16Le(text) {
  const buffer = new Uint8Array(text.length * 2);
  for (let index = 0; index < text.length; index += 1) {
    const codeUnit = text.charCodeAt(index);
    buffer[index * 2] = codeUnit & 0xff;
    buffer[index * 2 + 1] = codeUnit >> 8;
  }
  return buffer;
}
