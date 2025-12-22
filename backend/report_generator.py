"""
AI-powered Medical Report Generator using Groq LLM.
Generates comprehensive medical reports from patient data, entries, and analysis results.
"""
import os
import json
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_groq_client():
    """Get Groq client instance."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment variables")
    
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)


def generate_report_content(
    patient_data: Dict[str, Any],
    doctor_data: Dict[str, Any],
    entry_data: Dict[str, Any],
    analysis_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate medical report content using Groq LLM.
    
    Returns markdown formatted report content.
    """
    # Build context for the LLM
    patient_info = f"""
Patient Information:
- Name: {patient_data.get('username', 'N/A')}
- Age: {patient_data.get('age', 'N/A')}
- Gender: {patient_data.get('gender', 'N/A')}
- Medical History: {patient_data.get('medical_history', 'Not provided')}
"""

    doctor_info = f"""
Attending Physician:
- Dr. {doctor_data.get('username', 'N/A')}
- Specialization: {doctor_data.get('specialization', 'N/A')}
- Hospital: {doctor_data.get('hospital', 'N/A')}
- License Number: {doctor_data.get('license_number', 'N/A')}
"""

    entry_info = f"""
Examination Details:
- Date: {entry_data.get('time', datetime.now().isoformat())}
- Amount Voided: {entry_data.get('amount_voided', 'N/A')} ml
- Additional Notes: {entry_data.get('notes', 'None')}
"""

    # Parse analysis data if available
    analysis_info = ""
    if analysis_data and analysis_data.get('qmax_report_json'):
        try:
            qmax_data = json.loads(analysis_data['qmax_report_json'])
            analysis_info = f"""
Uroflowmetry Analysis Results:
- Maximum Flow Rate (Qmax): {qmax_data.get('Qmax', 'N/A'):.2f} ml/s
- Voided Volume: {qmax_data.get('Voided_Volume', 'N/A'):.2f} ml
- Time to Qmax: {qmax_data.get('Time_to_Qmax', 'N/A'):.2f} seconds
- Voiding Time: {qmax_data.get('Voiding_Time', 'N/A'):.2f} seconds
- Average Flow Rate: {qmax_data.get('Average_Flow_Rate', 'N/A'):.2f} ml/s
- Hesitancy: {qmax_data.get('Hesitancy', 'N/A'):.2f} seconds
- Flow Time: {qmax_data.get('Flow_Time', 'N/A'):.2f} seconds
"""
        except (json.JSONDecodeError, TypeError, KeyError):
            analysis_info = "\nAnalysis data available but could not be parsed."

    # Create the prompt for Groq
    system_prompt = """You are a medical report generator assistant. Generate professional, 
comprehensive medical reports based on uroflowmetry examination data. The reports should be:
1. Professional and suitable for medical records
2. Well-structured with clear sections
3. Include clinical observations and recommendations when appropriate
4. Written in markdown format for easy formatting

IMPORTANT: Generate factual, objective reports based only on the provided data.
Do not make up any information not provided. If data is missing, note it as "Not Available"."""

    user_prompt = f"""Generate a comprehensive medical examination report based on the following data:

{patient_info}
{doctor_info}
{entry_info}
{analysis_info}

Please generate a professional medical report in markdown format with the following sections:
1. Report Header (Title, Date, Report ID)
2. Patient Demographics
3. Examination Summary
4. Uroflowmetry Results (if analysis data available)
5. Clinical Interpretation
6. Recommendations
7. Physician Signature Section

Make the report professional, clear, and suitable for medical records."""

    try:
        client = get_groq_client()
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating report with Groq: {e}")
        # Fallback to basic template
        return _generate_fallback_report(patient_data, doctor_data, entry_data, analysis_data)


def _generate_fallback_report(
    patient_data: Dict[str, Any],
    doctor_data: Dict[str, Any],
    entry_data: Dict[str, Any],
    analysis_data: Optional[Dict[str, Any]] = None
) -> str:
    """Generate a basic report template when AI is unavailable."""
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""# Medical Examination Report

**Report Date:** {report_date}  
**Report ID:** RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}

---

## Patient Information

| Field | Value |
|-------|-------|
| Name | {patient_data.get('username', 'N/A')} |
| Age | {patient_data.get('age', 'N/A')} |
| Gender | {patient_data.get('gender', 'N/A')} |

---

## Attending Physician

| Field | Value |
|-------|-------|
| Name | Dr. {doctor_data.get('username', 'N/A')} |
| Specialization | {doctor_data.get('specialization', 'N/A')} |
| Hospital | {doctor_data.get('hospital', 'N/A')} |

---

## Examination Details

**Date of Examination:** {entry_data.get('time', 'N/A')}  
**Amount Voided:** {entry_data.get('amount_voided', 'N/A')} ml  
**Notes:** {entry_data.get('notes', 'None provided')}

