# Aparavi Gmail Fetcher 

⚠️ **IMPORTANT**: Getting Error for now use upload button to upload the files 
## Overview

This module provides placeholder endpoints that simulate fetching Gmail data through Aparavi's Data Toolchain for AI pipeline. All responses are simulated for demonstration purposes.

## Pipeline Configuration

The pipeline configuration (`aparavi-project-export-new-project-2025-10-04T17-32.json`) includes:

1. **Gmail Source** (`gmail_1`) - Fetches emails from Gmail
2. **Parser** (`parse_1`) - Parses email content and attachments
3. **Response** (`response_1`) - Returns processed data

## Endpoints

### 1. Fetch Gmail via Aparavi Pipeline
```bash
POST /aparavi/gmail/fetch
```

Simulates fetching Gmail data through the Aparavi pipeline.

**Request Body:**
```json
{
  "email_filters": {
    "from": "sender@example.com",
    "subject": "claim",
    "after": "2024-01-01",
    "before": "2024-12-31"
  },
  "max_results": 10
}
```

### 2. Validate Pipeline
```bash
POST /aparavi/pipeline/validate
```

Validates the pipeline configuration.

### 3. Execute Pipeline
```bash
POST /aparavi/pipeline/execute
```

Starts pipeline execution and returns a task token.

**Request Body:**
```json
{
  "pipeline_config": "path/to/config.json",
  "input_params": {}
}
```

### 4. Get Pipeline Status
```bash
GET /aparavi/pipeline/status/<token>
```

Retrieves the status of a running pipeline.

### 5. Teardown Pipeline
```bash
DELETE /aparavi/pipeline/teardown/<token>
```

Cleans up pipeline resources.

### 6. Health Check
```bash
GET /aparavi/health
```

Returns service health status.

## Running the Service

```bash
cd backend/aparavi-mail-fetcher
python aparavi_gmail_endpoint.py
```

The service will start on `http://localhost:5001`

## Testing with cURL

See `curl_examples.sh` for complete cURL command examples.

## Integration Notes

To integrate with actual Aparavi services:

1. Install the Aparavi Python SDK:
   ```bash
   pip install aparavi-dtc-sdk
   ```

2. Set up environment variables:
   ```bash
   APARAVI_API_KEY=your-api-key
   APARAVI_BASE_URL=https://eaas-dev.aparavi.com
   ```

3. Replace dummy implementations with actual SDK calls:
   ```python
   from aparavi_dtc_sdk import AparaviClient
   
   client = AparaviClient(
       base_url=os.getenv("APARAVI_BASE_URL"),
       api_key=os.getenv("APARAVI_API_KEY")
   )
   
   result = client.execute_pipeline_workflow(
       pipeline="./pipeline_config.json",
       file_glob="./*.eml"
   )
   ```

## References

- [Aparavi Python SDK Quickstart](https://aparavi.com/documentation-aparavi/data-toolchain-for-ai-documentation/python-sdk/python-sdk-quickstart/)
- [Aparavi Documentation](https://aparavi.com/documentation-aparavi/)
