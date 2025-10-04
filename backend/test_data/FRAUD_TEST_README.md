# Fraud Detection Test Data

## Overview

This directory contains test claim PDFs designed to trigger various fraud detection flags in the Claims Triage System.

## Generated Test Files

All test PDFs are located in: `test_data/fraud_samples/`

### Test Cases

| File | Fraud Indicators | Expected Flags |
|------|-----------------|----------------|
| **fraud_test_1_late_reporting.pdf** | Reported 45 days after incident | `late_reporting` (high severity) |
| **fraud_test_2_inconsistent_story.pdf** | Contradicting statements: "stopped"/"moving", "no injuries" but later reports injuries, "clear visibility"/"couldn't see" | `inconsistent_story` |
| **fraud_test_3_suspicious_patterns.pdf** | Contains: "pre-existing", "previous accident", "similar claim", "witness unavailable" | `suspicious_pattern` (multiple) |
| **fraud_test_4_soft_tissue_only.pdf** | 4 injuries, all soft tissue (whiplash, strain, sprain) | `soft_tissue_only` |
| **fraud_test_5_excessive_injuries.pdf** | 6 injuries reported (threshold: >5) | `excessive_injuries` |
| **fraud_test_6_combined_fraud.pdf** | **ALL OF THE ABOVE** - Multiple fraud indicators | **9+ fraud flags** ✅ |

## How to Test

### Option 1: Copy Individual Files

```bash
# Test a specific fraud type
cp test_data/fraud_samples/fraud_test_1_late_reporting.pdf uploads/
```

### Option 2: Copy All Test Files

```bash
# Test all fraud detection patterns at once
cp test_data/fraud_samples/*.pdf uploads/
```

### Option 3: Re-generate Test Data

```bash
# If you need to regenerate the test PDFs
cd backend
source venv/bin/activate
python scripts/generate_fraud_test_data.py
```

## Fraud Detection Logic

The system checks for these patterns (from `services/fraud_detector.py`):

### 1. Late Reporting
- **Threshold**: >14 days between incident and report date
- **Severity**:
  - Medium: 14-30 days
  - High: >30 days
- **Confidence**: Increases with delay (0.3 - 0.95)

### 2. Inconsistent Story
- **Patterns**: Contradicting statements in description vs document
- **Examples**:
  - "stopped" vs "moving"
  - "no injuries" vs "injury"
  - "clear visibility" vs "couldn't see"
  - "sober" vs "drinking"
- **Confidence**: 0.6

### 3. Suspicious Patterns
- **Keywords**:
  - "pre-existing"
  - "previous accident"
  - "similar claim"
  - "multiple injuries"
  - "witness unavailable"
- **Confidence**: 0.5

### 4. Soft Tissue Only
- **Trigger**: All injuries are soft tissue (whiplash, strain, sprain)
- **Confidence**: 0.4
- **Reasoning**: Difficult to verify medically

### 5. Excessive Injuries
- **Threshold**: >5 injuries reported
- **Confidence**: 0.5
- **Reasoning**: Unusually high for typical claims

## Viewing Fraud Alerts

After uploading test files, check:

1. **Dashboard** - Fraud Alerts panel shows claims with flags
2. **API Endpoint** - `GET /api/analytics/fraud-flags`
3. **Claim Details** - View individual claim to see specific fraud flags

## Test Results

### Example: Combined Fraud Test

```
✅ Successfully detected 9 fraud flags for CLM-20251003-154208-LFMU

Flags detected:
- late_reporting (high severity)
- suspicious_pattern (multiple matches)
- soft_tissue_only
- excessive_injuries
- inconsistent_story (multiple contradictions)
```

## Customization

To create custom fraud test cases:

1. Edit `scripts/generate_fraud_test_data.py`
2. Add new test case functions
3. Run the script to regenerate PDFs

## Notes

- Test PDFs use ReportLab to generate properly formatted claim documents
- LandingAI DPT-2 extracts the text from PDFs
- OpenAI GPT-4o parses extracted text into structured claim data
- Fraud detector analyzes structured data + raw text
- All fraud flags are logged and stored in MongoDB

## Cleanup

To remove test claims from the system:

```bash
# Remove test PDFs from uploads
rm uploads/fraud_test_*.pdf

# Clear database (use with caution!)
python scripts/clear_mongodb.py
```
