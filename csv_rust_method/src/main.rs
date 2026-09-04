//! CSV Rust workflow entry.
//!
//! Purpose: demonstrate CSV loading and dumping with the Rust library.
//! Usage: run `cargo run`; see `main.md` for details.
//! Substeps: create rows, write CSV data, reload it, and verify the result.

use rust_csv::{dump_csv, load_csv};

fn main() {
    let path = std::env::temp_dir().join("rust_csv_main_test.csv");
    let rows = vec![
        vec![
            ("name".to_string(), "Alice".to_string()),
            ("age".to_string(), "42".to_string()),
            ("blank".to_string(), String::new()),
        ],
        vec![
            ("name".to_string(), "Bob".to_string()),
            ("age".to_string(), String::new()),
            ("blank".to_string(), "x".to_string()),
        ],
    ];

    dump_csv(&path, &rows, None).expect("dump_csv failed");

    let loaded = load_csv(&path).expect("load_csv failed");
    println!("{loaded:?}");

    assert_eq!(loaded, rows);
}
