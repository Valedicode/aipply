"""
Quick test to verify WeasyPrint PDF generation is working.
"""

from pathlib import Path
from weasyprint import HTML, CSS

# Test HTML
test_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WeasyPrint Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 2cm;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        p {
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <h1>WeasyPrint Test Document</h1>
    <p>If you can see this PDF, WeasyPrint is working correctly!</p>
    <p>Your GTK installation was successful.</p>
    <p>PDF generation is now enabled for CV and cover letter endpoints.</p>
</body>
</html>
"""

def test_weasyprint():
    """Test WeasyPrint PDF generation."""
    try:
        # Create output directory
        output_dir = Path(__file__).parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF
        output_path = output_dir / "weasyprint_test.pdf"
        HTML(string=test_html).write_pdf(str(output_path))
        
        if output_path.exists():
            print("[SUCCESS] WeasyPrint PDF generation is working!")
            print(f"   Test PDF created at: {output_path}")
            print(f"   File size: {output_path.stat().st_size} bytes")
            return True
        else:
            print("[ERROR] PDF file was not created")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Testing WeasyPrint PDF Generation")
    print("="*70 + "\n")
    
    success = test_weasyprint()
    
    print("\n" + "="*70)
    if success:
        print("[SUCCESS] WeasyPrint is fully functional!")
        print("   You can now use PDF generation endpoints:")
        print("   - POST /api/writer/generate-cv")
        print("   - POST /api/writer/generate-cover-letter")
    else:
        print("[ERROR] WeasyPrint test failed")
        print("   Check your GTK installation")
    print("="*70 + "\n")

