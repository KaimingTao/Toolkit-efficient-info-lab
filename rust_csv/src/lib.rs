use std::collections::HashSet;
use std::fs;
use std::io;
use std::path::Path;

pub type CsvRow = Vec<(String, String)>;
pub type CsvTable = Vec<CsvRow>;

#[derive(Debug)]
pub enum CsvError {
    Io(io::Error),
    UnclosedQuote,
}

impl From<io::Error> for CsvError {
    fn from(error: io::Error) -> Self {
        Self::Io(error)
    }
}

pub fn load_csv<P: AsRef<Path>>(file_path: P) -> Result<CsvTable, CsvError> {
    let path = file_path.as_ref();
    let mut content = fs::read_to_string(path)?;

    if content.starts_with('\u{feff}') {
        content = content.trim_start_matches('\u{feff}').to_string();
    }

    let records = parse_csv_records(&content)?;
    if records.is_empty() {
        return Ok(Vec::new());
    }

    let headers = &records[0];
    let rows = records
        .iter()
        .skip(1)
        .map(|record| {
            headers
                .iter()
                .enumerate()
                .map(|(index, header)| {
                    let value = record.get(index).cloned().unwrap_or_default();
                    (header.clone(), value)
                })
                .collect()
        })
        .collect();

    Ok(rows)
}

pub fn dump_csv<P: AsRef<Path>>(
    file_path: P,
    table: &[CsvRow],
    header: Option<&[String]>,
) -> Result<(), CsvError> {
    let path = file_path.as_ref();

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let headers = match header {
        Some(header) => header.to_vec(),
        None => infer_header(table),
    };

    let mut output = String::new();
    output.push_str(&write_csv_record(&headers));
    output.push('\n');

    for row in table {
        let values: Vec<String> = headers
            .iter()
            .map(|header| lookup_value(row, header).unwrap_or_default())
            .collect();
        output.push_str(&write_csv_record(&values));
        output.push('\n');
    }

    fs::write(path, output)?;
    Ok(())
}

fn infer_header(table: &[CsvRow]) -> Vec<String> {
    let mut seen = HashSet::new();
    let mut headers = Vec::new();

    for row in table {
        for (key, _) in row {
            if seen.insert(key.clone()) {
                headers.push(key.clone());
            }
        }
    }

    headers
}

fn lookup_value(row: &CsvRow, header: &str) -> Option<String> {
    row.iter()
        .find(|(key, _)| key == header)
        .map(|(_, value)| value.clone())
}

fn parse_csv_records(input: &str) -> Result<Vec<Vec<String>>, CsvError> {
    let mut records = Vec::new();
    let mut record = Vec::new();
    let mut field = String::new();
    let mut chars = input.chars().peekable();
    let mut in_quotes = false;

    while let Some(ch) = chars.next() {
        match ch {
            '"' if in_quotes && chars.peek() == Some(&'"') => {
                field.push('"');
                chars.next();
            }
            '"' => {
                in_quotes = !in_quotes;
            }
            ',' if !in_quotes => {
                record.push(field);
                field = String::new();
            }
            '\n' if !in_quotes => {
                record.push(field);
                field = String::new();
                records.push(record);
                record = Vec::new();
            }
            '\r' if !in_quotes => {
                if chars.peek() == Some(&'\n') {
                    chars.next();
                }
                record.push(field);
                field = String::new();
                records.push(record);
                record = Vec::new();
            }
            _ => field.push(ch),
        }
    }

    if in_quotes {
        return Err(CsvError::UnclosedQuote);
    }

    if !field.is_empty() || !record.is_empty() {
        record.push(field);
        records.push(record);
    }

    Ok(records)
}

fn write_csv_record(values: &[String]) -> String {
    values
        .iter()
        .map(|value| write_csv_field(value))
        .collect::<Vec<_>>()
        .join(",")
}

fn write_csv_field(value: &str) -> String {
    if value.contains(',') || value.contains('"') || value.contains('\n') || value.contains('\r') {
        format!("\"{}\"", value.replace('"', "\"\""))
    } else {
        value.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_blank_values_as_strings() {
        let records = parse_csv_records("name,age,blank\nAlice,42,\nBob,,x\n").unwrap();

        assert_eq!(
            records,
            vec![
                vec!["name", "age", "blank"],
                vec!["Alice", "42", ""],
                vec!["Bob", "", "x"],
            ]
        );
    }

    #[test]
    fn writes_and_loads_csv() {
        let path = std::env::temp_dir().join("rust_csv_round_trip.csv");
        let rows = vec![vec![
            ("name".to_string(), "Alice".to_string()),
            ("age".to_string(), "42".to_string()),
            ("blank".to_string(), String::new()),
        ]];

        dump_csv(&path, &rows, None).unwrap();
        let loaded = load_csv(&path).unwrap();

        assert_eq!(loaded, rows);
    }

    #[test]
    fn quotes_fields_when_needed() {
        assert_eq!(write_csv_field("a,b"), "\"a,b\"");
        assert_eq!(write_csv_field("a\"b"), "\"a\"\"b\"");
        assert_eq!(write_csv_field("plain"), "plain");
    }
}
