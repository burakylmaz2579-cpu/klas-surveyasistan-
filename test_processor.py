import os
from create_sample_pdf import generate_sample_pdf
from doc_processor import SurveyDocumentProcessor

def run_test():
    print("--- SURVEYOR ASSISTANT PORTAL TEST RUN ---")
    pdf_path = "sample_survey_report.pdf"
    
    if not os.path.exists(pdf_path):
        print("Generating sample PDF...")
        generate_sample_pdf(pdf_path)
        
    print(f"Loading and processing {pdf_path}...")
    processor = SurveyDocumentProcessor(pdf_path)
    
    print("\n--- EXTRACTED VESSEL INFO ---")
    for k, v in processor.vessel_info.items():
        print(f"{k}: {v}")
        
    print("\n--- EXTRACTED TABLES ---")
    print(f"Total tables found: {len(processor.tables)}")
    for i, t in enumerate(processor.tables):
        print(f"Table {i+1} on page {t['page']}: {len(t['data'])} rows")
        
    print("\n--- RUNNING AUDIT PROCESSOR ---")
    findings = processor.process_findings()
    print(f"Total processed findings: {len(findings)}")
    
    for f in findings[:5]:
        print(f"\nItem #{f['item_no']}: {f['title']}")
        print(f"  Rule: {f['rule']}")
        print(f"  Status: {f['status']} (Severity: {f['severity']})")
        print(f"  Description: {f['description']}")
        if f.get('recommendation'):
            print(f"  Correction: {f['recommendation']}")

if __name__ == "__main__":
    run_test()
