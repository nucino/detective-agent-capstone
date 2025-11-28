import gradio as gr
import asyncio
import os
import uuid
from typing import Optional
from dotenv import load_dotenv

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.apps.app import App, EventsCompactionConfig
from google.genai import types

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
import re

# Load environment
load_dotenv()

# A2A Server Configuration
SERVER_URL = os.getenv("DETECTIVE_SERVER_URL", "http://localhost:8001")

# Database URL for session persistence
DB_URL = "sqlite:///detective_web_sessions.db"

async def investigate_company_async(company_query: str, progress=gr.Progress()) -> tuple[str, str]:
    """
    Run investigation via A2A agent - Following complete.py pattern with DatabaseSessionService
    
    Returns:
        tuple: (markdown_report, status_message)
    """
    if not company_query or not company_query.strip():
        return "", "❌ Please enter a company name or query"
    
    try:
        progress(0, desc="🔌 Connecting to Detective Ed D....")
        
        # Create RemoteA2aAgent - Day 5A pattern
        remote_detective = RemoteA2aAgent(
            name="detective_agent",
            description="Remote financial detective agent that investigates companies",
            agent_card=f"{SERVER_URL}{AGENT_CARD_WELL_KNOWN_PATH}"
        )
        
        progress(0.1, desc="🕵️ Ed D. is starting the investigation...")
        
        # Create App with event compaction - following complete.py pattern
        detective_web_app = App(
            name="detective_web_app",
            root_agent=remote_detective,
            events_compaction_config=EventsCompactionConfig(
                compaction_interval=3,
                overlap_size=1,
            ),
        )
        
        progress(0.2, desc="💾 Setting up session with database persistence...")
        
        # Setup session management with DatabaseSessionService - complete.py pattern
        session_service = DatabaseSessionService(db_url=DB_URL)
        app_name = detective_web_app.name
        user_id = "web_user"
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # Create or get session - complete.py pattern with try/except
        try:
            session = await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        except:
            # Session already exists, get it
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        progress(0.3, desc="🔧 Configuring runner with event compaction...")
        
        # Create runner with App (not bare agent) - complete.py pattern
        runner = Runner(
            app=detective_web_app,
            session_service=session_service
        )
        
        progress(0.4, desc="🔍 Searching for company information...")
        
        # Enhance query like complete.py does
        if "investigate" not in company_query.lower():
            query = f"Investigate the financial health and leadership of {company_query}"
        else:
            query = company_query
        
        # Prepare message - complete.py pattern
        message = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )
        
        # Call remote agent via runner - collect responses
        full_response = []
        event_count = 0

        # Start time-based progress simulation
        import time
        start_time = time.time()
        progress_task = None

        async def simulate_progress():
            """Show progress based on elapsed time while waiting for response"""
            elapsed = 0
            while elapsed < 60:  # Max 60 seconds simulation
                await asyncio.sleep(2)  # Update every 2 seconds
                elapsed = time.time() - start_time
                # Progress from 0.4 to 0.9 over 60 seconds
                simulated_progress = min(0.9, 0.4 + (elapsed / 60) * 0.5)
                
                # Randomize detective activity messages for realism
                activities = [
                    "🔍 Searching company databases...",
                    "📊 Analyzing financial reports...",
                    "👔 Investigating leadership...",
                    "💰 Checking revenue trends...",
                    "🚩 Looking for red flags...",
                    "✅ Finding positive indicators...",
                    "📸 Locating CEO information...",
                    "🔎 Cross-referencing sources..."
                ]
                activity_idx = int(elapsed / 8) % len(activities)
                progress(simulated_progress, desc=f"{activities[activity_idx]} ({int(elapsed)}s)")

        # Start progress simulation in background
        progress_task = asyncio.create_task(simulate_progress())

        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=message,
            ):
                event_count += 1
                
                # Cancel progress simulation when first event arrives
                if progress_task and not progress_task.done():
                    progress_task.cancel()
                    try:
                        await progress_task
                    except asyncio.CancelledError:
                        pass
                
                # Jump to 95% when response arrives
                progress(0.95, desc="📝 Compiling final report...")
                
                # Extract text from various event formats
                text_content = None
                
                # Method 1: Check if it's a final response with content
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts'):
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_content = part.text
                                    break
                
                # Method 2: Check standard content.parts (intermediate events)
                elif hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text and part.text != "None":
                                text_content = part.text
                                break
                
                # Method 3: Check if event has direct text attribute
                elif hasattr(event, 'text') and event.text:
                    text_content = event.text
                
                # Add valid text to response
                if text_content and len(text_content.strip()) > 0:
                    full_response.append(text_content)

        finally:
            # Ensure progress simulation is cancelled
            if progress_task and not progress_task.done():
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass

        progress(1.0, desc="✅ Investigation complete!")
        
        print(f"[DEBUG] Total events processed: {event_count}")
        print(f"[DEBUG] Response parts collected: {len(full_response)}")
        
        # Join response
        final_report = ''.join(full_response)
        
        if not final_report or len(final_report.strip()) < 50:
            # Debug output
            debug_info = f"⚠️ Agent returned minimal response.\n\n"
            debug_info += f"**Debug Info:**\n"
            debug_info += f"- Events processed: {event_count}\n"
            debug_info += f"- Response parts: {len(full_response)}\n"
            debug_info += f"- Server URL: {SERVER_URL}\n"
            debug_info += f"- Session ID: {session_id}\n\n"
            debug_info += f"**Troubleshooting:**\n"
            debug_info += f"1. Check server terminal logs for errors\n"
            debug_info += f"2. Verify agent card: `curl {SERVER_URL}{AGENT_CARD_WELL_KNOWN_PATH}`\n"
            debug_info += f"3. Try a simpler query like 'Tesla'\n"
            debug_info += f"4. Check if Google Search API is working (server logs)\n\n"
            
            if full_response:
                debug_info += f"**Partial Response Captured:**\n```\n{final_report}\n```"
            
            return debug_info, "⚠️ Investigation incomplete - see debug info above"
        
        status = f"✅ Investigation complete! Session: {session_id} | Events: {event_count}"
        return final_report, status
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Error: {str(e)}\n\n"
        error_msg += f"**Traceback:**\n```\n{traceback.format_exc()}\n```\n\n"
        error_msg += f"**Troubleshooting:**\n"
        error_msg += f"1. Make sure the detective server is running:\n"
        error_msg += f"   `python remote_agent.py`\n"
        error_msg += f"2. Check server URL: {SERVER_URL}\n"
        error_msg += f"3. Verify agent card is accessible:\n"
        error_msg += f"   `curl {SERVER_URL}{AGENT_CARD_WELL_KNOWN_PATH}`\n"
        error_msg += f"4. Check database: {DB_URL}"
        return "", error_msg

