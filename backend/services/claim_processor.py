"""
Direct claim processing service (without Pathway)
Processes claim files immediately upon upload
"""

import os
import logging
import time
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import random
import string

logger = logging.getLogger(__name__)


async def process_claim_file(file_path: str) -> Dict[str, Any]:
    """
    Process a single claim file through the entire pipeline

    Args:
        file_path: Absolute path to the uploaded file

    Returns:
        Dict with claim_id and processing result
    """
    try:
        start_time = time.time()

        # Import services
        from .event_queue import get_event_queue
        from .mongodb_service import get_mongodb_service
        from .document_processor import get_document_processor
        from .claim_scorer import get_claim_scorer
        from .fraud_detector import get_fraud_detector
        from .router_engine import get_router_engine
        from .rag_service import get_rag_service
        from .document_context import get_document_context_manager
        from .auto_processor import get_auto_processor
        from .task_manager import create_claim_task
        from .auto_transition import get_auto_transition_service

        # Get services
        event_queue = get_event_queue()
        mongodb = await get_mongodb_service()
        doc_processor = get_document_processor()
        scorer = get_claim_scorer()
        fraud_detector = get_fraud_detector()
        router = get_router_engine()
        rag_service = get_rag_service()
        context_mgr = get_document_context_manager()
        auto_processor = get_auto_processor()

        # Extract filename
        full_filename = Path(file_path).name
        source_filename_stem = Path(file_path).stem

        # Skip system files
        IGNORED_FILES = {'.DS_Store', '.gitkeep', 'Thumbs.db', '.gitignore', '.keep'}
        if full_filename in IGNORED_FILES or full_filename.startswith('.'):
            logger.info(f"⏭️  Skipping system file: {full_filename}")
            return {"status": "skipped", "reason": "system_file"}

        logger.info(f"📄 Processing claim file: {full_filename}")

        # Check if already processed
        existing_claim = await mongodb.get_claim_by_filename(source_filename_stem)
        if existing_claim:
            existing_claim_id = existing_claim.get("claim_id")
            current_status = existing_claim.get("status")
            if current_status in ["assigned", "in_progress", "review", "completed", "approved", "closed", "auto_approved"]:
                logger.info(f"⏭️  Skipping {full_filename} - already exists as {existing_claim_id} with status: {current_status}")
                return {"status": "skipped", "reason": f"already_{current_status}", "claim_id": existing_claim_id}

        # Generate claim ID
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        claim_id = f"CLM-{timestamp}-{random_suffix}"

        logger.info(f"✅ Generated claim ID: {claim_id}")

        # Detect source
        is_gmail_source = "_gmail_" in full_filename.lower()
        source = "gmail" if is_gmail_source else "upload"
        source_metadata = {}
        if is_gmail_source:
            source_metadata = {
                "source_type": "gmail_auto_fetch",
                "filename": full_filename
            }

        # Publish upload event
        await event_queue.publish({
            "type": "claim_uploaded",
            "message": f"📤 New claim uploaded: {claim_id}",
            "claim_id": claim_id,
            "status": "uploaded"
        })

        # Save initial claim
        initial_claim = {
            "claim_id": claim_id,
            "source_filename": source_filename_stem,
            "source": source,
            "source_metadata": source_metadata,
            "status": "extracting",
            "document_types": [],
            "file_paths": [file_path],
            "created_at": datetime.now()
        }
        await mongodb.save_claim(initial_claim)
        logger.info(f"💾 Saved initial claim to MongoDB")

        # Publish extraction event
        await event_queue.publish({
            "type": "claim_status_update",
            "message": f"📄 Extracting document data: {claim_id}",
            "claim_id": claim_id,
            "status": "extracting",
            "stage": "extraction"
        })

        # Extract document
        logger.info(f"🔍 Extracting document with LandingAI...")
        extracted = await doc_processor.extract_document_data(file_path)
        document_text = extracted.get("text", "")

        if not document_text:
            logger.error(f"❌ No text extracted from {full_filename}")
            await mongodb.update_claim_status(claim_id, "error")
            return {"status": "error", "error": "No text extracted", "claim_id": claim_id}

        logger.info(f"✅ Extracted {len(document_text)} characters")

        # Parse claim data
        logger.info(f"🧠 Parsing claim data with GPT-4o...")
        claim_data = await _parse_claim_data(document_text, extracted)

        # Add to fallback RAG service (in-memory cache)
        # Note: Pathway RAG will also automatically index this file since it's in uploads/
        try:
            rag_service.add_document(
                claim_id=claim_id,
                document_text=document_text,
                metadata={
                    "claim_id": claim_id,
                    "document_type": extracted.get("document_type", "unknown"),
                    "file_path": file_path,
                    "processed_at": datetime.now().isoformat()
                }
            )
            logger.info(f"✅ Added to fallback RAG service")
            logger.info(f"📁 File saved in {file_path} - Pathway RAG will auto-index")
        except Exception as e:
            logger.warning(f"Failed to add to fallback RAG: {e}")

        # Add to document context
        try:
            context_mgr.add_context(
                claim_id=claim_id,
                raw_text=document_text,
                structured_data=claim_data,
                document_type=extracted.get("document_type", "unknown"),
                file_path=file_path,
                tables=extracted.get("tables", [])
            )
            logger.info(f"✅ Added to document context")
        except Exception as e:
            logger.warning(f"Failed to add to context: {e}")

        # Update with extracted data
        await mongodb.save_claim({
            "claim_id": claim_id,
            "source_filename": source_filename_stem,
            "status": "scoring",
            "extracted_data": claim_data,
            "extracted_text": document_text,
            "file_paths": [file_path]
        })

        # Publish scoring event
        await event_queue.publish({
            "type": "claim_status_update",
            "message": f"📊 Analyzing claim severity and complexity: {claim_id}",
            "claim_id": claim_id,
            "status": "scoring",
            "stage": "scoring"
        })

        # Score claim
        logger.info(f"📊 Scoring claim...")
        scores = await scorer.score_claim(claim_data)
        logger.info(f"✅ Scores - Severity: {scores['severity_score']:.1f}, Complexity: {scores['complexity_score']:.1f}")

        # Publish fraud detection event
        await event_queue.publish({
            "type": "claim_status_update",
            "message": f"🔍 Running fraud detection: {claim_id}",
            "claim_id": claim_id,
            "status": "scoring",
            "stage": "fraud_detection"
        })

        # Detect fraud
        logger.info(f"🔍 Detecting fraud patterns...")
        fraud_flags = await fraud_detector.detect_fraud_flags(claim_data, document_text)

        if fraud_flags:
            logger.warning(f"⚠️  {len(fraud_flags)} fraud flag(s) detected")

        # Update with scores
        await mongodb.save_claim({
            "claim_id": claim_id,
            "source_filename": source_filename_stem,
            "status": "routing",
            "extracted_data": claim_data,
            "severity_score": scores["severity_score"],
            "complexity_score": scores["complexity_score"],
            "fraud_flags": fraud_flags,
            "file_paths": [file_path]
        })

        # Publish routing event
        await event_queue.publish({
            "type": "claim_status_update",
            "message": f"🎯 Finding optimal adjuster: {claim_id}",
            "claim_id": claim_id,
            "status": "routing",
            "stage": "routing"
        })

        # Get adjusters
        adjusters = await mongodb.get_all_adjusters(available_only=True)

        # Check auto-processing
        logger.info(f"🤖 Checking auto-processing eligibility...")
        auto_check = auto_processor.should_auto_process(
            claim_data,
            scores["severity_score"],
            scores["complexity_score"]
        )

        routing_decision = None
        if auto_check["should_auto_process"]:
            logger.info(f"🤖 Auto-processing: {auto_check['reason']}")

            await event_queue.publish({
                "type": "claim_status_update",
                "message": f"🤖 Auto-processing: {auto_check['reason']}",
                "claim_id": claim_id,
                "status": "routing",
                "stage": "auto_processing"
            })

            auto_decision = auto_check["auto_decision"]
            if auto_decision.get("action") == "approve":
                routing_decision = await auto_processor.process_auto_approved_claim(
                    claim_id, claim_data, auto_decision
                )
            elif auto_decision.get("action") == "route_to_junior":
                routing_decision = await auto_processor.route_to_junior_adjuster(
                    claim_data, adjusters, auto_decision
                )

        # Regular routing if not auto-processed
        if not routing_decision:
            logger.info(f"🎯 Routing to adjuster...")
            routing_decision = await router.route_claim(
                claim_data=claim_data,
                available_adjusters=adjusters,
                severity_score=scores["severity_score"],
                complexity_score=scores["complexity_score"],
                fraud_flags=fraud_flags
            )

        # Determine final status
        processing_time = time.time() - start_time
        final_status = "in_progress" if routing_decision.get("adjuster_id") else "routing"

        # Save final claim
        full_claim = {
            "claim_id": claim_id,
            "source_filename": source_filename_stem,
            "source": source,
            "source_metadata": source_metadata,
            "document_types": [extracted.get("document_type", "unknown")],
            "file_paths": [file_path],
            "extracted_data": claim_data,
            "severity_score": scores["severity_score"],
            "complexity_score": scores["complexity_score"],
            "fraud_flags": fraud_flags,
            "routing_decision": routing_decision,
            "status": final_status,
            "processing_time_seconds": processing_time,
        }

        await mongodb.save_claim(full_claim)

        # Schedule auto-transition
        if final_status == "in_progress":
            auto_transition = get_auto_transition_service()
            auto_transition.schedule_transition(
                claim_id=claim_id,
                claim_amount=claim_data.get("claim_amount", 0)
            )
            logger.info(f"📅 Scheduled auto-transition")

        # Update adjuster workload
        adjuster_id = routing_decision.get("adjuster_id")
        if adjuster_id and adjuster_id != "AUTO_SYSTEM":
            await mongodb.update_adjuster_workload(adjuster_id, 1)

        # Create task
        task_created = False
        if routing_decision.get("adjuster_id"):
            try:
                task_id = await create_claim_task(
                    claim_id=claim_id,
                    adjuster_id=routing_decision.get("adjuster_id"),
                    adjuster_name=routing_decision.get("assigned_to"),
                    claim_amount=claim_data.get("claim_amount"),
                    incident_type=claim_data.get("incident_type"),
                    priority=routing_decision.get("priority", "medium"),
                    is_auto_approved=routing_decision.get("auto_processed", False)
                )

                if task_id:
                    task_created = True
                    await mongodb.update_claim_field(claim_id, "task_id", task_id)
                    logger.info(f"📋 Created task {task_id}")
            except Exception as e:
                logger.warning(f"Failed to create task: {e}")

        # Publish completion
        message = f"✅ Claim processed: {claim_id} → {routing_decision.get('assigned_to', 'Unassigned')}"
        if task_created:
            message += " (Task created)"

        await event_queue.publish({
            "type": "claim_processed",
            "message": message,
            "claim_id": claim_id,
            "status": final_status,
            "routing_decision": routing_decision,
            "processing_time": processing_time,
            "severity_score": scores["severity_score"],
            "complexity_score": scores["complexity_score"],
            "task_created": task_created
        })

        logger.info(f"🎉 Claim processed in {processing_time:.1f}s → {final_status}")

        return {
            "status": "success",
            "claim_id": claim_id,
            "final_status": final_status,
            "processing_time": processing_time,
            "adjuster": routing_decision.get("assigned_to")
        }

    except Exception as e:
        logger.error(f"Error processing claim: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


async def _parse_claim_data(document_text: str, extracted: Dict) -> Dict:
    """Parse extracted text into structured claim data using GPT-4o"""
    import openai
    import json

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""Extract claim information from this document and return as JSON:

{document_text[:3000]}

Return JSON with these fields:
{{
  "claim_number": str (the claim number from document) or null,
  "policy_number": str (policy number) or null,
  "claim_amount": float or null,
  "incident_type": "auto" | "property" | "injury" | "commercial" | "liability",
  "incident_date": "YYYY-MM-DD" or null,
  "report_date": "YYYY-MM-DD" or null,
  "parties": [{{"name": str, "role": "claimant"|"insured"|"third_party"}}],
  "location": {{"city": str, "state": str}},
  "injuries": [{{"person": str, "severity": "minor"|"moderate"|"serious"|"critical"|"fatal", "description": str}}],
  "description": str,
  "fault_determination": "clear" | "disputed" | "multi-party",
  "attorney_involved": bool
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        claim_data = json.loads(response.choices[0].message.content)
        logger.info(f"Parsed claim data: {list(claim_data.keys())}")

        return claim_data

    except Exception as e:
        logger.error(f"Failed to parse claim data: {e}")
        return {
            "claim_amount": None,
            "incident_type": "unknown",
            "description": document_text[:500]
        }
