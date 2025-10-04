"""
Pathway Real-time Processing Pipeline
Watches uploads directory and processes claims automatically
"""

import os
import logging
import asyncio
import threading
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pathway as pw
    PATHWAY_AVAILABLE = True
except ImportError:
    logger.warning("Pathway not available. Install with: pip install pathway[all]")
    PATHWAY_AVAILABLE = False


class PathwayPipeline:
    """Real-time claims processing pipeline using Pathway"""

    def __init__(self, data_dir: str = "./uploads"):
        self.data_dir = data_dir
        self.pipeline_thread = None
        self.running = False

    async def start_pipeline(self):
        """Start Pathway pipeline in background thread"""
        if not PATHWAY_AVAILABLE:
            logger.error("Pathway not available - cannot start pipeline")
            return

        if self.running:
            logger.warning("Pathway pipeline already running")
            return

        try:
            logger.info(f"🚀 Starting Pathway pipeline watching: {self.data_dir}")

            # Start Pathway in background thread
            self.pipeline_thread = threading.Thread(
                target=self._run_pathway_pipeline,
                daemon=True
            )
            self.pipeline_thread.start()
            self.running = True

            logger.info("✅ Pathway pipeline started successfully")

        except Exception as e:
            logger.error(f"Failed to start Pathway pipeline: {e}", exc_info=True)

    def _run_pathway_pipeline(self):
        """Run the Pathway pipeline (blocking call in thread)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from .event_queue import get_event_queue
            from .sync_mongodb import get_sync_mongodb
            from .pinecone_service import get_pinecone_service
            from .document_processor import get_document_processor
            from .claim_scorer import get_claim_scorer
            from .fraud_detector import get_fraud_detector
            from .router_engine import get_router_engine
            from .rag_service import get_rag_service
            from .document_context import get_document_context_manager

            logger.info("🔧 Initializing Pathway components...")

            # Create file watcher
            files = pw.io.fs.read(
                path=self.data_dir,
                format="binary",
                mode="streaming",
                with_metadata=True,
            )

            logger.info(f"👀 Pathway watching directory: {self.data_dir}")

            # Process each file
            def process_file(data, metadata):
                """Process a single claim file"""
                try:
                    import time
                    start_time = time.time()

                    # Extract file path
                    file_path_obj = metadata["path"]
                    file_path = file_path_obj.value if hasattr(file_path_obj, 'value') else str(file_path_obj)
                    file_path = file_path.strip('"').strip("'")
                    source_filename = Path(file_path).name

                    # Skip system files
                    IGNORED_FILES = {'.DS_Store', '.gitkeep', 'Thumbs.db', '.gitignore', '.keep'}
                    if source_filename in IGNORED_FILES or source_filename.startswith('.'):
                        logger.info(f"⏭️  Skipping system file: {source_filename}")
                        return {"status": "skipped", "reason": "system_file"}

                    source_filename = Path(file_path).stem

                    # Check if claim already exists by filename BEFORE creating temp claim
                    mongodb = get_sync_mongodb()
                    existing_claim = mongodb.get_claim_by_filename(source_filename)

                    if existing_claim:
                        existing_claim_id = existing_claim.get("claim_id")
                        current_status = existing_claim.get("status")
                        # Don't reprocess claims that are already assigned or beyond
                        if current_status in ["assigned", "in_progress", "review", "completed", "approved", "closed", "auto_approved", "auto_routed"]:
                            logger.info(f"⏭️  Skipping {source_filename} - already exists as {existing_claim_id} with status: {current_status}")
                            return {"status": "skipped", "reason": f"already_in_status_{current_status}"}

                    logger.info(f"📄 Processing new file: {source_filename}")

                    # Generate unique claim ID immediately (no temp ID)
                    from datetime import datetime
                    import random
                    import string

                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    claim_id = f"CLM-{timestamp}-{random_suffix}"

                    logger.info(f"✅ Generated unique claim ID: {claim_id}")

                    # Publish event with final claim ID
                    event_queue = get_event_queue()
                    try:
                        loop.run_until_complete(event_queue.publish({
                            "type": "claim_uploaded",
                            "message": f"📤 New claim uploaded: {claim_id}",
                            "claim_id": claim_id,
                            "status": "uploaded"
                        }))
                    except:
                        pass

                    # Detect source (upload vs gmail)
                    is_gmail_source = "_gmail_" in source_filename.lower()
                    source = "gmail" if is_gmail_source else "upload"
                    source_metadata = {}
                    if is_gmail_source:
                        # Extract email info from filename if possible
                        source_metadata = {
                            "source_type": "gmail_auto_fetch",
                            "filename": source_filename
                        }

                    # Save initial claim to MongoDB with final claim ID
                    initial_claim = {
                        "claim_id": claim_id,
                        "source_filename": source_filename,
                        "source": source,
                        "source_metadata": source_metadata,
                        "status": "extracting",
                        "document_types": [],
                        "file_paths": [file_path],
                        "created_at": datetime.now()
                    }
                    mongodb.save_claim(initial_claim)

                    # Publish extraction start event
                    try:
                        loop.run_until_complete(event_queue.publish({
                            "type": "claim_status_update",
                            "message": f"📄 Extracting document data: {claim_id}",
                            "claim_id": claim_id,
                            "status": "extracting",
                            "stage": "extraction"
                        }))
                    except:
                        pass

                    # Extract document
                    doc_processor = get_document_processor()
                    try:
                        extracted = loop.run_until_complete(doc_processor.extract_document_data(file_path))
                    except Exception as e:
                        logger.error(f"❌ Extraction failed: {e}")
                        return {"status": "error", "error": str(e)}

                    document_text = extracted.get("text", "")
                    if not document_text:
                        logger.error(f"❌ No text extracted")
                        return {"status": "error", "error": "No text extracted"}

                    logger.info(f"✅ Extracted {len(document_text)} chars")

                    # Parse extracted text for claim data (simplified)
                    claim_data = loop.run_until_complete(self._parse_claim_data(document_text, extracted))

                    # Store extracted policy number separately if available
                    extracted_policy_number = claim_data.get("policy_number")
                    if extracted_policy_number:
                        logger.info(f"📋 Policy number from document: {extracted_policy_number}")

                    # Add document to RAG service for Q&A
                    try:
                        rag_service = get_rag_service()
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
                        logger.info(f"✅ Added claim {claim_id} to RAG service")
                    except Exception as e:
                        logger.warning(f"Failed to add to RAG service: {e}")

                    # Add to document context manager
                    try:
                        context_mgr = get_document_context_manager()
                        context_mgr.add_context(
                            claim_id=claim_id,
                            raw_text=document_text,
                            structured_data=claim_data,
                            document_type=extracted.get("document_type", "unknown"),
                            file_path=file_path,
                            tables=extracted.get("tables", [])
                        )
                        logger.info(f"✅ Added claim {claim_id} to document context")
                    except Exception as e:
                        logger.warning(f"Failed to add to document context: {e}")

                    # Update claim with extracted data and status
                    mongodb.save_claim({
                        "claim_id": claim_id,
                        "source_filename": source_filename,
                        "status": "scoring",
                        "extracted_data": claim_data,
                        "extracted_text": document_text,  # Store LandingAI extracted text
                        "file_paths": [file_path]
                    })

                    # Publish scoring event
                    try:
                        loop.run_until_complete(event_queue.publish({
                            "type": "claim_status_update",
                            "message": f"📊 Analyzing claim severity and complexity: {claim_id}",
                            "claim_id": claim_id,
                            "status": "scoring",
                            "stage": "scoring"
                        }))
                    except:
                        pass

                    # Score claim
                    scorer = get_claim_scorer()
                    scores = loop.run_until_complete(scorer.score_claim(claim_data))

                    logger.info(f"✅ Scores - Severity: {scores['severity_score']:.1f}, Complexity: {scores['complexity_score']:.1f}")

                    # Publish fraud detection event
                    try:
                        loop.run_until_complete(event_queue.publish({
                            "type": "claim_status_update",
                            "message": f"🔍 Running fraud detection analysis: {claim_id}",
                            "claim_id": claim_id,
                            "status": "scoring",
                            "stage": "fraud_detection"
                        }))
                    except:
                        pass

                    # Detect fraud
                    fraud_detector = get_fraud_detector()
                    fraud_flags = loop.run_until_complete(fraud_detector.detect_fraud_flags(claim_data, document_text))

                    if fraud_flags:
                        logger.warning(f"⚠️  {len(fraud_flags)} fraud flag(s) detected for {claim_id}")

                    # Update claim with scores and status
                    mongodb.save_claim({
                        "claim_id": claim_id,
                        "source_filename": source_filename,
                        "status": "routing",
                        "extracted_data": claim_data,
                        "severity_score": scores["severity_score"],
                        "complexity_score": scores["complexity_score"],
                        "fraud_flags": fraud_flags,
                        "file_paths": [file_path]
                    })

                    # Publish routing event
                    try:
                        loop.run_until_complete(event_queue.publish({
                            "type": "claim_status_update",
                            "message": f"🎯 Finding optimal adjuster match: {claim_id}",
                            "claim_id": claim_id,
                            "status": "routing",
                            "stage": "routing"
                        }))
                    except:
                        pass

                    # Get available adjusters
                    adjusters = mongodb.get_all_adjusters(available_only=True)

                    # Check if claim qualifies for auto-processing
                    from .auto_processor import get_auto_processor
                    auto_processor = get_auto_processor()
                    auto_check = auto_processor.should_auto_process(
                        claim_data,
                        scores["severity_score"],
                        scores["complexity_score"]
                    )

                    routing_decision = None
                    if auto_check["should_auto_process"]:
                        logger.info(f"🤖 Auto-processing claim: {auto_check['reason']}")

                        # Publish auto-processing event
                        try:
                            loop.run_until_complete(event_queue.publish({
                                "type": "claim_status_update",
                                "message": f"🤖 Auto-processing: {auto_check['reason']}",
                                "claim_id": claim_id,
                                "status": "routing",
                                "stage": "auto_processing"
                            }))
                        except:
                            pass

                        auto_decision = auto_check["auto_decision"]
                        if auto_decision.get("action") == "approve":
                            # Auto-approve
                            routing_decision = loop.run_until_complete(
                                auto_processor.process_auto_approved_claim(claim_id, claim_data, auto_decision)
                            )
                        elif auto_decision.get("action") == "route_to_junior":
                            # Route to junior adjuster
                            routing_decision = loop.run_until_complete(
                                auto_processor.route_to_junior_adjuster(claim_data, adjusters, auto_decision)
                            )
                            if not routing_decision:
                                # Fallback to regular routing if no junior available
                                logger.info("No junior adjuster available, using regular routing")

                    # If not auto-processed or auto-processing failed, use regular routing
                    if not routing_decision:
                        router = get_router_engine()
                        routing_decision = loop.run_until_complete(router.route_claim(
                            claim_data=claim_data,
                            available_adjusters=adjusters,
                            severity_score=scores["severity_score"],
                            complexity_score=scores["complexity_score"],
                            fraud_flags=fraud_flags
                        ))

                    # Save to MongoDB
                    processing_time = time.time() - start_time
                    final_status = "in_progress" if routing_decision.get("adjuster_id") else "routing"

                    # Detect source (upload vs gmail)
                    is_gmail_source = "_gmail_" in source_filename.lower()
                    source = "gmail" if is_gmail_source else "upload"
                    source_metadata = {}
                    if is_gmail_source:
                        source_metadata = {
                            "source_type": "gmail_auto_fetch",
                            "filename": source_filename
                        }

                    full_claim = {
                        "claim_id": claim_id,
                        "source_filename": source_filename,
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

                    mongodb.save_claim(full_claim)

                    # Schedule auto-transition if claim is in_progress
                    if final_status == "in_progress":
                        from .auto_transition import get_auto_transition_service
                        auto_transition = get_auto_transition_service()
                        auto_transition.schedule_transition(
                            claim_id=claim_id,
                            claim_amount=claim_data.get("claim_amount", 0)
                        )
                        logger.info(f"📅 Scheduled auto-transition for claim {claim_id}")

                    # Update adjuster workload (skip AUTO_SYSTEM)
                    adjuster_id = routing_decision.get("adjuster_id")
                    if adjuster_id and adjuster_id != "AUTO_SYSTEM":
                        mongodb.update_adjuster_workload(adjuster_id, 1)

                    # Create task for the claim
                    task_id = None
                    task_created = False
                    try:
                        if routing_decision.get("adjuster_id"):
                            # Import task management service
                            from services.task_manager import create_claim_task

                            task_id = loop.run_until_complete(create_claim_task(
                                claim_id=claim_id,
                                adjuster_id=routing_decision.get("adjuster_id"),
                                adjuster_name=routing_decision.get("assigned_to"),
                                claim_amount=claim_data.get("claim_amount"),
                                incident_type=claim_data.get("incident_type"),
                                priority=routing_decision.get("priority", "medium"),
                                is_auto_approved=routing_decision.get("auto_processed", False)
                            ))

                            if task_id:
                                task_created = True
                                # Update claim with task_id
                                mongodb.update_claim_field(claim_id, "task_id", task_id)
                                logger.info(f"📋 Created task {task_id} for claim {claim_id}")
                    except Exception as e:
                        logger.warning(f"Failed to create task for claim {claim_id}: {e}")

                    # Publish completion event
                    try:
                        message = f"✅ Claim processed: {claim_id} → {routing_decision.get('assigned_to', 'Unassigned')}"
                        if task_created:
                            message += " (Task created)"

                        loop.run_until_complete(event_queue.publish({
                            "type": "claim_processed",
                            "message": message,
                            "claim_id": claim_id,
                            "status": final_status,
                            "routing_decision": routing_decision,
                            "processing_time": processing_time,
                            "severity_score": scores["severity_score"],
                            "complexity_score": scores["complexity_score"],
                            "task_created": task_created
                        }))
                    except:
                        pass

                    logger.info(f"🎉 Claim processed: {claim_id} in {processing_time:.1f}s → Status: {final_status}")

                    return {"status": "success", "claim_id": claim_id}

                except Exception as e:
                    logger.error(f"Error processing file: {e}", exc_info=True)
                    return {"status": "error", "error": str(e)}

            # Apply processing to each file
            processed = files.select(
                result=pw.apply(process_file, pw.this.data, pw.this._metadata)
            )

            # Subscribe to results
            def on_result(key, row, time, is_addition):
                if is_addition:
                    result = row.get("result", {}) if isinstance(row, dict) else row.result
                    logger.info(f"Pathway result: {result}")

            pw.io.subscribe(processed, on_result)

            # Run pipeline (blocking)
            logger.info("▶️  Starting Pathway run...")
            pw.run()

        except Exception as e:
            logger.error(f"Pathway pipeline error: {e}", exc_info=True)

    async def _parse_claim_data(self, document_text: str, extracted: Dict) -> Dict:
        """Parse extracted text into structured claim data (simplified using LLM)"""
        import openai
        import json

        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            prompt = f"""Extract claim information from this document and return as JSON:

{document_text[:3000]}

Return JSON with these fields:
{{
  "claim_number": str (the claim number from document like "CLM-2025-001234" or "Claim Number: AUTO-2025-400-GLASS") or null,
  "policy_number": str (policy number from document) or null,
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


# Singleton instance
_pathway_pipeline = None


def get_pathway_pipeline() -> PathwayPipeline:
    """Get or create the Pathway pipeline instance"""
    global _pathway_pipeline
    if _pathway_pipeline is None:
        _pathway_pipeline = PathwayPipeline()
    return _pathway_pipeline