def investigate_company(company_query: str, progress=gr.Progress()) -> tuple[str, str]:
    """
    Synchronous wrapper for async investigation with retry logic
    
    Automatically retries up to 3 times if investigation is incomplete.
    Uses exponential backoff: 2s, 4s, 8s between retries.
    """
    MAX_RETRIES = 3
    
    for attempt in range(1, MAX_RETRIES + 1):
        # Run investigation
        report, status = asyncio.run(investigate_company_async(company_query, progress))
        
        # Check if investigation was successful
        is_successful = (
            report and 
            len(report.strip()) >= 50 and 
            "⚠️" not in status and 
            "Investigation incomplete" not in status and
            "minimal response" not in status.lower()
        )
        
        if is_successful:
            # Success! Return immediately
            return report, status
        
        # Investigation failed or incomplete
        if attempt < MAX_RETRIES:
            # Not last attempt - retry with backoff
            wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
            
            if progress:
                progress(
                    0.3, 
                    desc=f"🔄 Investigation incomplete. Retrying ({attempt}/{MAX_RETRIES}) in {wait_time}s..."
                )
            
            print(f"[RETRY] Attempt {attempt} failed. Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}")
            print(f"[RETRY] Status was: {status[:100]}")
            
            import time
            time.sleep(wait_time)
            
            if progress:
                progress(0.35, desc=f"🔄 Retrying investigation (attempt {attempt + 1}/{MAX_RETRIES})...")
        else:
            # Last attempt failed - return with retry info
            print(f"[RETRY] All {MAX_RETRIES} attempts exhausted. Returning last result.")
            retry_msg = f"\n\n⚠️ **Note:** Investigation attempted {MAX_RETRIES} times but remained incomplete."
            return report, status + retry_msg
    
    # Should never reach here, but just in case
    return report, status

