"""Document Classification - Rule-based + optional LLM."""
from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    TEXTBOOK = "textbook"
    QUESTION_PAPER = "question_paper"
    MARKING_SCHEME = "marking_scheme"
    CURRICULUM = "curriculum"
    BYLAW = "bylaw"
    MODEL_ANSWER = "model_answer"
    SAMPLE_PAPER = "sample_paper"
    BLUEPRINT = "blueprint"
    EXEMPLAR = "exemplar"
    WORKSHEET = "worksheet"
    ACTIVITY_GUIDE = "activity_guide"
    LAB_MANUAL = "lab_manual"
    REVISION_NOTES = "revision_notes"
    CIRCULAR = "circular"
    TEACHER_MANUAL = "teacher_manual"
    COMPETENCY_FRAMEWORK = "competency_framework"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    doc_type: DocumentType
    confidence: float
    metadata: dict
    matched_rules: list[str]


class DocumentClassifier:
    """Rule-based document classifier with optional LLM fallback."""
    
    def __init__(self, use_llm: bool = False, ollama_url: str = "http://localhost:11434",
                 ollama_model: str = "llama3.1:8b"):
        self.use_llm = use_llm
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile all classification patterns."""
        self.patterns = {
            DocumentType.TEXTBOOK: [
                (r"ncert|national council of educational research", 0.9),
                (r"textbook|पाठ्यपुस्तक", 0.8),
                (r"class\s+\d+|grade\s+\d+", 0.6),
                (r"chapter\s+\d+", 0.5),
            ],
            DocumentType.QUESTION_PAPER: [
                (r"question\s+paper|प्रश्न\s+पत्र", 0.95),
                (r"examination|परीक्षा", 0.7),
                (r"time\s*:\s*\d+\s*(hour|hr|min)", 0.8),
                (r"maximum\s+marks|अधिकतम\s+अंक", 0.8),
                (r"roll\s+no|अनुक्रमांक", 0.7),
            ],
            DocumentType.MARKING_SCHEME: [
                (r"marking\s+scheme|मूल्यांकन\s+योजना", 0.95),
                (r"answer\s+key|उत्तर\s+कुंजी", 0.9),
                (r"mark\s+distribution|अंक\s+वितरण", 0.8),
                (r"rubric|मूल्यांकन\s+मापदंड", 0.7),
            ],
            DocumentType.CURRICULUM: [
                (r"curriculum|पाठ्यक्रम", 0.9),
                (r"syllabus|पाठ्यचर्या", 0.85),
                (r"learning\s+outcome|अधिगम\s+परिणाम", 0.8),
                (r"competency|दक्षता", 0.7),
                (r"blueprint|खाका", 0.7),
            ],
            DocumentType.BYLAW: [
                (r"bye.?law|उप.?नियम", 0.9),
                (r"examination\s+bye.?law", 0.95),
                (r"affiliation\s+bye.?law", 0.9),
                (r"notification|अधिसूचना", 0.6),
                (r"circular|परिपत्र", 0.6),
            ],
            DocumentType.MODEL_ANSWER: [
                (r"model\s+answer|आदर्श\s+उत्तर", 0.95),
                (r"suggested\s+answer|सुझाया\s+गया\s+उत्तर", 0.8),
                (r"answer\s+script|उत्तर\s+लिपि", 0.7),
            ],
            DocumentType.SAMPLE_PAPER: [
                (r"sample\s+paper|नमूना\s+पत्र", 0.95),
                (r"practice\s+paper|अभ्यास\s+पत्र", 0.8),
                (r"mock\s+test|मॉक\s+टेस्ट", 0.8),
            ],
            DocumentType.BLUEPRINT: [
                (r"blueprint|खाका", 0.9),
                (r"question\s+paper\s+design", 0.8),
                (r"weightage|भार", 0.7),
                (r"typology|प्रकारिकी", 0.7),
            ],
            DocumentType.EXEMPLAR: [
                (r"exemplar|उदाहरण", 0.9),
                (r"exemplar\s+problem|उदाहरण\s+समस्या", 0.9),
            ],
            DocumentType.WORKSHEET: [
                (r"worksheet|कार्यपत्रक", 0.9),
                (r"activity\s+sheet|गतिविधि\s+पत्रक", 0.8),
            ],
            DocumentType.ACTIVITY_GUIDE: [
                (r"activity\s+guide|गतिविधि\s+मार्गदर्शिका", 0.9),
                (r"teacher\s+guide|शिक्षक\s+मार्गदर्शिका", 0.7),
            ],
            DocumentType.LAB_MANUAL: [
                (r"lab\s+manual|प्रयोगशाला\s+मैनुअल", 0.95),
                (r"practical\s+manual|प्रायोगिक\s+मैनुअल", 0.9),
                (r"experiment\s+\d+", 0.7),
            ],
            DocumentType.REVISION_NOTES: [
                (r"revision\s+notes|पुनरावृत्ति\s+नोट्स", 0.9),
                (r"summary|सारांश", 0.6),
                (r"key\s+points|मुख्य\s+बिंदु", 0.7),
            ],
            DocumentType.CIRCULAR: [
                (r"circular|परिपत्र", 0.8),
                (r"circular\s+no\.?\s*\d+", 0.9),
                (r"cbse\s+circular", 0.85),
            ],
            DocumentType.TEACHER_MANUAL: [
                (r"teacher\s+manual|शिक्षक\s+मैनुअल", 0.95),
                (r"teacher\s+guide|शिक्षक\s+मार्गदर्शिका", 0.9),
            ],
            DocumentType.COMPETENCY_FRAMEWORK: [
                (r"competency\s+framework|दक्षता\s+ढांचा", 0.95),
                (r"learning\s+framework|अधिगम\s+ढांचा", 0.8),
            ],
        }
    
    def classify(self, pdf_path: Path, first_pages_text: str = "") -> ClassificationResult:
        """Classify document based on filename and content."""
        
        # Get filename features
        filename = pdf_path.name.lower()
        stem = pdf_path.stem.lower()
        
        scores = {}
        matched_rules = {}
        
        # Run rule-based classification
        for doc_type, patterns in self.patterns.items():
            score = 0.0
            rules = []
            
            # Check filename
            for pattern, weight in patterns:
                if re.search(pattern, filename) or re.search(pattern, stem):
                    score = max(score, weight)
                    rules.append(f"filename:{pattern}")
            
            # Check first pages text
            if first_pages_text:
                for pattern, weight in patterns:
                    if re.search(pattern, first_pages_text, re.IGNORECASE):
                        score = max(score, weight * 0.8)  # Content slightly less weight
                        rules.append(f"content:{pattern}")
            
            if score > 0:
                scores[doc_type] = score
                matched_rules[doc_type] = rules
        
        # Get best match
        if scores:
            best_type = max(scores, key=scores.get)
            confidence = scores[best_type]
            rules = matched_rules.get(best_type, [])
        else:
            best_type = DocumentType.UNKNOWN
            confidence = 0.0
            rules = []
        
        # Extract metadata
        metadata = self._extract_metadata(filename, stem, first_pages_text)
        
        # Optional LLM refinement
        if self.use_llm and confidence < 0.8:
            llm_result = self._llm_classify(filename, first_pages_text[:2000])
            if llm_result and llm_result.confidence > confidence:
                return llm_result
        
        return ClassificationResult(
            doc_type=best_type,
            confidence=confidence,
            metadata=metadata,
            matched_rules=rules
        )
    
    def _extract_metadata(self, filename: str, stem: str, text: str) -> dict:
        """Extract structured metadata from filename and content."""
        metadata = {
            "source_filename": filename,
            "board": "CBSE",
        }
        
        # Grade/Class
        grade_match = re.search(r"(?:class|grade|std)\.?\s*(\d{1,2})", filename + " " + text[:500], re.IGNORECASE)
        if grade_match:
            grade = int(grade_match.group(1))
            if 1 <= grade <= 12:
                metadata["grade"] = grade
        
        # Subject
        subjects = {
            "mathematics": ["math", "mathematics", "ganita", "गणित"],
            "physics": ["physics", "bhautik", "भौतिक"],
            "chemistry": ["chemistry", "rasayan", "रसायन"],
            "biology": ["biology", "jeev", "जीव", "life science"],
            "science": ["science", "vigyan", "विज्ञान"],
            "english": ["english", "angrezi", "अंग्रेजी"],
            "hindi": ["hindi", "हिंदी"],
            "sanskrit": ["sanskrit", "संस्कृत"],
            "social_science": ["social", "sst", "history", "geography", "civics", "political"],
            "computer_science": ["computer", "ip", "informatics", "cs"],
            "accountancy": ["accountancy", "accounts", "lekha"],
            "business_studies": ["business", "bst", "vyapar"],
            "economics": ["economics", "arthashastra", "अर्थशास्त्र"],
        }
        
        for subj, keywords in subjects.items():
            if any(kw in filename or kw in text[:1000].lower() for kw in keywords):
                metadata["subject"] = subj
                break
        
        # Year
        year_match = re.search(r"(20\d{2})", filename)
        if year_match:
            metadata["year"] = int(year_match.group(1))
        
        # Language
        if re.search(r"[अ-ह]", text[:500]):
            metadata["language"] = "hi"
        else:
            metadata["language"] = "en"
        
        return metadata
    
    def _llm_classify(self, filename: str, text: str) -> Optional[ClassificationResult]:
        """Optional LLM-based classification."""
        try:
            import requests
            prompt = f"""Classify this CBSE/NCERT document:
Filename: {filename}
First 2000 chars: {text}

Types: textbook, question_paper, marking_scheme, curriculum, bylaw, model_answer, sample_paper, blueprint, exemplar, worksheet, activity_guide, lab_manual, revision_notes, circular, teacher_manual, competency_framework

Return JSON: {{"type": "...", "confidence": 0.0-1.0, "metadata": {{...}}}}"""
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "format": "json", "stream": False},
                timeout=30
            )
            if response.status_code == 200:
                import json
                result = json.loads(response.json()["response"])
                return ClassificationResult(
                    doc_type=DocumentType(result["type"]),
                    confidence=result["confidence"],
                    metadata=result.get("metadata", {}),
                    matched_rules=["llm"]
                )
        except Exception as e:
            logger.debug(f"LLM classification failed: {e}")
        return None


def get_classifier(use_llm: bool = False, **kwargs) -> DocumentClassifier:
    """Factory for document classifier."""
    return DocumentClassifier(use_llm=use_llm, **kwargs)