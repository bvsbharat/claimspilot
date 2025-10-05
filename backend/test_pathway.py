"""
Test Pathway pipeline directly to see errors
"""
import logging
logging.basicConfig(level=logging.INFO)

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.pathway_pipeline import PathwayPipeline

# Create and start pipeline
pipeline = PathwayPipeline(data_dir="./uploads")
print("Starting Pathway pipeline test...")

try:
    # Run directly (not in thread) to see errors
    pipeline._run_pathway_pipeline()
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
