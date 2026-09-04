# CSV Validator Web

## What it does

`index.html` is a static browser application that reads a CSV selected from the
local machine, detects delimiter, encoding, and line-break details, validates
compatibility risks, and prepares a corrected CSV for download. Processing
remains in the browser.

## How to use it

Open the entry page in a browser:

```sh
open csv_validator_web/index.html
```

Choose a CSV file, select the desired delimiter, line terminator, encoding,
quote style, and BOM setting, then review the report or download the corrected
file.

## Main substeps

1. Read the selected local CSV file with browser file APIs.
2. Detect and validate its structure and compatibility risks.
3. Apply the selected output settings and offer corrected CSV data for download.

## Dependencies

This static workflow uses only standard browser APIs. It has no runtime package
dependencies.