# Build Gradio interface - Ed D. detective theme
demo = gr.Blocks(title="Detective Agent - Ed D.")

with demo: 
    # Header with detective image banner
    from pathlib import Path
    SCRIPT_DIR = Path(__file__).parent
    detective_image_path = SCRIPT_DIR / "detective_sketch.png"
    
    # Load detective image as base64
    if detective_image_path.exists():
        import base64
        with open(detective_image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
       
    else:
        img_data = ""
       
    # Full HTML header - bypasses Gradio gr.image
    gr.HTML(f"""
        <div style="display: flex; align-items: flex-start; gap: 30px; padding: 20px; margin-bottom: 20px; width: 100%; background: transparent; border-radius: 10px;">
            <div style="flex-shrink: 0;">
                <img src="data:image/png;base64,{img_data}" 
                     alt="Detective Ed D." 
                     style="width: 200px; height: auto; border-radius: 8px; object-fit: contain;" />
            </div>
            <div style="flex-grow: 1; padding-top: 0px;">
                <h1 style="margin: 0 0 10px 0; font-family: 'Courier New', monospace; font-size: 2.86em; text-align: center;">
                    DETECTIVE AGENT - Ed D.
                </h1>
                <h3 style="margin: 60px 0 15px 0; font-family: Georgia, serif; font-style: italic; font-weight: normal; font-size: 1.56em;">
                    "I've been investigating companies since before the dot-com bubble..."
                </h3>
                <p style="margin: 0 0 15px 0; font-weight: bold; font-style: italic; font-size: 1.3em;">
                    40 Years of Financial Investigation Experience.
                </p>
                <p style="margin: 0 0 15px 0; font-weight: bold; font-style: italic; font-size: 1.3em;">
                    For educational purposes only, not financial advice.
                </p>
                <div style="margin: 15px 0 0 0; padding: 10px 15px; font-style: italic; font-size: 1.3em;">
                    "I've seen every trick in the book, kid. 
                    Now let's dig into the numbers and see what we're really dealing with here."
                </div>
            </div>
        </div>
    """)
    
    gr.Markdown("---")
    
    # Instructions
    gr.Markdown(
        """
        ## What Company Should I Investigate?
        
        Enter a company name below. I'll dig into their financials, leadership, and give you 
        my honest assessment. I've seen it all - boom cycles, crashes, frauds, 
        and comebacks. Let's see what we're dealing with here...
        
        💾 **Your sessions are saved to the database** - don't make me repeat myself!
        """
    )
    
    # Input section
    with gr.Row():
        with gr.Column(scale=4):
            company_input = gr.Textbox(
                label="🏢 Company or Investigation Query",
                placeholder="e.g., Tesla, Microsoft, OpenAI",
                lines=2,
                info="Be specific. I don't have all day."
            )
        with gr.Column(scale=1):
            investigate_btn = gr.Button(
                "🔍 Start Investigation", 
                variant="primary", 
                size="lg"
            )
    
    # Examples
    gr.Examples(
        examples=[
            ["Tesla"],
            ["Microsoft"],
            ["OpenAI"],
        ],
        inputs=company_input,
        label="📋 Quick Examples (Click to Use)"
    )
    
    # Status message
    status_output = gr.Textbox(
        label="📊 Investigation Status",
        interactive=False,
        show_label=True
    )
    
    # Output section
    gr.Markdown("## 📋 Investigation Report")
    gr.Markdown("Investigation report generated by Detective Agent Ed D.:")
    
    report_output = gr.Markdown(
        label="Detective's Report",
        show_label=False
    )
    
    # Download button - Initially disabled
    with gr.Row():
        download_btn = gr.DownloadButton(
            label="📥 Download Report as PDF",
            visible=True,
            interactive=False,  # Disabled initially
            variant="secondary",
            size="lg"
        )
        gr.Markdown(
            "*Button will be enabled after investigation completes*",
            elem_id="download-hint"
        )
      
    # Store report in state for PDF generation
    report_state = gr.State(value="")
    company_state = gr.State(value="")
    
    # Event handlers
    def handle_investigation(query: str, progress=gr.Progress()):
        """Handle investigation and enable download button if successful"""
        report, status = investigate_company(query, progress)
        
        # Check if investigation was successful
        if report and len(report.strip()) >= 50 and "⚠️" not in status:
            # Success - enable download button
            return report, status, report, query, gr.Button(interactive=True)
        else:
            # Failed - keep button disabled
            return report, status, "", "", gr.Button(interactive=False)
    
    def generate_pdf(report: str, company_query: str):
        """Generate PDF when download button is clicked"""
        if not report or len(report.strip()) < 50:
            return None
        
        try:
            # Create PDF filename with timestamp
            timestamp = uuid.uuid4().hex[:8]
            safe_query = "".join(c if c.isalnum() else "_" for c in company_query[:20])
            pdf_filename = f"investigation_{safe_query}_{timestamp}.pdf"
            
            # Save to same directory as local_agent.py
            pdf_path = os.path.join(os.path.dirname(__file__), pdf_filename)
            
            # Check if detective sketch exists
            sketch_path = os.path.join(
                os.path.dirname(__file__), 
                "detective_sketch.png"
            )
            if not os.path.exists(sketch_path):
                print(f"[WARN] Detective sketch not found at: {sketch_path}")
                sketch_path = None
            
            # Generate PDF with detective image
            markdown_to_pdf(report, pdf_path, sketch_path)
            
            print(f"[DEBUG] PDF generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"[ERROR] PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # Wire up the investigation button
    investigate_btn.click(
        fn=handle_investigation,
        inputs=[company_input],
        outputs=[report_output, status_output, report_state, company_state, download_btn]
    )
    
    # Wire up Enter key in text input
    company_input.submit(
        fn=handle_investigation,
        inputs=[company_input],
        outputs=[report_output, status_output, report_state, company_state, download_btn]
    )
    
    # Wire up download button to generate PDF on click
    download_btn.click(
        fn=generate_pdf,
        inputs=[report_state, company_state],
        outputs=download_btn
    )

def markdown_to_pdf(report_text: str, output_path: str, detective_sketch_path: str = None) -> str:
    """
    Convert markdown investigation report to PDF with detective theme
    
    Args:
        report_text: Markdown formatted investigation report
        output_path: Path to save PDF file
        detective_sketch_path: Optional path to detective sketch image
        
    Returns:
        Path to generated PDF file
    """
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for PDF elements
    story = []
    
    # Define styles - Film noir detective theme
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'DetectiveTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor("#817907"),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Courier-Bold'
    )
    
    # Heading styles
    h1_style = ParagraphStyle(
        'DetectiveH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#817907'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Courier-Bold',
        borderWidth=1,
        borderColor=HexColor('#636e72'),
        borderPadding=5
    )
    
    h2_style = ParagraphStyle(
        'DetectiveH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor("#0D5503"),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Courier-Bold'
    )
    
    # Red Flags special style - dark red color
    red_flags_style = ParagraphStyle(
        'RedFlagsH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#c0392b'),  # Dark red
        spaceAfter=10,
        spaceBefore=10,
        fontName='Courier-Bold'
    )
    
    # Body text style
    body_style = ParagraphStyle(
        'DetectiveBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=HexColor('#2d3436'),
        spaceAfter=8,
        fontName='Times-Roman',
        leading=16
    )
    
    # Add detective sketch if provided - CENTERED with better sizing
    if detective_sketch_path and os.path.exists(detective_sketch_path):
        try:
            # Load and resize image proportionally
            from PIL import Image as PILImage
            pil_img = PILImage.open(detective_sketch_path)
            
            # Calculate aspect ratio
            aspect = pil_img.width / pil_img.height
            
            # Set target dimensions (fits nicely in header)
            target_width = 2.5 * inch
            target_height = target_width / aspect
            
            # Create ReportLab image
            img = RLImage(detective_sketch_path, width=target_width, height=target_height)
            
            # Center the image
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
            
        except Exception as e:
            print(f"[WARN] Could not load detective image: {e}")
            pass  # Continue without image
    
    # Add title
    story.append(Paragraph("FINANCIAL INVESTIGATION REPORT", title_style))
    story.append(Paragraph("Detective Agent - Ed D.", body_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Helper function to remove emojis (reportlab can't render them)
    def remove_emojis(text):
        """Remove emoji characters that cause squares in PDF"""
        # Remove common emojis used in reports
        emoji_pattern = re.compile(
            "["
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub('', text).strip()
    
    # Parse markdown to structured text
    lines = report_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.1*inch))
            continue
        
        # H1 headers (# Header)
        if line.startswith('# '):
            text = line[2:].strip()
            # Remove emojis first
            text = remove_emojis(text)
            # Remove markdown bold/italic markers
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            if text:  # Only add if not empty after emoji removal
                story.append(Paragraph(text, h1_style))
        
        # H2 headers (## Header)
        elif line.startswith('## '):
            text = line[3:].strip()
            # Remove emojis first
            text = remove_emojis(text)
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            if text:  # Only add if not empty after emoji removal
                # Check if this is the Red Flags heading - use special dark red style
                if 'red flag' in text.lower():
                    story.append(Paragraph(text, red_flags_style))
                else:
                    story.append(Paragraph(text, h2_style))
        
        # H3 headers (### Header)
        elif line.startswith('### '):
            text = line[4:].strip()
            # Remove emojis first
            text = remove_emojis(text)
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            if text:  # Only add if not empty after emoji removal
                story.append(Paragraph(text, h2_style))
        
        # Bold text (**text**)
        elif '**' in line:
            text = remove_emojis(line)
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            # Handle image markdown ![alt](url)
            text = re.sub(r'!\[.*?\]\((.*?)\)', r'<i>Image: \1</i>', text)
            if text:  # Only add if not empty
                story.append(Paragraph(text, body_style))
        
        # List items (- item or * item)
        elif line.startswith('- ') or line.startswith('* '):
            text = '• ' + line[2:]
            text = remove_emojis(text)
          
            if text and text != '• ':  # Only add if has content
                story.append(Paragraph(text, body_style))
        
        # Regular paragraph
        else:
            text = remove_emojis(line)
            
            if text:  # Only add if not empty
                story.append(Paragraph(text, body_style))
    
    # Add footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#636e72'),
        alignment=TA_CENTER,
        fontName='Courier'
    )
    story.append(Paragraph("―" * 50, footer_style))
    story.append(Paragraph(
        "Generated by Detective Agent Ed D. | Powered by Google ADK & A2A Protocol",
        footer_style
    ))
    
    # Build PDF
    doc.build(story)
    return output_path

#----------------------------------------------------------------------------
    
if __name__ == "__main__":
    print("=" * 80)
    print("🌐 Detective Agent Web Interface - Ed D.")
    print("=" * 80)
    print(f"\n🔗 A2A Server: {SERVER_URL}")
    print(f"💾 Database: {DB_URL}")
    print("\n🚀 Starting Gradio interface at http://localhost:7860")
    print("💭 'Web interface ready. Let's get to work, kid...'\n")
    print("-" * 80 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        footer_links=[()],
    )