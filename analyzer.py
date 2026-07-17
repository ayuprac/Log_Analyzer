import os
import re
import csv
import argparse
from collections import Counter
from datetime import datetime

LOG_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>INFO|WARNING|ERROR)\s+"
    r"(?P<message>.*)$"
)

def read_log_files(log_dir: str):
    """Return list of (filename, line_number, raw_line) from all .log files in a folder."""
    if not os.path.isdir(log_dir):
        raise FileNotFoundError(f"Log folder not found: {log_dir}")

    entries = []
    for fname in os.listdir(log_dir):
        if fname.lower().endswith(".log"):
            path = os.path.join(log_dir, fname)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, start=1):
                    line = line.strip()
                    if line:
                        entries.append((fname, i, line))
    return entries

def parse_logs(entries):
    """
    Parse raw lines using regex.
    Returns:
      parsed_records: list of dicts {file, line, timestamp, level, message}
      invalid_records: list of dicts {file, line, raw}
    """
    parsed_records = []
    invalid_records = []

    for fname, line_no, raw in entries:
        m = LOG_PATTERN.match(raw)
        if not m:
            invalid_records.append({"file": fname, "line": line_no, "raw": raw})
            continue

        dt_str = f"{m.group('date')} {m.group('time')}"
        try:
            timestamp = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            invalid_records.append({"file": fname, "line": line_no, "raw": raw})
            continue

        parsed_records.append({
            "file": fname,
            "line": line_no,
            "timestamp": timestamp,
            "level": m.group("level"),
            "message": m.group("message").strip()
        })

    return parsed_records, invalid_records

def summarize(parsed_records):
    """Compute counts and most common errors."""
    level_counts = Counter(r["level"] for r in parsed_records)

    # Only error messages for frequency analysis
    error_messages = [r["message"] for r in parsed_records if r["level"] == "ERROR"]
    top_errors = Counter(error_messages).most_common(10)

    return level_counts, top_errors

def write_csv_report(output_csv, parsed_records, invalid_records, level_counts, top_errors):
    """Write a CSV report (summary + details)."""
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Summary section
        writer.writerow(["SUMMARY"])
        writer.writerow(["Total parsed logs", len(parsed_records)])
        writer.writerow(["Total invalid logs", len(invalid_records)])
        writer.writerow(["INFO", level_counts.get("INFO", 0)])
        writer.writerow(["WARNING", level_counts.get("WARNING", 0)])
        writer.writerow(["ERROR", level_counts.get("ERROR", 0)])
        writer.writerow([])

        writer.writerow(["TOP 10 ERROR MESSAGES"])
        writer.writerow(["Error message", "Count"])
        for msg, cnt in top_errors:
            writer.writerow([msg, cnt])
        writer.writerow([])

        # Details section
        writer.writerow(["PARSED LOG DETAILS"])
        writer.writerow(["file", "line", "timestamp", "level", "message"])
        for r in sorted(parsed_records, key=lambda x: x["timestamp"]):
            writer.writerow([r["file"], r["line"], r["timestamp"].isoformat(sep=" "), r["level"], r["message"]])
        writer.writerow([])

        # Invalid lines section
        writer.writerow(["INVALID / UNPARSEABLE LINES"])
        writer.writerow(["file", "line", "raw"])
        for r in invalid_records:
            writer.writerow([r["file"], r["line"], r["raw"]])

def show_chart(level_counts):
    """Optional bar chart using matplotlib (if installed)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[!] matplotlib not installed, skipping chart. (Run: python -m pip install matplotlib)")
        return

    labels = ["INFO", "WARNING", "ERROR"]
    values = [level_counts.get("INFO", 0), level_counts.get("WARNING", 0), level_counts.get("ERROR", 0)]

    plt.figure()
    plt.bar(labels, values)
    plt.title("Log Level Counts")
    plt.xlabel("Level")
    plt.ylabel("Count")
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Simple Python Log Analyzer")
    parser.add_argument("--logdir", default="logs", help="Folder containing .log files (default: logs)")
    parser.add_argument("--out", default="report.csv", help="Output CSV filename (default: report.csv)")
    parser.add_argument("--chart", action="store_true", help="Show bar chart (requires matplotlib)")
    args = parser.parse_args()

    entries = read_log_files(args.logdir)
    if not entries:
        print(f"[!] No .log files found in '{args.logdir}'")
        return

    parsed_records, invalid_records = parse_logs(entries)
    level_counts, top_errors = summarize(parsed_records)

    # Console summary
    print("=== LOG ANALYZER SUMMARY ===")
    print(f"Log folder: {args.logdir}")
    print(f"Parsed lines: {len(parsed_records)}")
    print(f"Invalid lines: {len(invalid_records)}")
    print(f"INFO: {level_counts.get('INFO', 0)}")
    print(f"WARNING: {level_counts.get('WARNING', 0)}")
    print(f"ERROR: {level_counts.get('ERROR', 0)}")
    print()

    if top_errors:
        print("Top error messages:")
        for msg, cnt in top_errors[:5]:
            print(f"- ({cnt}x) {msg}")
    else:
        print("No ERROR messages found.")

    # Write report
    write_csv_report(args.out, parsed_records, invalid_records, level_counts, top_errors)
    print(f"\n[✓] Report saved to: {args.out}")

    # Optional chart
    if args.chart:
        show_chart(level_counts)
        #for dashboard
def analyze_folder(log_dir="logs"):
    """
    Helper function for dashboard usage.
    Returns a dict with summary data.
    """
    entries = read_log_files(log_dir)
    parsed_records, invalid_records = parse_logs(entries)
    level_counts, top_errors = summarize(parsed_records)

    return {
        "log_dir": log_dir,
        "parsed_count": len(parsed_records),
        "invalid_count": len(invalid_records),
        "level_counts": dict(level_counts),
        "top_errors": top_errors,   # list of (message, count)
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
if __name__ == "__main__":
    main()