"""

    if analysis_data and analysis_data.get('qmax_report_json'):
        try:
            qmax = json.loads(analysis_data['qmax_report_json'])
            report += f"""
---

## Uroflowmetry Analysis Results

| Parameter | Value | Unit |
|-----------|-------|------|
| Maximum Flow Rate (Qmax) | {qmax.get('Qmax', 'N/A'):.2f} | ml/s |
| Voided Volume | {qmax.get('Voided_Volume', 'N/A'):.2f} | ml |
| Time to Qmax | {qmax.get('Time_to_Qmax', 'N/A'):.2f} | seconds |
| Voiding Time | {qmax.get('Voiding_Time', 'N/A'):.2f} | seconds |
| Average Flow Rate | {qmax.get('Average_Flow_Rate', 'N/A'):.2f} | ml/s |

"""
        except:
            pass

    report += f"""
---

## Physician Signature

**Dr. {doctor_data.get('username', 'N/A')}**  
{doctor_data.get('specialization', '')}  
{doctor_data.get('hospital', '')}  
License: {doctor_data.get('license_number', 'N/A')}

*This report was auto-generated on {report_date}*
"""
    return report


def markdown_to_pdf(markdown_content: str, output_path: str) -> bool:
    """
    Convert markdown content to PDF.
    Returns True on success, False on failure.
    """
    try:
        # Try weasyprint first (best quality)
        try:
            from weasyprint import HTML, CSS
            import markdown
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code']
            )
            
            # Add styling
            styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        hr {{
            border: none;
            border-top: 1px solid #eee;
            margin: 30px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
            HTML(string=styled_html).write_pdf(output_path)
            return True
            
        except ImportError:
            print("weasyprint not available, trying alternative methods...")
        
        # Try pdfkit as fallback
        try:
            import pdfkit
            import markdown
            
            html_content = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code']
            )
            
            pdfkit.from_string(html_content, output_path)
            return True
            
        except ImportError:
            print("pdfkit not available...")
        
        # If no PDF library available, return False
        print("No PDF generation library available. Install weasyprint or pdfkit.")
        return False
        
    except Exception as e:
        print(f"Error converting markdown to PDF: {e}")
        return False


def upload_pdf_to_cloudinary(file_path: str, folder: str = "dockothon/reports") -> Optional[str]:
    """
    Upload PDF to Cloudinary and return the download URL.
    Uses the same upload pattern as videos (cloudinary_service).
    """
    try:
        from cloudinary_service import upload_file
        
        # Use auto type like videos do - this works with the existing config
        result = upload_file(file_path, folder=folder, resource_type="auto")
        
        url = result.get("url")
        if url:
            print(f"PDF uploaded successfully: {url}")
            return url
        
        print("No URL returned from Cloudinary upload")
        return None
        
    except Exception as e:
        print(f"Error uploading PDF to Cloudinary: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_and_upload_report(
    patient_data: Dict[str, Any],
    doctor_data: Dict[str, Any],
    entry_data: Dict[str, Any],
    analysis_data: Optional[Dict[str, Any]] = None,
    entry_id: int = None
) -> Dict[str, Any]:
    """
    Main function to generate report and upload to Cloudinary.
    
    Returns:
        dict with:
            - success: bool
            - report_url: str (if PDF uploaded)
            - markdown_content: str (always included)
            - error: str (if failed)
    """
    result = {
        "success": False,
        "report_url": None,
        "markdown_content": None,
        "error": None
    }
    
    try:
        # Step 1: Generate report content
        print("Generating report content with AI...")
        markdown_content = generate_report_content(
            patient_data, doctor_data, entry_data, analysis_data
        )
        result["markdown_content"] = markdown_content
        
        # Step 2: Try to convert to PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        print("Converting to PDF...")
        pdf_success = markdown_to_pdf(markdown_content, pdf_path)
        
        if pdf_success and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            # Step 3: Upload to Cloudinary
            print("Uploading PDF to Cloudinary...")
            folder = f"dockothon/entries/{entry_id}/reports" if entry_id else "dockothon/reports"
            report_url = upload_pdf_to_cloudinary(pdf_path, folder)
            
            if report_url:
                result["report_url"] = report_url
                result["success"] = True
                print(f"Report uploaded successfully: {report_url}")
            else:
                # PDF created but upload failed - still success with markdown
                result["success"] = True
                result["error"] = "PDF created but upload failed. Markdown content saved."
        else:
            # PDF generation failed - store markdown only
            result["success"] = True
            result["error"] = "PDF generation unavailable. Markdown content saved."
        
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
            
    except Exception as e:
        result["error"] = str(e)
        print(f"Error in report generation: {e}")
    
    return result
