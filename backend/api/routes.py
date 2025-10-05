"""
FastAPI routes for claims triage system
"""

import os
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from services import get_mongodb_service, get_event_queue, get_rag_service, get_document_context_manager, get_gmail_service, get_pdf_generator, get_gmail_auto_fetch_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory cache with TTL
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 5  # seconds

# Data models
class ClaimUploadResponse(BaseModel):
    claim_id: str
    status: str
    message: str

class AdjusterCreate(BaseModel):
    adjuster_id: str
    name: str
    email: str
    specializations: List[str]
    experience_level: str
    years_experience: int
    max_claim_amount: float
    max_concurrent_claims: int = 15
    territories: List[str] = []

# Upload directory
UPLOAD_DIR = Path(os.getenv("DATA_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_cached(key: str) -> Optional[Any]:
    """Get cached value if not expired"""
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["timestamp"] < CACHE_TTL:
            return entry["data"]
        else:
            del _cache[key]
    return None


def set_cache(key: str, data: Any):
    """Set cached value with timestamp"""
    _cache[key] = {"data": data, "timestamp": time.time()}


@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Claims Triage System API",
        "version": "1.0.0"
    }


@router.get("/api/health")
async def health_check():
    """System health check"""
    try:
        mongodb = await get_mongodb_service()
        claims_count = len(await mongodb.get_all_claims())

        return {
            "status": "healthy",
            "mongodb": "connected",
            "claims_processed": claims_count,
            "processing_mode": "direct_upload",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/api/events/stream")
async def stream_events(request: Request):
    """Server-Sent Events endpoint for real-time updates"""
    import asyncio
    import json

    async def event_generator():
        event_queue = get_event_queue()
        logger.info("SSE client connected")

        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break

                event = await event_queue.subscribe()
                event_data = json.dumps(event)
                yield f"data: {event_data}\n\n"

        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
        except Exception as e:
            logger.error(f"SSE error: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/api/claims/upload", response_model=ClaimUploadResponse)
async def upload_claim(file: UploadFile = File(...), background_tasks=None):
    """Upload claim document and process immediately"""
    try:
        import unicodedata
        import re
        from services.claim_processor import process_claim_file

        # Sanitize filename
        normalized = unicodedata.normalize('NFKD', file.filename)
        ascii_filename = normalized.encode('ascii', 'ignore').decode('ascii')
        clean_filename = re.sub(r'[^\w\s.-]', '', ascii_filename)
        clean_filename = re.sub(r'\s+', '_', clean_filename)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{clean_filename}"
        file_path = UPLOAD_DIR / safe_filename

        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"📤 Claim uploaded: {safe_filename}")

        # Process claim immediately (in background to not block response)
        import asyncio
        asyncio.create_task(process_claim_file(str(file_path)))

        # Generate temporary claim ID for response
        claim_id = Path(safe_filename).stem

        return ClaimUploadResponse(
            claim_id=claim_id,
            status="processing",
            message="Claim uploaded - processing started"
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/claims/list")
async def list_claims(status: Optional[str] = None):
    """List all claims"""
    try:
        cache_key = f"claims_list_{status}"
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

        mongodb = await get_mongodb_service()
        claims = await mongodb.get_all_claims(status=status)

        result = {
            "claims": claims,
            "total": len(claims)
        }
        set_cache(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"List claims failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/claims/queue")
async def get_claims_queue():
    """Get claims in triage queue"""
    try:
        mongodb = await get_mongodb_service()
        queue = await mongodb.get_claims_queue()

        return {
            "queue": queue,
            "total": len(queue)
        }
    except Exception as e:
        logger.error(f"Get queue failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/claims/{claim_id}")
async def get_claim(claim_id: str):
    """Get claim details"""
    try:
        mongodb = await get_mongodb_service()
        claim = await mongodb.get_claim(claim_id)

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        return claim
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get claim failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/adjusters/list")
async def list_adjusters(available_only: bool = False):
    """List all adjusters"""
    try:
        cache_key = f"adjusters_list_{available_only}"
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

        mongodb = await get_mongodb_service()
        adjusters = await mongodb.get_all_adjusters(available_only=available_only)

        result = {
            "adjusters": adjusters,
            "total": len(adjusters)
        }
        set_cache(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"List adjusters failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/adjusters/create")
async def create_adjuster(adjuster: AdjusterCreate):
    """Create new adjuster"""
    try:
        mongodb = await get_mongodb_service()

        adjuster_data = adjuster.dict()
        adjuster_data["available"] = True
        adjuster_data["current_workload"] = 0

        success = await mongodb.save_adjuster(adjuster_data)

        if success:
            return {"message": "Adjuster created successfully", "adjuster_id": adjuster.adjuster_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to create adjuster")

    except Exception as e:
        logger.error(f"Create adjuster failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/adjusters/{adjuster_id}/workload")
async def get_adjuster_workload(adjuster_id: str):
    """Get adjuster's current workload"""
    try:
        mongodb = await get_mongodb_service()

        adjuster = await mongodb.get_adjuster(adjuster_id)
        if not adjuster:
            raise HTTPException(status_code=404, detail="Adjuster not found")

        # Get active claims
        all_claims = await mongodb.get_all_claims(status="assigned")
        adjuster_claims = [c for c in all_claims if c.get("routing_decision", {}).get("adjuster_id") == adjuster_id]

        return {
            "adjuster_id": adjuster_id,
            "adjuster_name": adjuster.get("name"),
            "current_claims": len(adjuster_claims),
            "max_claims": adjuster.get("max_concurrent_claims", 15),
            "capacity_percentage": (len(adjuster_claims) / adjuster.get("max_concurrent_claims", 15)) * 100,
            "active_claims": [c.get("claim_id") for c in adjuster_claims]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/fraud-flags")
async def get_fraud_flags():
    """Get all fraud flags"""
    try:
        cache_key = "fraud_flags"
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

        mongodb = await get_mongodb_service()
        claims_with_flags = await mongodb.get_fraud_flags()

        result = {
            "fraud_flags": claims_with_flags,
            "total": len(claims_with_flags)
        }
        set_cache(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Get fraud flags failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/metrics")
async def get_metrics():
    """Get processing metrics"""
    try:
        cache_key = "metrics"
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

        mongodb = await get_mongodb_service()
        metrics = await mongodb.get_processing_metrics()

        set_cache(cache_key, metrics)
        return metrics
    except Exception as e:
        logger.error(f"Get metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/processing/status")
async def get_processing_status():
    """Get claim processing system status"""
    try:
        import os

        uploads_dir = str(UPLOAD_DIR)
        abs_uploads_dir = os.path.abspath(uploads_dir)

        # Count files in uploads directory
        files_in_dir = []
        if os.path.exists(abs_uploads_dir):
            files_in_dir = [f for f in os.listdir(abs_uploads_dir)
                           if not f.startswith('.') and os.path.isfile(os.path.join(abs_uploads_dir, f))]

        mongodb = await get_mongodb_service()
        all_claims = await mongodb.get_all_claims()

        return {
            "processing_mode": "direct_upload",
            "pathway_disabled": True,
            "uploads_dir": uploads_dir,
            "abs_uploads_dir": abs_uploads_dir,
            "dir_exists": os.path.exists(abs_uploads_dir),
            "files_in_uploads": len(files_in_dir),
            "claims_in_db": len(all_claims),
            "file_list": files_in_dir[:10],  # Show first 10 files
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Get processing status failed: {e}", exc_info=True)
        return {
            "processing_mode": "direct_upload",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


class ClaimStatusUpdate(BaseModel):
    status: str

@router.patch("/api/claims/{claim_id}/status")
async def update_claim_status(claim_id: str, update: ClaimStatusUpdate):
    """Update claim status with task tracking"""
    try:
        mongodb = await get_mongodb_service()
        claim = await mongodb.get_claim(claim_id)

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        old_status = claim.get("status")
        new_status = update.status

        # Update status
        success = await mongodb.update_claim_status(claim_id, new_status)

        if success:
            # Decrement adjuster workload when claim is completed or closed
            if new_status in ["completed", "closed", "approved"]:
                routing_decision = claim.get("routing_decision", {})
                adjuster_id = routing_decision.get("adjuster_id")
                if adjuster_id and adjuster_id != "AUTO_SYSTEM":
                    await mongodb.update_adjuster_workload(adjuster_id, -1)
                    logger.info(f"Decremented workload for adjuster {adjuster_id} (claim {claim_id} completed)")

            # Handle status-specific actions
            if new_status == "review" and old_status == "in_progress":
                # Create review check ID
                import uuid
                review_check_id = f"CHECK-{str(uuid.uuid4())[:8].upper()}"
                await mongodb.update_claim_field(claim_id, "review_check_id", review_check_id)
                logger.info(f"🔍 Created review check {review_check_id} for claim {claim_id}")

                # Publish event
                event_queue = get_event_queue()
                await event_queue.publish({
                    "type": "claim_moved_to_review",
                    "message": f"Claim {claim_id} moved to review - Check ID: {review_check_id}",
                    "claim_id": claim_id,
                    "status": new_status,
                    "review_check_id": review_check_id
                })
            elif new_status == "completed" and old_status in ["review", "pending_review"]:
                # Publish completion event
                event_queue = get_event_queue()
                await event_queue.publish({
                    "type": "claim_completed",
                    "message": f"✅ Claim {claim_id} completed and closed",
                    "claim_id": claim_id,
                    "status": new_status
                })
            else:
                # General status update event
                event_queue = get_event_queue()
                await event_queue.publish({
                    "type": "claim_status_updated",
                    "message": f"Claim {claim_id} status updated to {new_status}",
                    "claim_id": claim_id,
                    "status": new_status
                })

            return {"message": "Status updated successfully", "claim_id": claim_id, "status": new_status}
        else:
            raise HTTPException(status_code=500, detail="Failed to update status")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/claims/{claim_id}")
async def delete_claim(claim_id: str):
    """Delete a claim"""
    try:
        mongodb = await get_mongodb_service()
        claim = await mongodb.get_claim(claim_id)

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Update adjuster workload if claim was assigned
        routing_decision = claim.get("routing_decision", {})
        adjuster_id = routing_decision.get("adjuster_id")
        if adjuster_id:
            await mongodb.update_adjuster_workload(adjuster_id, -1)
            logger.info(f"Updated workload for adjuster {adjuster_id} (decreased by 1)")

        # Delete the claim
        success = await mongodb.delete_claim(claim_id)

        if success:
            # Publish deletion event
            event_queue = get_event_queue()
            await event_queue.publish({
                "type": "claim_deleted",
                "message": f"🗑️ Claim {claim_id} deleted",
                "claim_id": claim_id
            })

            logger.info(f"✅ Claim {claim_id} deleted successfully")
            return {"message": "Claim deleted successfully", "claim_id": claim_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete claim")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete claim failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== CHAT / RAG ENDPOINTS ==========

class ChatQuery(BaseModel):
    query: str
    claim_id: Optional[str] = None


@router.post("/api/chat/query")
async def query_rag(chat_query: ChatQuery):
    """Query the RAG system with a question (uses Pathway RAG if available)"""
    try:
        # Try Pathway RAG server first (vector-based)
        from services.pathway_rag_server import get_pathway_rag_server, PATHWAY_LLM_AVAILABLE

        if PATHWAY_LLM_AVAILABLE:
            rag_server = get_pathway_rag_server()
            if rag_server and rag_server.running:
                try:
                    import requests

                    # Query Pathway RAG server
                    response = requests.post(
                        "http://127.0.0.1:8765/v2/answer",
                        json={"prompt": chat_query.query},
                        timeout=30
                    )

                    if response.status_code == 200:
                        pathway_result = response.json()

                        # Format response to match our API
                        return {
                            "answer": pathway_result.get("response", pathway_result.get("answer", "")),
                            "sources": pathway_result.get("sources", []),
                            "context": pathway_result.get("context", []),
                            "model": "gpt-4o (via Pathway RAG)",
                            "engine": "pathway_vector_rag"
                        }
                except Exception as e:
                    logger.warning(f"Pathway RAG query failed, falling back to basic RAG: {e}")

        # Fallback to basic RAG service
        rag_service = get_rag_service()
        result = await rag_service.query(
            question=chat_query.query,
            claim_id=chat_query.claim_id
        )
        result["engine"] = "fallback_text_rag"

        return result

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chat/context/{claim_id}")
async def get_claim_context(claim_id: str):
    """Get all context for a specific claim"""
    try:
        # Get claim from MongoDB
        mongodb = await get_mongodb_service()
        claim = await mongodb.get_claim(claim_id)

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Get document context
        context_mgr = get_document_context_manager()
        doc_context = context_mgr.get_context(claim_id)

        # Get RAG context
        rag_service = get_rag_service()
        rag_context = await rag_service.get_claim_context(claim_id)

        return {
            "claim": claim,
            "document_context": doc_context,
            "rag_context": rag_context
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get claim context failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chat/processed-data/{claim_id}")
async def get_processed_data(claim_id: str):
    """Get LandingAI extracted/processed data for a claim"""
    try:
        context_mgr = get_document_context_manager()
        context = context_mgr.get_context(claim_id)

        if not context:
            raise HTTPException(status_code=404, detail="No processed data found for this claim")

        return {
            "claim_id": claim_id,
            "raw_text": context.get("raw_text", ""),
            "structured_data": context.get("structured_data", {}),
            "tables": context.get("tables", []),
            "document_type": context.get("document_type", "unknown"),
            "char_count": context.get("char_count", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get processed data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chat/stats")
async def get_rag_stats():
    """Get RAG service statistics"""
    try:
        rag_service = get_rag_service()
        context_mgr = get_document_context_manager()

        return {
            "rag_service": rag_service.get_stats(),
            "document_context": context_mgr.get_stats()
        }
    except Exception as e:
        logger.error(f"Get RAG stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== GMAIL INTEGRATION ENDPOINTS ==========

@router.get("/api/gmail/status")
async def get_gmail_status():
    """Check if Gmail is connected (using credentials.json and token.json)"""
    try:
        gmail_service = get_gmail_service()

        if gmail_service.is_connected():
            user_email = gmail_service.get_user_email()
            return {
                "connected": True,
                "user_email": user_email,
                "message": "Gmail connected via credentials.json"
            }
        else:
            return {
                "connected": False,
                "message": "Gmail not connected. Check credentials.json and token.json files."
            }
    except Exception as e:
        logger.error(f"Failed to get Gmail status: {e}")
        return {
            "connected": False,
            "error": str(e)
        }


@router.post("/api/gmail/fetch")
async def fetch_gmail_claims(max_results: int = 10, days_back: int = 7):
    """Fetch claim-related emails from Gmail and process them"""
    try:
        gmail_service = get_gmail_service()

        if not gmail_service.is_connected():
            raise HTTPException(status_code=401, detail="Gmail not connected. Check credentials.json and token.json files.")

        # Fetch claim emails
        emails = gmail_service.fetch_claim_emails(
            max_results=max_results,
            days_back=days_back
        )

        if not emails:
            return {
                "message": "No claim-related emails found",
                "emails_found": 0,
                "emails_processed": 0
            }

        # Process emails into PDFs
        pdf_generator = get_pdf_generator()
        processed_count = 0
        claim_ids = []

        for email in emails:
            try:
                # Generate PDF from email
                pdf_path = pdf_generator.generate_from_gmail_message(
                    message_id=email['id'],
                    subject=email['subject'],
                    sender=email['from'],
                    date=email['date'],
                    body=email['body_html'] or email['body_text'] or email['snippet'],
                    attachments=email['attachments'],
                    output_dir=UPLOAD_DIR
                )

                if pdf_path:
                    processed_count += 1
                    claim_id = pdf_path.stem
                    claim_ids.append(claim_id)

                    # Mark email as read and add label
                    gmail_service.mark_as_read(email['id'])
                    gmail_service.add_label(email['id'], 'CLAIM_PROCESSED')

                    logger.info(f"✅ Processed email to claim: {claim_id}")

            except Exception as e:
                logger.error(f"Failed to process email {email['id']}: {e}")
                continue

        # Publish event
        event_queue = get_event_queue()
        await event_queue.publish({
            "type": "gmail_fetch_completed",
            "message": f"📧 Fetched {len(emails)} emails, processed {processed_count} claims",
            "emails_found": len(emails),
            "emails_processed": processed_count
        })

        return {
            "message": f"Successfully processed {processed_count} of {len(emails)} emails",
            "emails_found": len(emails),
            "emails_processed": processed_count,
            "claim_ids": claim_ids,
            "emails": [
                {
                    "id": e['id'],
                    "subject": e['subject'],
                    "from": e['from'],
                    "date": e['date'],
                    "has_attachments": e['has_attachments']
                }
                for e in emails
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gmail/preview")
async def preview_gmail_claims(max_results: int = 10, days_back: int = 7):
    """Preview claim-related emails without processing"""
    try:
        gmail_service = get_gmail_service()

        if not gmail_service.is_connected():
            raise HTTPException(status_code=401, detail="Gmail not connected. Check credentials.json and token.json files.")

        # Fetch claim emails
        emails = gmail_service.fetch_claim_emails(
            max_results=max_results,
            days_back=days_back
        )

        # Return preview data
        return {
            "emails": [
                {
                    "id": e['id'],
                    "subject": e['subject'],
                    "from": e['from'],
                    "date": e['date'],
                    "snippet": e['snippet'],
                    "has_attachments": e['has_attachments'],
                    "attachment_count": len(e['attachments'])
                }
                for e in emails
            ],
            "total": len(emails)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== GMAIL AUTO-FETCH ENDPOINTS ==========

@router.get("/api/gmail/auto-fetch/status")
async def get_auto_fetch_status():
    """Get Gmail auto-fetch service status"""
    try:
        auto_fetch_service = get_gmail_auto_fetch_service()
        status = auto_fetch_service.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get auto-fetch status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AutoFetchToggle(BaseModel):
    enabled: bool


@router.post("/api/gmail/auto-fetch/toggle")
async def toggle_auto_fetch(toggle: AutoFetchToggle):
    """Enable or disable Gmail auto-fetch"""
    try:
        auto_fetch_service = get_gmail_auto_fetch_service()

        if toggle.enabled:
            if not auto_fetch_service.running:
                await auto_fetch_service.start()
                return {
                    "message": "Auto-fetch enabled",
                    "status": auto_fetch_service.get_status()
                }
            else:
                return {
                    "message": "Auto-fetch already running",
                    "status": auto_fetch_service.get_status()
                }
        else:
            if auto_fetch_service.running:
                await auto_fetch_service.stop()
                return {
                    "message": "Auto-fetch disabled",
                    "status": auto_fetch_service.get_status()
                }
            else:
                return {
                    "message": "Auto-fetch already stopped",
                    "status": auto_fetch_service.get_status()
                }
    except Exception as e:
        logger.error(f"Failed to toggle auto-fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gmail/auto-fetch/fetch-now")
async def trigger_fetch_now():
    """Manually trigger an immediate fetch (bypasses interval)"""
    try:
        auto_fetch_service = get_gmail_auto_fetch_service()
        result = await auto_fetch_service.fetch_now()

        if result.get("success"):
            return {
                "message": f"Fetched {result['emails_processed']} of {result['emails_found']} emails",
                **result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Fetch failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


