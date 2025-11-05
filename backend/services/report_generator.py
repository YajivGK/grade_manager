import html as html_module
from datetime import datetime
from sqlalchemy.orm import Session
from models import StudentEvaluation, Student, Subject, Class, InternalMarks

def generate_evaluation_report_html(subject_id, batch, evaluation_date, db):
    """
    Generate HTML report for evaluated students for a specific batch and subject
    Returns: HTML content as string
    """
    try:
        # Get subject
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            return "<html><body><h1>Subject not found</h1></body></html>"
        
        # Get evaluations
        evaluations = db.query(StudentEvaluation).join(Student).filter(
            StudentEvaluation.subject_id == subject_id,
            StudentEvaluation.batch == batch,
            StudentEvaluation.evaluation_date == evaluation_date
        ).order_by(Student.regno).all()
        
        if not evaluations:
            return "<html><body><h1>No evaluations found</h1></body></html>"
        
        # Build HTML content
        html_content = ""
        
        # Header
        batch_name = "Odd" if batch == 1 else "Even"
        date_str = evaluation_date.strftime('%Y-%m-%d') if evaluation_date else 'N/A'
        
        html_content += f"""
        <div style="page-break-inside: avoid; margin-bottom: 30px;">
            <div style="background-color: #4CAF50; color: white; padding: 15px; margin-bottom: 15px; border-radius: 5px;">
                <h2 style="margin: 0 0 10px 0; font-size: 18px;">Subject: {html_module.escape(str(subject.code))} - {html_module.escape(str(subject.name))}</h2>
                <p style="margin: 5px 0; font-size: 14px;"><strong>Batch:</strong> {batch_name} &nbsp;&nbsp; <strong>Evaluation Date:</strong> {date_str}</p>
            </div>
            
            <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #2c3e50; color: white;">
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Reg No</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Student Name</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: center;">Attendance %</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: center;">Internal Total</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: center;">External Total</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: center;">Combined Marks</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: center;">Grade</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Get internal marks breakdown for each evaluation
        for eval in evaluations:
            internal_marks_list = db.query(InternalMarks).filter(
                InternalMarks.evaluation_id == eval.id
            ).all()
            
            # Grade color coding
            grade_colors = {
                'O': '#28a745',
                'A+': '#17a2b8',
                'A': '#007bff',
                'B+': '#ffc107',
                'B': '#fd7e14',
                'U': '#dc3545',
                'SA': '#6c757d'
            }
            grade_color = grade_colors.get(eval.grade, '#000000')
            
            html_content += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">{html_module.escape(str(eval.student_ref.regno))}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{html_module.escape(str(eval.student_ref.name))}</td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{eval.attendance_percent:.2f}%</td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{eval.internal_total:.2f}</td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{eval.external_total:.2f}</td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{eval.combined_marks:.2f}</td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: {grade_color}; font-weight: bold;">{eval.grade}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </div>
        """
        
        # Full HTML document
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Grade Evaluation Report - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 15mm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    font-size: 12px;
                }}
                .header-section {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    margin-bottom: 30px;
                    border-radius: 5px;
                }}
                .header-section h1 {{
                    margin: 0 0 10px 0;
                    font-size: 24px;
                }}
                .header-section p {{
                    margin: 5px 0;
                    font-size: 14px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 30px;
                    page-break-inside: avoid;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #2c3e50;
                    color: white;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #ddd;
                    font-size: 10px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header-section">
                <h1>Grade Evaluation Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            {html_content}
            
            <div class="footer">
                <p>Report generated by Grade Manager System</p>
            </div>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        print(f"Error generating HTML report: {e}")
        import traceback
        traceback.print_exc()
        return "<html><body><h1>Error generating report</h1></body></html>"

