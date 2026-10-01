import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import fitz
for pdf,label in [(r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters\aejm1\aejm113.pdf","aejm1-ch13"),
                  (r"C:\Users\varsh\OneDrive\Documents\Sarvam\ncert-dataset\textbooks\chapters\jhks1\jhks105.pdf","jhks1-ch05")]:
    d=fitz.open(pdf)
    print("="*60); print(label,"pages",len(d))
    t=d[1].get_text()
    print("page2 text len:",len(t))
    print(repr(t[:400]))
    d.close()
