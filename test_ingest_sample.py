#!/usr/bin/env python
"""Test the ingestion pipeline on a small sample."""
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from ingestion.state import IngestionStateDB, IngestionStatus
from ingestion.main import IngestionPipeline, IngestionConfig


def test_state_db():
    """Test the state database."""
    print("Testing IngestionStateDB...")
    
    # Use a test database
    db = IngestionStateDB("test_ingestion_state.db")
    
    # Test adding a document
    test_pdf = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\science\class6_curiosity.pdf")
    
    if test_pdf.exists():
        doc = db.add_document(test_pdf, classification="textbook")
        print(f"  ✓ Added document: {doc.document_id}")
        print(f"    Source: {doc.source_path}")
        print(f"    Pages: {doc.pages_total}")
        print(f"    Status: {doc.status}")
        
        # Test retrieving
        retrieved = db.get_document(doc.document_id)
        assert retrieved is not None
        print(f"  ✓ Retrieved document: {retrieved.document_id}")
        
        # Test updating
        db.update_document(doc.document_id, status=IngestionStatus.PROCESSING)
        updated = db.get_document(doc.document_id)
        assert updated.status == IngestionStatus.PROCESSING
        print(f"  ✓ Updated status to PROCESSING")
        
        # Test stats
        stats = db.get_stats()
        print(f"  ✓ Stats: {stats}")
        
        print("  ✓ State DB tests passed!\n")
        return True
    else:
        print(f"  ⚠ Test PDF not found: {test_pdf}")
        return False


def test_discovery():
    """Test document discovery."""
    print("Testing document discovery...")
    
    db = IngestionStateDB("test_ingestion_state.db")
    
    # Discover from ncert-dataset
    ncert_path = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset")
    if ncert_path.exists():
        docs = db.discover_documents([ncert_path])
        print(f"  ✓ Found {len(docs)} documents in ncert-dataset")
        for doc in docs[:3]:  # Show first 3
            print(f"    - {doc.source_path} ({doc.pages_total} pages)")
    else:
        print(f"  ⚠ ncert-dataset not found: {ncert_path}")
    
    # Discover from ZIPs
    cbse_path = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\cbse-dataset\question-papers\question-paper\2026\X")
    if cbse_path.exists():
        docs = db.discover_from_zips([cbse_path])
        print(f"  ✓ Found {len(docs)} documents in ZIPs")
    else:
        print(f"  ⚠ cbse-dataset path not found: {cbse_path}")
    
    print()


def test_pipeline_on_sample():
    """Test the pipeline on a small sample."""
    print("Testing pipeline on sample...")
    
    config = IngestionConfig(
        source_paths=[
            Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\science\class6_curiosity.pdf"),
        ],
        output_dir="test_output",
        workers=1,
        db_path="test_ingestion_state.db",
        temp_dir="test_temp",
        batch_size=1,
    )
    
    pipeline = IngestionPipeline(config)
    
    # Discover
    docs = pipeline.discover_all_documents()
    print(f"  ✓ Discovered {len(docs)} documents")
    
    # Process first document
    if docs:
        result = pipeline.process_document(docs[0])
        if result.success:
            print(f"  ✓ Successfully processed {result.pages_processed} pages")
            print(f"    Output: {result.output_path}")
            if result.output_path:
                import json
                with open(result.output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"    Pages: {data.get('page_count')}")
                    print(f"    Classification: {data.get('classification')}")
                    print(f"    Metadata: {data.get('metadata')}")
        else:
            print(f"  ✗ Failed to process: {result.error_message}")
    
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("AcademicOS Ingestion Pipeline - Sample Test")
    print("=" * 60 + "\n")
    
    try:
        test_state_db()
        test_discovery()
        test_pipeline_on_sample()
        
        print("=" * 60)
        print("All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
