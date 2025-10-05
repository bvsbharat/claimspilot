# Simple Fix: Replace Pathway with Watchdog

## Problem

Pathway 0.2.0 has limitations:
1. No `with_metadata` parameter
2. No `binary` format support (only plaintext, csv, json)
3. Can't handle PDF files properly
4. Overcomplicated for simple file watching

## Solution

Replace Pathway with Python's `watchdog` library for file monitoring.
This is simpler, works with all file types, and has no compatibility issues.

## Implementation

Add to requirements.txt:
```
watchdog==3.0.0
```

Replace `services/pathway_pipeline.py` with a simple watchdog-based file watcher.

The current Pathway approach is overengineered for this use case.
File watching is a solved problem - we don't need a complex streaming framework for it.

##Alternative: Process on Upload

Even simpler: Just process files directly in the upload endpoint!
No background watching needed - process synchronously on upload.

Would you like me to implement either:
1. Watchdog-based file watcher
2. Direct processing on upload (simplest)
