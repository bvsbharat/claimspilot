# Pathway Pipeline Fixes - Summary

## Issues Fixed

### 1. **File Path Handling**
**Problem:** Complex file path extraction logic was failing to properly parse metadata paths, causing files to not be detected.

**Fix:**
- Simplified path extraction: `file_path = str(metadata.get("path", ""))`
- Separated full filename from stem for proper deduplication
- Added explicit logging of detected files

### 2. **Filename Deduplication Logic**
**Problem:** Line 104 was overwriting `source_filename` with stem, losing extension and breaking MongoDB lookups.

**Fix:**
- Created separate variables: `full_filename` (with extension) and `source_filename_stem` (without)
- Used stem consistently for MongoDB deduplication
- Kept full filename for logging and display

### 3. **Pathway Initialization**
**Problem:** Missing absolute path conversion and no confirmation of directory watching.

**Fix:**
- Added `nest_asyncio.apply()` for proper event loop nesting
- Convert to absolute path before passing to Pathway
- Added directory existence check and creation
- Enhanced logging to confirm Pathway is watching

### 4. **pw.run() Configuration**
**Problem:** Default monitoring could cause overhead and no error handling for the blocking call.

**Fix:**
- Added `pw.run(monitoring_level=pw.MonitoringLevel.NONE)` for production
- Wrapped in try/except for KeyboardInterrupt and errors
- Added clear logging about continuous operation

### 5. **Missing Activity Logging**
**Problem:** No logs showing when Pathway detects files or processes them.

**Fix:**
- Added "🔔 Pathway detected new file" log at start of process_file
- Added "✅ Pathway processed file - result" in on_result callback
- Added file removal logging for deletions
- Enhanced startup logging showing absolute path being watched

## Key Changes Made

### services/pathway_pipeline.py
```python
# Before
file_path_obj = metadata["path"]
file_path = file_path_obj.value if hasattr(file_path_obj, 'value') else str(file_path_obj)
source_filename = Path(file_path).name
source_filename = Path(file_path).stem  # OVERWRITES!

# After
file_path = str(metadata.get("path", ""))
full_filename = Path(file_path).name
source_filename_stem = Path(file_path).stem  # Separate variable
```

```python
# Before
files = pw.io.fs.read(
    path=self.data_dir,
    format="binary",
    mode="streaming",
    with_metadata=True,
)
pw.run()  # No monitoring config

# After
abs_data_dir = os.path.abspath(self.data_dir)
files = pw.io.fs.read(
    path=abs_data_dir,  # Absolute path
    format="binary",
    mode="streaming",
    with_metadata=True,
)
pw.run(monitoring_level=pw.MonitoringLevel.NONE)  # Production config
```

### api/routes.py
Added new endpoints:
- Enhanced `/api/health` with Pathway status
- New `/api/pathway/status` for detailed diagnostics

## Testing Instructions

### 1. Check Pathway Status
```bash
curl http://localhost:8080/api/pathway/status | python3 -m json.tool
```

Expected output:
```json
{
  "running": true,
  "thread_alive": true,
  "data_dir": "./uploads",
  "abs_data_dir": "/full/path/to/uploads",
  "dir_exists": true,
  "files_in_dir": 3,
  "file_list": ["file1.pdf", "file2.pdf"],
  "timestamp": "2025-10-04T18:30:00"
}
```

### 2. Upload Test Document
```bash
# Via API
curl -X POST http://localhost:8080/api/claims/upload \
  -F "file=@demo_data/sample_claim.pdf"

# Or direct copy (triggers Pathway)
cp demo_data/sample_claim.pdf backend/uploads/
```

### 3. Monitor Logs
Watch backend console for:
- `🔔 Pathway detected new file: filename.pdf`
- `📂 Full path: /path/to/file.pdf`
- `📄 Processing new file: filename (stem: filename)`
- `✅ Pathway processed file - result: {...}`

### 4. Verify Claims Created
```bash
curl http://localhost:8080/api/claims/list | python3 -m json.tool
```

## What to Watch For

### Signs Pathway is Working:
1. Backend logs show: `✅ Pathway file watcher created successfully`
2. Backend logs show: `▶️  Starting Pathway run (will run continuously)...`
3. Backend logs show: `🎯 Watching for new files in: /absolute/path`
4. `/api/pathway/status` shows `running: true` and `thread_alive: true`
5. When file uploaded: `🔔 Pathway detected new file` appears

### Signs of Problems:
1. `pathway_thread_alive: false` in health check
2. No `🔔 Pathway detected new file` log after upload
3. `files_in_dir` count doesn't match actual files
4. Errors in backend logs about "Pathway pipeline error"

## Root Cause Analysis

The main issue was **Pathway file watching was working, but the process_file function was failing silently** due to:

1. **Path extraction errors** - Complex logic failed to parse metadata properly
2. **Variable overwriting** - Deduplication check used wrong filename
3. **No error visibility** - Missing logs made debugging impossible
4. **Thread isolation** - Pathway runs in background thread, errors not bubbling up

## Additional Improvements

1. **nest_asyncio** integration for proper async/await in Pathway thread
2. **Absolute paths** to avoid working directory issues
3. **Enhanced error handling** with exc_info=True for full stack traces
4. **Diagnostics endpoint** for real-time monitoring
5. **Consistent logging** showing file detection → processing → completion flow

## MongoDB Connection Note

Backend is successfully connecting to MongoDB Atlas (confirmed by `/api/health` showing `claims_processed: 0`), so database connectivity is not an issue.

## Next Steps if Issues Persist

1. **Restart backend** to apply all fixes
2. **Clear uploads/** directory and test with one fresh file
3. **Check backend logs** for "Pathway pipeline error" messages
4. **Verify LandingAI API key** is valid with credits
5. **Test manually** by copying file to uploads/ and watching logs

## Files Modified

- ✅ `backend/services/pathway_pipeline.py` - Core fixes
- ✅ `backend/api/routes.py` - Diagnostics endpoints
