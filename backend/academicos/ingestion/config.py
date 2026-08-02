"""AcademicOS Ingestion Pipeline - Configuration."""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class IngestionSettings(BaseSettings):
    # Source directories
    source_dirs: list[Path] = Field(
        default_factory=lambda: [
            Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset"),
            Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\cbse-dataset"),
        ]
    )
    
    # Output
    output_dir: Path = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\processed")
    state_db: Path = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\processed\ingestion_state.db")
    
    # Processing
    max_workers: int = 4
    batch_size: int = 10
    page_timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # OCR
    use_gpu: bool = False
    paddleocr_lang: str = "en"  # en, hi, or "en,hi" for mixed
    tesseract_lang: str = "eng+hin"
    ocr_confidence_threshold: float = 0.6
    force_ocr_min_chars: int = 50  # If native text < this, force OCR
    
    # Layout
    use_layoutparser: bool = True
    layout_model: str = "lp://PubLayNet/ppyolov2_r50vd_dcn_365e/config"
    
    # Tables
    table_engines: list[str] = ["pdfplumber", "camelot"]
    table_min_accuracy: float = 0.7
    
    # Equations
    detect_equations: bool = True
    equation_model: str = "pix2struct"  # or unimernet
    
    # Quality
    min_page_confidence: float = 0.5
    flag_for_review_below: float = 0.6
    
    # Monitoring
    log_dir: Path = Path(r"C:\Users\varsh\OneDrive\Documents\Sarvam\logs")
    metrics_port: int = 9090
    dashboard_port: int = 8501
    
    # Classification
    use_llm_classification: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    
    class Config:
        env_prefix = "ACADEMICOS_"
        case_sensitive = False


settings = IngestionSettings()