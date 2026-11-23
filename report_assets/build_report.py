from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
import shutil, subprocess, sys, re, textwrap

ROOT = Path(r"D:\cyberproject - Copy")
OUT = ROOT / "report_assets"
IMG = OUT / "images"
IMG.mkdir(parents=True, exist_ok=True)

# Preserve the user-provided evidence in the report's working folder.
evidence = {
    r"C:\Users\Lenovo\AppData\Local\Temp\codex-clipboard-d1da833c-7398-4c34-b003-79293b245e66.png": IMG / "example-dashboard.png",
    r"C:\Users\Lenovo\AppData\Local\Temp\codex-clipboard-e4d0a5d6-0e33-4f06-943b-7c538502f7cc.png": IMG / "signin-screen.png",
    r"C:\Users\Lenovo\AppData\Local\Temp\codex-clipboard-637100b8-3955-4381-8f57-ad5d13f2f746.png": IMG / "registration-screen.png",
    r"C:\Users\Lenovo\Downloads\surface-watch-example.com.pdf": IMG / "example-report.pdf",
    r"C:\Users\Lenovo\Downloads\surface-watch-neverssl.com.pdf": IMG / "neverssl-report.pdf",
}
for src, dst in evidence.items():
    if Path(src).exists():
        shutil.copy2(src, dst)

def font(size=24, bold=False):
    candidates = [r"C:\Windows\Fonts\times.ttf", r"C:\Windows\Fonts\arial.ttf"]
    if bold: candidates = [r"C:\Windows\Fonts\timesbd.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
    for f in candidates:
        if Path(f).exists(): return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def draw_box(draw, xy, label, fill="#F7F4EF", outline="#4B4034", fsize=22, radius=16):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=3)
    x1,y1,x2,y2=xy
    lines=label.split("\n")
    heights=[draw.textbbox((0,0),s,font=font(fsize,bold=True))[3] for s in lines]
    y=(y1+y2-sum(heights)-8*(len(lines)-1))/2
    for s,h in zip(lines,heights):
        box=draw.textbbox((0,0),s,font=font(fsize,bold=True)); w=box[2]-box[0]
        draw.text(((x1+x2-w)/2,y),s,font=font(fsize,bold=True),fill="#211B17")
        y += h+8

def arrow(draw, p1, p2, color="#D86A18", width=5):
    draw.line([p1,p2],fill=color,width=width)
    import math
    a=math.atan2(p2[1]-p1[1],p2[0]-p1[0]); size=17
    p3=(p2[0]-size*math.cos(a-.5),p2[1]-size*math.sin(a-.5))
    p4=(p2[0]-size*math.cos(a+.5),p2[1]-size*math.sin(a+.5))
    draw.polygon([p2,p3,p4],fill=color)

def diagram(name, title, boxes, links, width=1500, height=820):
    im=Image.new("RGB",(width,height),"white"); d=ImageDraw.Draw(im)
    d.text((width/2,35),title,font=font(34,True),fill="#29211A",anchor="ma")
    for b in boxes: draw_box(d,b["xy"],b["text"],b.get("fill","#F7F4EF"),fsize=b.get("size",21))
    for start,end in links: arrow(d,start,end)
    im.save(IMG/name,dpi=(180,180))

diagram("architecture.png","Surface Watch system architecture",[
 {"xy":(70,300,340,470),"text":"User in Chrome\nReact dashboard"},
 {"xy":(475,300,740,470),"text":"Express API\nAuthentication + scans"},
 {"xy":(880,115,1170,285),"text":"Scanner\nURL validation + GET"},
 {"xy":(880,520,1170,690),"text":"MongoDB\nUsers, sessions, scans"},
 {"xy":(1240,300,1460,470),"text":"Public target\nHTTP / HTTPS"}],
 [((340,385),(475,385)),((740,345),(880,240)),((740,425),(880,600)),((1170,200),(1240,345)),((1240,425),(1170,580))])

diagram("scan-flow.png","Bounded passive assessment flow",[
 {"xy":(60,300,280,450),"text":"Enter URL"},{"xy":(365,300,620,450),"text":"Parse scheme\nand hostname"},
 {"xy":(720,300,990,450),"text":"Resolve DNS; reject\nnon-public addresses"},
 {"xy":(1080,300,1370,450),"text":"Pinned HTTPS/HTTP\nGET (10 s / 512 KiB)"},
 {"xy":(1080,570,1370,720),"text":"Validate each redirect\n(maximum 3)"},
 {"xy":(720,570,990,720),"text":"Evaluate observed TLS,\nheaders and cookies"},
 {"xy":(365,570,620,720),"text":"Score, summarize,\nrecommend"},
 {"xy":(60,570,280,720),"text":"Save and display\nreport"}],
 [((280,375),(365,375)),((620,375),(720,375)),((990,375),(1080,375)),((1225,450),(1225,570)),((1080,645),(990,645)),((720,645),(620,645)),((365,645),(280,645))],height=850)

diagram("security-controls.png","Controls around the outbound request",[
 {"xy":(60,190,330,355),"text":"Input controls\nHTTP(S) only\nNo embedded credentials"},
 {"xy":(430,190,720,355),"text":"Resolution controls\nReject localhost/private\nRequire all answers public"},
 {"xy":(820,190,1110,355),"text":"Connection controls\nPin validated IP\nPreserve TLS verification"},
 {"xy":(1210,190,1460,355),"text":"Redirect controls\nRe-validate every hop\nStop after 3"},
 {"xy":(430,510,720,675),"text":"Resource controls\n10 s timeout\n512 KiB response cap"},
 {"xy":(820,510,1110,675),"text":"Method and scope\nSingle GET\nNo crawling or payloads"}],
 [((330,270),(430,270)),((720,270),(820,270)),((1110,270),(1210,270)),((1350,355),(1110,550)),((820,595),(720,595))])

diagram("data-model.png","Account and scan storage model",[
 {"xy":(150,220,570,570),"text":"User\nemail (unique)\npasswordHash\ncreatedAt / updatedAt"},
 {"xy":(930,160,1370,620),"text":"Per-user Scan\ntarget, finalUrl, host\nscannedAt, score, summary\nstatus, duration, redirects\nfindings[] and scopeNote"},
 {"xy":(40,620,480,760),"text":"MongoDB default DB\nUsers + sessions"},
 {"xy":(1000,650,1450,790),"text":"surface_user_<id>\nscans collection"}],
 [((570,390),(930,390)),((360,570),(260,620)),((1160,620),(1220,650))],height=900)

diagram("design-options.png","Three design alternatives considered",[
 {"xy":(90,250,500,540),"text":"A  Manual checklist\nHuman opens site and\nchecks headers by hand"},
 {"xy":(550,250,960,540),"text":"B  Active vulnerability\nscanner with crawling,\npayloads and probes"},
 {"xy":(1010,250,1410,540),"text":"C  Surface Watch\nOne safe bounded GET,\nconfiguration indicators"}],[],height=700)

# Summary figures use only the two user-supplied dated reports.
im=Image.new("RGB",(1500,850),"white"); d=ImageDraw.Draw(im)
d.text((750,45),"Observed score in supplied scan reports",font=font(34,True),fill="#29211A",anchor="ma")
for x,lab in [(390,"example.com"),(1070,"neverssl.com")]:
    d.ellipse((x-150,180,x+150,480),outline="#E9E2D8",width=30)
    d.arc((x-150,180,x+150,480),-90,118,fill="#E88926",width=30)
    d.text((x,305),"58",font=font(100,True),fill="#30271F",anchor="mm")
    d.text((x,525),lab,font=font(30,True),fill="#30271F",anchor="mm")
    d.text((x,580),"3 medium  |  4 low  |  1 info",font=font(23),fill="#51483F",anchor="mm")
d.text((750,730),"Both snapshots are bounded observations, not a measure of legitimacy or overall security.",font=font(24),fill="#51483F",anchor="mm")
im.save(IMG/"results-summary.png",dpi=(180,180))

im=Image.new("RGB",(1400,760),"white"); d=ImageDraw.Draw(im)
d.text((700,40),"Selected empirical studies in the review corpus",font=font(32,True),fill="#29211A",anchor="ma")
years=[("2017",1),("2018",2),("2021",1),("2023",1),("2024",1)]
base_y=600; max_h=350
for i,(yr,val) in enumerate(years):
    x=170+i*245; h=max_h*val/2
    d.rectangle((x,base_y-h,x+100,base_y),fill="#D86A18")
    d.text((x+50,base_y-h-42),str(val),font=font(24,True),fill="#29211A",anchor="mm")
    d.text((x+50,base_y+35),yr,font=font(24),fill="#51483F",anchor="mm")
d.text((700,710),"Purposive reading set only (n = 6 empirical studies)",font=font(22),fill="#51483F",anchor="mm")
im.save(IMG/"literature-year-profile.png",dpi=(180,180))

POPPLER=Path(r"C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe")
for stem in ("example-report","neverssl-report"):
    pdf=IMG/(stem+".pdf")
    if pdf.exists() and POPPLER.exists():
        subprocess.run([str(POPPLER),"-png","-r","105",str(pdf),str(IMG/stem)],check=False,capture_output=True)

DOC = Document()
sec=DOC.sections[0]
sec.page_width=Inches(8.27); sec.page_height=Inches(11.69)
sec.top_margin=Inches(.85); sec.bottom_margin=Inches(.8); sec.left_margin=Inches(1); sec.right_margin=Inches(1)
sec.header_distance=Inches(.35); sec.footer_distance=Inches(.35)

def set_font(style, size, bold=False, italic=False):
    style.font.name="Times New Roman"; style.font.size=Pt(size); style.font.bold=bold; style.font.italic=italic
    style._element.rPr.rFonts.set(qn("w:eastAsia"),"Times New Roman")
    style.font.color.rgb=RGBColor(0,0,0)

normal=DOC.styles["Normal"]; set_font(normal,12)
normal.paragraph_format.line_spacing=1.5; normal.paragraph_format.space_after=Pt(6)
normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
for name,size,align in [("Heading 1",16,WD_ALIGN_PARAGRAPH.CENTER),("Heading 2",14,WD_ALIGN_PARAGRAPH.LEFT),("Heading 3",12,WD_ALIGN_PARAGRAPH.LEFT)]:
    s=DOC.styles[name]; set_font(s,size,True); s.paragraph_format.alignment=align
    s.paragraph_format.space_before=Pt(10); s.paragraph_format.space_after=Pt(6); s.paragraph_format.keep_with_next=True
    s.paragraph_format.line_spacing=1.0
for style_name in ["Caption"]:
    st=DOC.styles[style_name]; set_font(st,10,True); st.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER; st.paragraph_format.line_spacing=1.0

def shade(cell, fill="E9E2D8"):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement("w:shd"); shd.set(qn("w:fill"),fill); tcPr.append(shd)
def repeat_header(row):
    trPr=row._tr.get_or_add_trPr(); el=OxmlElement("w:tblHeader"); el.set(qn("w:val"),"true"); trPr.append(el)
def set_cell_text(cell,text,bold=False,size=10):
    cell.text=""; p=cell.paragraphs[0]; p.paragraph_format.line_spacing=1.0; p.paragraph_format.space_after=Pt(2)
    r=p.add_run(str(text)); r.bold=bold; r.font.name="Times New Roman"; r.font.size=Pt(size)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
def add_table(headers, rows, widths=None, fontsize=10):
    global TABLE_COUNT
    TABLE_COUNT += 1
    label=CURRENT_HEADING or (headers[0] if headers else "Supporting data")
    cap_text=f"Table {TABLE_COUNT}: {label}"
    cp=DOC.add_paragraph(style="Caption"); cp.paragraph_format.keep_with_next=True; cp.add_run(cap_text)
    TABLE_CAPTIONS.append(cap_text)
    t=DOC.add_table(rows=1,cols=len(headers)); t.style="Table Grid"; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    repeat_header(t.rows[0])
    for i,h in enumerate(headers): set_cell_text(t.rows[0].cells[i],h,True,fontsize); shade(t.rows[0].cells[i])
    for row in rows:
        cells=t.add_row().cells
        for i,val in enumerate(row): set_cell_text(cells[i],val,False,fontsize)
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    DOC.add_paragraph()
    return t
def para(text, style=None, center=False, italic=False, boldlead=None):
    p=DOC.add_paragraph(style=style)
    if center: p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    if boldlead and text.startswith(boldlead):
        p.add_run(boldlead).bold=True; p.add_run(text[len(boldlead):])
    else:
        r=p.add_run(text); r.italic=italic
    return p
_NEXT_PAGE=False
CURRENT_HEADING="Front matter"
TABLE_COUNT=0
TABLE_CAPTIONS=[]
FIGURE_CAPTIONS=[]
def heading(text, level=2):
    global _NEXT_PAGE, CURRENT_HEADING
    p=DOC.add_heading(text,level)
    CURRENT_HEADING=text
    if _NEXT_PAGE:
        p.paragraph_format.page_break_before=True
        _NEXT_PAGE=False
    return p
def page():
    global _NEXT_PAGE
    _NEXT_PAGE=True
def caption(text):
    p=DOC.add_paragraph(style="Caption"); p.add_run(text); FIGURE_CAPTIONS.append(text); return p
def image(path, width=6.1):
    global _NEXT_PAGE
    p=DOC.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next=True
    if _NEXT_PAGE:
        p.paragraph_format.page_break_before=True
        _NEXT_PAGE=False
    p.add_run().add_picture(str(path),width=Inches(width)); return p
def chapter(number,title):
    global _NEXT_PAGE, CURRENT_HEADING
    p=DOC.add_paragraph(style="Heading 1"); p.add_run(f"CHAPTER {number}\n{title.upper()}")
    CURRENT_HEADING=f"Chapter {number} {title}"
    p.paragraph_format.keep_with_next=True
    if number != 1: p.paragraph_format.page_break_before=True
    _NEXT_PAGE=False
def sub(number,title,paras):
    heading(f"{number} {title}",2)
    for x in paras: para(x)
def sub3(title,paras):
    heading(title,3)
    for x in paras: para(x)
def bullet(text):
    p=DOC.add_paragraph(style="List Bullet"); p.paragraph_format.line_spacing=1.5; p.add_run(text)
def numbered(text):
    p=DOC.add_paragraph(style="List Number"); p.paragraph_format.line_spacing=1.5; p.add_run(text)
def page_field(p):
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(); fld=OxmlElement("w:fldSimple"); fld.set(qn("w:instr"),"PAGE"); r._r.addnext(fld)

def configure_section(section, roman=False, restart=None):
    section.page_width=Inches(8.27); section.page_height=Inches(11.69)
    section.top_margin=Inches(.85); section.bottom_margin=Inches(.8); section.left_margin=Inches(1); section.right_margin=Inches(1)
    section.header_distance=Inches(.35); section.footer_distance=Inches(.35)
    pg=section._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg=OxmlElement("w:pgNumType"); section._sectPr.append(pg)
    pg.set(qn("w:fmt"),"lowerRoman" if roman else "decimal")
    if restart is not None: pg.set(qn("w:start"),str(restart))
    section.footer.is_linked_to_previous=False
    p=section.footer.paragraphs[0]; p.text="Surface Watch | Project Report   |   "
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs: r.font.name="Times New Roman"; r.font.size=Pt(9)
    r=p.add_run(); fld=OxmlElement("w:fldSimple"); fld.set(qn("w:instr"),"PAGE"); r._r.addnext(fld)

# Cover and title pages
for _ in range(2):
    p=DOC.add_paragraph(); p.paragraph_format.space_before=Pt(72); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("CHANDIGARH UNIVERSITY"); r.bold=True; r.font.name="Times New Roman"; r.font.size=Pt(20)
    p=DOC.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(64)
    r=p.add_run("SURFACE WATCH"); r.bold=True; r.font.name="Times New Roman"; r.font.size=Pt(24)
    p=DOC.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("A Web Application Vulnerability Dashboard"); r.bold=True; r.font.name="Times New Roman"; r.font.size=Pt(18)
    p=DOC.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(55)
    p.add_run("A project report submitted in partial fulfilment of the requirements for the degree of\nBachelor of Engineering in Computer Science and Engineering").font.size=Pt(14)
    p=DOC.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(45)
    p.add_run("Submitted by\nAMAN KUMAR\nThird Year | Fifth Semester | Individual Project").font.size=Pt(14)
    p=DOC.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(40)
    p.add_run("Project Supervisors\nSanjeev Kumar\nJoban").font.size=Pt(14)
    p=DOC.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(35)
    p.add_run("Project period: 28 August 2026 to present\nNovember 2026").font.size=Pt(12)
    if _==0: page()

page(); heading("BONAFIDE CERTIFICATE",1)
para("This is to certify that the project report entitled “Surface Watch: A Web Application Vulnerability Dashboard” is a bona fide record of the project work carried out by Aman Kumar, Third Year, Fifth Semester, Bachelor of Engineering in Computer Science and Engineering, Chandigarh University, as an individual project during the period from 28 August 2026 to present.")
para("The work presented in this report is submitted in partial fulfilment of the academic requirements for the Bachelor of Engineering degree in Computer Science and Engineering. The report describes the design, implementation, and evaluation of a bounded passive website configuration assessment tool.")
DOC.add_paragraph("\n\n")
add_table(["Project Supervisor","Signature","Date"],[["Sanjeev Kumar\nDesignation: __________________","__________________","__________________"],["Joban\nDesignation: __________________","__________________","__________________"]],[2.7,1.6,1.6],11)
para("Department of Computer Science and Engineering\nChandigarh University\nInstitutional address: [To be completed by the student]",center=True)
para("This page is prepared for review and signature by the university supervisors.",italic=True,center=True)

page(); heading("ACKNOWLEDGEMENT",1)
for t in [
"I would like to express my sincere gratitude to my project supervisors, Sanjeev Kumar and Joban, for their guidance and support during the development of Surface Watch. Their direction helped me shape the project into a focused study of the information a public website returns at the HTTP and TLS boundary.",
"I am thankful to Chandigarh University and the Department of Computer Science and Engineering for providing the academic environment in which I could explore web security, software engineering, and responsible assessment practices. The project allowed me to connect classroom concepts with implementation decisions involving network requests, browser protections, authentication, persistence, and user experience.",
"I also acknowledge the maintainers of the open standards, technical documentation, and security guidance cited in this report. These resources informed the checks and limitations discussed here. I am grateful to the developers of React, Express, Node.js, MongoDB, Mongoose, Vite, and the other open-source libraries used by the application.",
"Finally, I thank my family and peers for their encouragement throughout this work. Any errors in the implementation or in this report remain my responsibility."
]: para(t)
para("Aman Kumar\nChandigarh University",center=True)

# Front matter with page fields and list headings
page(); heading("TABLE OF CONTENTS",1)
para("The report is arranged in the sequence prescribed by the supplied project report format. Page numbers are to be refreshed in Microsoft Word after the final pagination review.",italic=True)
toc=[
"Bonafide Certificate","Acknowledgement","Table of Contents","List of Figures","List of Tables","Abstract","Graphical Abstract","Abbreviations, Symbols and Nomenclature","Chapter 1  Introduction","Chapter 2  Literature Survey","Chapter 3  Design Flow and Process","Chapter 4  Results, Analysis and Validation","Chapter 5  Conclusion and Future Work","References","Appendix 1  User Manual","Appendix 2  Test Cases and Traceability","Appendix 3  Technical Reference and Selected Code","Appendix 4  Project Planning and Risk Register","Appendix 5  Rule Catalog and Interpretation Notes","Appendix 6  Operations and Maintenance Guide","Appendix 7  Original Scan Evidence","Appendix 8  Expanded Glossary","Appendix 9  Threat Model and Misuse Analysis","Appendix 10  Evaluation Framework and Score Examples","Achievements"]
for x in toc: para(x+" .......................................................... ______",style="List Bullet")

page(); heading("LIST OF FIGURES",1)
figures=["1.1 Project context and principal components","2.1 Selected empirical studies by year","3.1 Alternative project concepts","3.2 Client, API, scanner, database and target relationships","3.3 Outbound request safeguards","3.4 User and scan storage","3.5 Assessment algorithm","4.1 Supplied scan score summary","4.2 Example.com dashboard screenshot","A1.1 Sign-in screen","A1.2 Account creation screen","A1.3 Assessment dashboard","A7.1-A7.4 Original scan report pages"]
for x in figures: para(x+" .......................................................... ______")

page(); heading("LIST OF TABLES",1)
tables=["1.1 Objectives and evidence","1.2 Work packages","1.3 Project timeline","2.1 Web security policy milestones","2.2 Selected empirical studies by year","2.3 Assessment approach comparison","3.1 Functional requirements","3.2 Non-functional requirements","3.3 Design constraints","3.4 Alternative design decision matrix","3.5 Severity weights","3.6 Scan data model","4.1 Supplied scan metadata","4.2 Severity counts","4.3 Finding analysis","4.4 Validation test cases","A1.1 Operating requirements","A1.2 Troubleshooting","A2.1 Requirements traceability","A2.2 Network safety cases","A2.3 Rule tests","A2.4 Workflow tests","A3.1 Request limits","A3.2 Authentication properties","A3.3 API routes","A4.1 Risk register","A5.1 Rule outcomes","A6.1 Maintenance schedule","A9.1 Assets and trust boundaries","A9.2 Misuse cases","A10.1 Evaluation dimensions"]
for x in tables: para(x+" .......................................................... ______")

page(); heading("ABSTRACT",1)
para("Surface Watch is a web application that helps a user inspect a small set of browser-facing website security configuration signals. The system accepts a public HTTP or HTTPS URL, performs one bounded GET request, validates redirects and public DNS destinations, and summarizes transport, security header, cookie attribute, and server-header observations. It presents findings with severity labels, recommendations, a score, and a downloadable PDF report. Authenticated users can revisit recent scan reports stored in per-user MongoDB databases.")
para("The project was developed with React, Vite, Express, Node.js, Mongoose, and MongoDB. Its outbound request component restricts accepted protocols, rejects private and loopback destinations, validates every redirect, pins each request to a previously validated IP address, verifies TLS certificates, limits redirects to three, times out after ten seconds, and reads no more than 512 KiB. The assessment is passive: it does not crawl links, submit forms, inject payloads, attempt credentials, or exploit vulnerabilities.")
para("Two user-supplied assessment reports were used as an evidence sample: example.com and neverssl.com. Both recorded a score of 58/100 with eight observations: three medium, four low, and one informational. In both snapshots the connection returned HTTP 200 over HTTPS, the certificate was validated, and no redirects were recorded. The finding pattern was the same: missing clickjacking protection, Content Security Policy, HSTS, MIME-sniffing protection, Permissions-Policy, and Referrer-Policy, plus a disclosed Server header and validated HTTPS transport. The sample is descriptive and too small to support any general claim about website security.")
para("The project demonstrates how a focused, low-impact assessment can make selected configuration evidence understandable to a student or site operator. The score and findings are indicators of observed response configuration, not a determination that a website is legitimate, trustworthy, or free of vulnerabilities. A future version should improve score transparency, explain rule context, add a consent-focused workflow, expand validated checks, and provide stronger report versioning and test automation.")
para("Keywords: website security, HTTP headers, TLS, HSTS, CSP, cookies, passive assessment, SSRF prevention, React, Express.")

page(); heading("GRAPHICAL ABSTRACT",1)
image(IMG/"scan-flow.png",6.15); caption("Figure GA.1: User-submitted URL to bounded configuration report")
para("Surface Watch accepts a website URL and makes a single carefully constrained request. The response is converted into a short list of observed configuration signals, together with severity labels and remediation guidance. The application does not inspect every page or test exploitability. Its report helps the reader decide what to review next, while ownership and legitimacy require separate evidence.")

page(); heading("ABBREVIATIONS, SYMBOLS AND NOMENCLATURE",1)
add_table(["Term","Meaning"],[
("API","Application Programming Interface"),("CSP","Content Security Policy"),("CSS","Cascading Style Sheets"),("DNS","Domain Name System"),("GET","HTTP method used to retrieve a resource"),("HSTS","HTTP Strict Transport Security"),("HTML","HyperText Markup Language"),("HTTP","Hypertext Transfer Protocol"),("HTTPS","HTTP protected by TLS"),("IP","Internet Protocol"),("JSON","JavaScript Object Notation"),("JWT","JSON Web Token; not used by this implementation"),("MIME","Multipurpose Internet Mail Extensions"),("MongoDB","Document-oriented database used for accounts, sessions and scans"),("NFR","Non-functional requirement"),("OWASP","Open Worldwide Application Security Project"),("PII","Personally identifiable information"),("RBAC","Role-based access control"),("SSRF","Server-Side Request Forgery"),("TLS","Transport Layer Security"),("URL","Uniform Resource Locator"),("XFO","X-Frame-Options"),("XSS","Cross-Site Scripting")],[1.0,5.0],10)
para("Score S: score reported on a 0-100 scale. Finding count n: number of individual observations. Response cap: maximum number of response bytes retained for a scan. Request timeout: maximum time allowed for an outbound request.")

# Front matter uses lower-case Roman page numbering; chapters restart at Arabic 1.
front_section=DOC.sections[0]
configure_section(front_section,roman=True,restart=1)
front_section.different_first_page_header_footer=True
front_section.first_page_footer.paragraphs[0].text=""
main_section=DOC.add_section(WD_SECTION.NEW_PAGE)
configure_section(main_section,roman=False,restart=1)

# Chapter 1: context, need and objectives
chapter(1,"Introduction")
sub("1.1","Background",[
"A website is experienced through a sequence of network exchanges, but a visitor usually sees only the rendered page. The browser also receives transport-level information, HTTP status and response headers, cookie instructions, and a body. These elements influence how the browser connects to the service, handles content, and stores state. A small number of response configuration choices can therefore affect the protection available to users even when the page appears visually normal.",
"Transport security and browser security policy solve different parts of the problem. TLS protects the connection between endpoints and supports server authentication when the certificate is correctly validated. Headers such as Content-Security-Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy tell a supporting browser how to handle particular classes of content or navigation. Cookie attributes govern how session-related state is stored and returned. The benefits depend on correct deployment and on the site's application design; a header by itself does not prove that the application is safe [1-5].",
"Surface Watch was conceived as a compact dashboard for translating a subset of these response details into observations that a user can review. Its focus is intentionally narrow: the first response reached after a bounded, validated request. This makes the tool easier to understand and reduces operational impact, while also limiting what it can discover. It is best considered an educational configuration review and a prompt for follow-up, not a substitute for a full application security assessment."
])
sub("1.2","Identification of the user need",[
"The user need was described by the student as helping people avoid being scammed by checking whether a website is legitimate and okay. This is an important concern, but it is broader than the implemented technical checks. A security header scanner cannot establish the identity or honesty of an organization, confirm that a page is free from deceptive content, or prove that a domain has not been compromised. It can observe a limited set of configuration indicators on the returned response.",
"The report therefore frames the need as improving a visitor's awareness of selected website configuration signals. A visible score and plain-language recommendations can help the reader notice transport and browser-policy gaps that are otherwise hidden in response metadata. The user remains responsible for interpreting those indicators alongside independent checks such as domain ownership, contact information, payment practices, reputation, and the expected behavior of the service.",
"The intended user is a student, developer, or non-specialist who wants a first-pass view of a public page's edge configuration. The tool is also useful for a site operator who wants a quick reminder of common response controls. It is not designed for a security operations center, penetration tester, incident response team, or organization requiring evidence of regulatory compliance."
])
sub("1.3","Contemporary web security context",[
"The HTTP ecosystem has evolved from a simple request-response mechanism into a layered platform with many browser-enforced policies. The HTTP semantics specification defines requests, responses, methods, status codes, and fields, while TLS supplies a protected channel for application protocols [1,2]. HSTS allows a site to signal that browsers should use secure transport on later connections to that host, with deployment decisions such as subdomain scope and retention period requiring care [3].",
"Content Security Policy gives operators a mechanism to restrict the sources and behaviors from which a document can load or execute content. A policy is only useful when it matches the site's resource dependencies and is tested carefully. Framing restrictions can help mitigate clickjacking, but they are not a complete defense for every page or workflow. Cookie controls such as Secure and HttpOnly limit particular exposure paths, while SameSite expresses cross-site sending behavior; none of these attributes eliminates every session threat [4,5].",
"Measurement research shows why configuration checks can be useful and why they must be bounded. Large-scale studies compare deployments across many domains, while Surface Watch observes only a small number of individual URL responses. The results from a single endpoint cannot be extrapolated to a whole organization or to all pages within a domain. A homepage can use different headers from a login page, a static asset, an API route, or a checkout flow."
])
sub("1.4","Problem identification",[
"The central problem is that users have little visibility into response-level security configuration and may misinterpret the presence of HTTPS or a high score as proof of safety. Existing inspection workflows can require browser developer tools, command-line requests, specialist vocabulary, and manual interpretation. These barriers make it difficult for a learner or site owner to identify a limited number of common configuration conditions quickly.",
"A second problem is that a URL-fetching service introduces its own safety risks. If a backend accepts arbitrary URLs, an attacker may try to cause it to reach loopback services, private network hosts, cloud metadata endpoints, or destinations reached through redirects. DNS answers can change between validation and connection. A scanner must therefore treat its outbound network client as a security boundary and enforce scope before making a request.",
"The engineering problem addressed in this project is to design a small, authenticated web dashboard that performs a low-impact public-site request, produces understandable findings, and stores reports per account. The design must balance usefulness with operational restraint. It should communicate uncertainty, preserve user data boundaries, limit resource consumption, and avoid implying that passive indicators are a comprehensive vulnerability verdict."
])
sub("1.5","Problem statement",[
"How can a student-built web application provide a clear, low-impact review of selected HTTP response and transport configuration indicators for an explicitly entered public website, while preventing its request feature from reaching private destinations and clearly communicating the limits of the resulting score?",
"The answer implemented in Surface Watch is a one-request assessment pipeline. It accepts only HTTP and HTTPS, resolves and checks all destination addresses, rejects non-public destinations, pins outbound sockets to a checked address, rechecks every redirect, caps the response size and time, and evaluates a defined set of TLS, header, cookie, and disclosure rules. The resulting report is saved for the authenticated account and displayed with severity counts, score, facts, and recommendations.",
"The problem is intentionally not defined as detecting all vulnerabilities or verifying website legitimacy. Those broader objectives would require different evidence sources, active testing, identity verification, and a substantially different assurance model."
])
sub("1.6","Project aim",[
"The aim is to design and implement Surface Watch, a private web dashboard that presents a bounded passive assessment of selected browser-facing configuration signals on public websites. The project combines a React client, an Express API, an outbound request safety layer, deterministic response checks, report generation, account authentication, and per-user scan history.",
"The project also aims to demonstrate responsible assessment design. The scanner communicates its low-impact scope, does not crawl or inject test payloads, and provides remediation-oriented observations rather than exploit claims. A user can inspect the same report later and export it as a PDF."
])
sub("1.7","Goals and measurable objectives",[
"The objectives below translate the project aim into verifiable implementation outcomes. Each objective is tied to an observable artifact in the source code, interface, or scan evidence. The list is limited to functions present in the inspected project at report preparation time.",
"Success is defined as delivering an application that completes the selected workflow, safely rejects unsupported destinations, explains a defined set of findings, stores an authenticated user's reports separately, and exports a readable scan report. It does not require proof that the tool detects every vulnerability or that its users can identify fraudulent websites with certainty."
])
add_table(["ID","Objective","Evidence of completion"],[
("O1","Accept an HTTP or HTTPS URL from a signed-in user","URL input and POST /api/scans workflow"),
("O2","Restrict requests to globally routable public addresses","DNS checks, private-address rejection, socket pinning"),
("O3","Bound request work","10-second timeout, 512 KiB response cap, maximum three redirects"),
("O4","Observe TLS and selected response controls","Rule engine checks transport, headers, cookies, Server and X-Powered-By"),
("O5","Present actionable findings","Severity, detail, recommendation, score and summary"),
("O6","Keep account history private","Authenticated routes and account-specific scan database naming"),
("O7","Export scan evidence","Client-side A4 PDF exporter with findings and scope note"),
("O8","Evaluate with supplied examples","Two user-provided scan reports for example.com and neverssl.com")],[.55,2.55,3.1],9)
sub("1.8","Scope and boundaries",[
"In scope are account registration and login, a single website assessment request, response-header and cookie checks, certificate-validation status as observed by the HTTPS client, redirect tracking, response facts, severity scoring, scan history, and PDF export. The scanner reads a limited response body only to extract an HTML title and does not parse links or execute scripts.",
"Out of scope are crawling, form submission, authentication attempts against target websites, payload injection, exploit validation, directory enumeration, port scanning, subdomain discovery, JavaScript analysis, source-map discovery, dependency scanning, certificate-chain reporting beyond the successful validation signal, TLS cipher enumeration, DNSSEC review, phishing detection, reputation checks, business identity verification, and monitoring over time.",
"The project is intended for public sites the user owns or is authorized to assess. Its server binds to loopback for local operation. The backend can only assess a response returned from the requested URL and followed redirect chain under its safety checks. The report's scope note travels with the PDF to remind later readers what the scan did and did not do."
])
sub("1.9","Stakeholders and intended use",[
"The primary stakeholder is the student developer, who needs a complete academic description of design choices and results. The direct application user is an authenticated person who enters a public URL and wants to understand selected configuration signals. A website administrator may use the report as a prompt to review edge settings, but should independently verify each recommendation against the site's architecture and resource requirements.",
"Other stakeholders include a course supervisor reviewing the design, a maintainer responsible for the application, and a person whose website is assessed. The latter has an interest in predictable request volume and accurate presentation of findings. A single GET is less intrusive than crawling or payload testing, but the scanner should still be used only within a clear authorization boundary.",
"The interface presents findings as observed properties of one response. It avoids wording such as “safe,” “legitimate,” or “verified trustworthy.” The score label “Surface Score” summarizes the project's rule weights; it does not express a statistically validated probability of compromise."
])
sub("1.10","Task identification and deliverables",[
"Work was divided into requirements definition, literature review, design selection, implementation, result capture, report preparation, and user documentation. The source tree separates the browser interface, Express server, scanner orchestration, request safety logic, rule evaluation, account model, and scan model. This decomposition makes the central network behavior and the report rule set easier to examine independently.",
"The main software deliverable is the Surface Watch application. Academic deliverables include this report, two sample scan reports, screenshots of sign-in, registration, and assessment screens, an implementation and validation narrative, a user manual, requirements traceability, limitations, and future work. The report records that supervisor signatures and academic designations remain for institutional completion."
])
add_table(["Work package","Tasks","Deliverable"],[
("WP1 Requirements","User need, scope, acceptance criteria","Requirements and objective matrix"),
("WP2 Research","Standards and empirical studies","Literature review and research gap"),
("WP3 Design","Alternatives, architecture, request safety","Design diagrams and decision matrix"),
("WP4 Implementation","UI, authentication, scanner, scoring, history, export","React/Express application"),
("WP5 Evaluation","Two supplied reports, expected-result comparison","Results and limitations"),
("WP6 Reporting","Write, format, user manual, evidence appendices","A4 project report")],[1.25,2.75,2.2],9)
sub("1.11","Project timeline",[
"The project start date supplied by the student is 28 August 2026. The report was prepared during the ongoing project period in November 2026. Because exact phase start and end dates were not supplied, the schedule below is a month-level reconstruction of the work sequence implied by the available implementation and evidence. It is not a timesheet or a claim that every task started on a specific day.",
"The implementation source and exported reports show that a working end-to-end path exists: account entry, target submission, report generation, visual display, persistence, and PDF export. The next project period can focus on supervisor review, broader test coverage, usability improvements, and polishing the final documentation."
])
add_table(["Period","Focus","Status in this report"],[
("28 Aug 2026","Project start","Student-provided date"),
("Sep 2026","Need definition, scope, basic interface and architecture","Reconstructed sequence; exact dates unavailable"),
("Oct 2026","Scanner, rule engine, authentication, persistence and PDF export","Implementation visible in source"),
("1 Nov 2026","Sample report captures for example.com and neverssl.com","Evidence provided by student"),
("Nov 2026 onward","Validation, supervisor feedback, refinements and final submission","Ongoing")],[1.1,2.9,2.2],9)
sub("1.12","Organization of the report",[
"Chapter 1 defines the context, user need, scope, objectives, stakeholders, tasks, and timeline. Chapter 2 reviews web security policy standards and measurement studies, then identifies the narrow gap addressed by a bounded student project. Chapter 3 explains the alternative concepts, requirements, design constraints, architecture, request algorithm, rules, scoring, data storage, and implementation plan.",
"Chapter 4 documents the technologies used and analyzes the two supplied scan reports, screenshots, and validation approach. Chapter 5 states the conclusions, limitations, deviations from the wider user need, and future work. The appendices provide a step-by-step user manual, test cases and traceability, selected implementation notes, and a project risk register."
])
image(IMG/"architecture.png",6.2); caption("Figure 1.1: Project context and principal components")

# Chapter 2 literature
chapter(2,"Literature Survey")
sub("2.1","Review method and research questions",[
"The literature review uses standards and primary research publications concerning transport security, security response headers, cookie attributes, and automated web measurement. Standards explain the intended behavior of protocol features; measurement studies report what researchers observed in sampled populations; implementation guidance translates those mechanisms into operational recommendations. These evidence types answer different questions and are not combined as if they were interchangeable.",
"The review was organized around four questions: (1) which browser-facing controls are relevant to a passive response audit; (2) what have researchers measured about the adoption and consistency of those controls; (3) what methodological constraints apply to automated website measurements; and (4) what small project contribution can be made without claiming comprehensive vulnerability detection?",
"The selected corpus is purposive and illustrative rather than exhaustive. It contains a small group of publicly identifiable standards and empirical studies, chosen for direct relevance to HTTP headers, TLS, cookies, safe measurement, and security verification. The descriptive bibliometric summaries in this chapter describe only that selected corpus. They are not a systematic review of all web security publications and do not estimate the global research output."
])
sub("2.2","Historical development of relevant controls",[
"HTTP cookies became a widely used mechanism for maintaining state across otherwise independent requests. RFC 6265 describes the Set-Cookie and Cookie fields and the behavior of attributes such as Secure and HttpOnly [4]. Later work and evolving browser behavior have added policy semantics such as SameSite; implementers should check current browser and standards guidance when choosing values.",
"HSTS was standardized in RFC 6797 in 2012. It describes how a host announces a policy over secure transport and how a user agent can upgrade future requests to HTTPS. HSTS is a transport enforcement mechanism and is explicitly not a way to identify fraudulent sites or malware [3].",
"CSP emerged as a way for a web document to express restrictions on resource loading and execution. The policy's effectiveness depends on its directives, sources, delivery, browser support, and the site's content model. Frame-ancestors can express framing restrictions. The practical deployment challenge is reflected in research on CSP correctness and maintenance [5,6].",
"Over the following decade, researchers moved from describing individual headers toward measuring adoption, configuration errors, and inconsistencies across many sites or pages. This research emphasizes that a check at one URL can miss configuration differences elsewhere and that superficially present policies may still be weak or inconsistent [7-10]."
])
sub("2.3","Timeline of the reported problem",[
"The underlying problem has several layers. First, web applications expose responses containing both application data and metadata. Second, browser vendors added mechanisms that let operators influence how browsers handle transport, scripts, framing, referrers, and device capabilities. Third, the number and interaction of controls grew, creating a need for measurement. Finally, usability efforts attempted to convert technical observations into scores, but scoring can conceal important differences among checks.",
"Surface Watch sits at the end of this timeline as a narrow educational tool. It does not reproduce large-scale measurement research. It applies a local rule set to a single response and presents the result in a dashboard. The strongest connection to the literature is methodological: clear scope, bounded request behavior, explicit limitations, and repeatable rule definitions are essential to interpreting a scan."
])
add_table(["Year","Milestone","Relevance"],[
("1990s-2000s","HTTP deployments expand; cookies become common state mechanism","Application state creates confidentiality and session handling considerations"),
("2011","RFC 6265 standardizes HTTP cookie field behavior","Provides basis for checking selected response cookie attributes"),
("2012","RFC 6797 defines HSTS","Explains secure-transport policy and why HSTS matters after HTTPS"),
("2017-2018","Empirical work measures header adoption across large site samples","Shows how automated response sampling can describe deployment patterns"),
("2021","Research studies inconsistencies in CSP, HSTS and cookie policy deployment","Highlights that page-level response checks do not establish origin-wide consistency"),
("2023","Longitudinal CSP implementation study examines policy bugs and fixes","Shows maintenance and correctness challenges beyond simple presence checks"),
("2024 onward","New measurement work continues to examine security headers","Reinforces need to date samples and avoid treating old results as current global truth"),
("2026 project period","Surface Watch conducts two one-response student assessments","Applies a bounded local rule set to two test destinations")],[.8,2.7,2.7],9)
sub("2.4","Transport security and certificate validation",[
"TLS is designed to provide a protected communication channel and to authenticate the server endpoint under the applicable certificate validation rules. The current TLS 1.3 specification is RFC 9846, published in July 2026; it supersedes RFC 8446 while retaining the TLS 1.3 version number [2]. Surface Watch delegates the TLS handshake and certificate verification to Node.js HTTPS and sets certificate rejection on. Its positive finding means the connection completed with verification enabled, not that the destination's business identity has been proven to the user.",
"HSTS addresses the browser's later transport behavior. A browser that has accepted a site's HSTS policy upgrades future insecure references to secure transport and treats secure-transport errors strictly. The policy is delivered over an already secure response, and its max-age and subdomain applicability require careful operational planning [3]. The current scanner reports HSTS missing when it is absent on an HTTPS response, but does not validate its syntax, duration, preload status, or behavior across subdomains.",
"HTTP status is separate from transport security. HTTP 200 indicates that the GET request succeeded at the protocol level according to the responding endpoint; it is not an assurance statement about content quality, organizational identity, or freedom from deceptive behavior [1]. In the two supplied reports, both responses returned status 200, but the assessment still surfaced missing browser-facing protections."
])
sub("2.5","Content Security Policy and framing protection",[
"CSP lets a site define policy for resources and browser behaviors. A restrictive policy can reduce some exploit opportunities when an application has injection weaknesses, but creating a policy requires understanding the page's legitimate resource dependencies. A policy that is too permissive may add little protection; a policy that is too strict may break the application. Presence-only assessment is therefore a first signal, not a quality evaluation.",
"Frame-ancestors expresses which origins may embed a document, while X-Frame-Options provides a legacy framing control. OWASP guidance recommends using frame-ancestors where suitable and warns that control effectiveness depends on the type of response and browser behavior [11]. Surface Watch flags the absence of both a recognized X-Frame-Options header and the CSP frame-ancestors directive. It does not visit a frame context to confirm actual behavior.",
"The literature also emphasizes consistency. If policies vary across pages within an origin, users may receive different protection depending on which path is loaded. A scanner that samples a single URL cannot measure this variation. A broader assessment would need a defined endpoint set, authorization, crawling rules, and careful treatment of pages that require authentication."
])
sub("2.6","Cookie attributes and session state",[
"The Secure attribute restricts the circumstances in which a user agent sends a cookie, and HttpOnly prevents access through non-HTTP script APIs under the defined browser behavior. These attributes are independent, so a sensitive session cookie may require both. SameSite controls whether a browser sends a cookie with cross-site requests according to its mode and context. Cookie security remains dependent on the application's session design, token lifecycle, CSRF defenses, and deployment boundary [4,11].",
"The Surface Watch rule engine reads Set-Cookie response values and checks for the presence of Secure on HTTPS responses, HttpOnly on all observed cookies, and SameSite. It does not determine whether a cookie is a session identifier, whether a cookie truly needs script access, whether Path or Domain is overbroad, whether expiry is appropriate, or whether the authentication flow is robust. The recommendation must therefore be reviewed in application context.",
"Neither supplied test PDF reports cookie findings. The appropriate interpretation is that the scan did not observe a Set-Cookie value that triggered the implemented checks in the sampled response. It is not evidence that every page, subdomain, or subsequent workflow on either site uses safe cookies."
])
sub("2.7","Information disclosure and auxiliary headers",[
"Server and X-Powered-By response fields may reveal implementation details. Removing unnecessary detail can modestly reduce low-effort fingerprinting, but these fields are not a direct vulnerability and other observable behavior may still identify a technology stack. OWASP treats them as disclosure considerations rather than a substitute for patching or secure configuration [11].",
"Referrer-Policy governs how much referrer information a browser includes in outgoing requests. Permissions-Policy lets a response control access to selected browser features. X-Content-Type-Options: nosniff helps prevent MIME type reinterpretation in supported contexts. These controls are sensitive to resource type, browser behavior, and application requirements; a missing header should prompt a contextual review rather than a blind copy of a generic policy.",
"The rule engine reports only whether the named field is present. It does not parse all directive values. For CSP, it checks only for the existence of the header and separately searches the value for frame-ancestors when no X-Frame-Options is observed. This simple rule can produce false reassurance when a policy is syntactically invalid or permissive."
])
sub("2.8","Empirical research on header adoption",[
"Buchanan, Helme, and Woodward analyzed adoption of selected security headers in a large website sample and examined use of CSP, HSTS, X-Frame-Options, and related controls [7]. Lavrenovs and Melón analyzed response headers for domains in a top-one-million list, following redirects and comparing HTTP and HTTPS behavior [8]. Such work demonstrates how automated response sampling can characterize deployment at scale, but its dataset, timing, request pattern, and interpretation determine what the results mean.",
"Calzavara and coauthors studied inconsistencies in site security policy across pages and found that policies may be deployed unevenly across origins and sites [9]. Their results are especially relevant to Surface Watch because they show why a single landing-page response cannot stand in for all routes. Franken and colleagues examined the lifecycle of CSP implementation bugs and fixes, emphasizing that even important policies require ongoing maintenance [6].",
"A 2024 preprint by Kishnani and Das analyzes HTTP security headers across a sample of popular global websites and reports widespread weaknesses [12]. As a preprint, it should be treated as emerging evidence rather than as an established peer-reviewed consensus. Together, these works support the use of careful response measurement while cautioning against universal conclusions from a narrow sample."
])
sub("2.9","Bibliometric profile of the selected empirical corpus",[
"A compact descriptive mapping was prepared from six selected empirical studies that directly examine HTTP security headers, transport-policy adoption, policy inconsistency, or CSP maintenance. This corpus was selected for topical relevance and identifiable metadata; it is not the result of a database-wide query with a reproducible systematic search protocol. The counts below therefore describe this report's selected reading set only.",
"The selected studies span 2017 to 2024. Two fall in 2018, one in 2017, one in 2021, one in 2023, and one in 2024. The emphasis is on measurement of deployed websites rather than formal usability research or exploit demonstrations. This small chronological profile illustrates that the field has sustained interest in adoption and consistency, while recent work also studies maintenance and policy quality.",
"Because the corpus is small and purposive, citation counts, author network measures, geographic collaboration metrics, and keyword co-occurrence analyses would be misleading here. The report uses a transparent year-by-year count and topic coding only. A true bibliometric study would require a defined database, search string, date range, inclusion criteria, deduplication method, and exported metadata."
])
add_table(["Publication year","Selected empirical studies","Count"],[
("2017","Exploring HTTP header manipulation in the wild","1"),
("2018","Security-header adoption; top-one-million analysis","2"),
("2021","Inconsistency analysis of site policies","1"),
("2023","Longitudinal CSP bug lifecycle study","1"),
("2024","Analysis of headers in popular global sites (preprint)","1"),
("Total","Purposively selected empirical works","6")],[1.1,4.5,.6],9)
image(IMG/"literature-year-profile.png",6.1); caption("Figure 2.1: Descriptive count of selected empirical studies by year (n=6)")
sub("2.10","Comparison of related assessment approaches",[
"Research scanners commonly make many requests, sample broad domain populations, or compare endpoint behavior over time. Commercial and open-source vulnerability scanners may crawl, probe, or test application behavior. These methods answer questions that a passive single-request dashboard cannot answer, but they carry different operational cost and authorization requirements.",
"Surface Watch deliberately selects a smaller design point. It provides a quick explanatory report for one URL, with explicit limits and deterministic rules. The tradeoff is less coverage and weaker assurance. The product's value is not that it replaces broader approaches; it is that it makes a small set of edge observations accessible and repeatable for an individual user."
])
add_table(["Approach","Strength","Limit relative to Surface Watch"],[
("Manual browser inspection","Context-sensitive; can inspect rendered behavior","Requires technical skill and repeatable note-taking"),
("Large-scale header measurement","Describes adoption patterns across a population","Not tailored to an individual user's question; sampling changes over time"),
("Active vulnerability scanner","Can test behaviors and exploitability across many paths","Higher traffic and authorization needs; may affect targets"),
("Surface Watch passive check","Simple, bounded, human-readable, stores results","One response only; limited checks; no legitimacy or exploit proof")],[1.55,2.3,2.35],9)
sub("2.11","Research synthesis and project gap",[
"The standards establish what selected mechanisms are intended to do. Empirical studies show that deployment can be uneven, inconsistent, or difficult to maintain. Security guidance helps translate mechanisms into implementation advice, while verification standards provide a broader assurance framework. Together they show that a useful first-pass tool should expose observations plainly, explain each rule, and avoid suggesting that presence or absence alone settles application security.",
"The practical gap addressed by Surface Watch is educational presentation of a small, bounded response review, together with controls that prevent the URL-fetching feature from reaching private destinations. The project combines these two ideas in one local dashboard: safety of measurement and accessibility of interpretation. The gap is modest by design and is appropriate for an individual student project.",
"The project does not introduce a new security standard, novel vulnerability detection method, global measurement corpus, or validated risk score. Its contribution is a functioning end-to-end prototype, a transparent rule set, an explicit request boundary, and evidence from two supplied sample scans."
])
sub("2.12","Problem definition",[
"Given a user-entered public URL, return a concise report about a predefined set of observable configuration indicators while ensuring that the application makes at most one bounded request per redirect hop, rejects private destinations, and communicates that the findings are incomplete indicators rather than a trust verdict.",
"The problem decomposes into target validation, network safety, response acquisition, rule evaluation, severity and score calculation, user presentation, private report storage, export, and user education. Failure at any stage should prevent an unsafe or misleading report from being presented as a successful scan."
])
sub("2.13","Goals, objectives and research questions",[
"The literature informs three evaluation questions. RQ1: Can the implementation complete the expected low-impact workflow for an accepted public URL and return a report with stable fields? RQ2: Does the request layer encode safeguards against common server-side request abuse, including private-address destinations and redirect escape? RQ3: Do the supplied reports show that the dashboard can summarize a real HTTP response into findings and recommendations that are understandable to the user?",
"The present evidence supports a descriptive answer only. The source code shows the request and rule logic. The two supplied PDF reports show successful results for the recorded URLs and times. They do not demonstrate exhaustive correctness, cross-browser behavior, resistance to every SSRF bypass, or user comprehension in a controlled study."
])

# Chapter 3 design
chapter(3,"Design Flow and Process")
sub("3.1","Concept generation",[
"Three design concepts were considered. A manual checklist would avoid building a network service but would require the user to find and interpret response metadata independently. An active scanner could discover more behavior, but would introduce crawling and probing risks beyond the project's educational objective. A passive one-request dashboard offers an intermediate design: it automates a narrow set of checks while constraining its outbound behavior.",
"The selected concept uses a browser interface for account access and scan review, an authenticated API for target submission, a dedicated fetch layer that validates destinations and redirects, a deterministic report builder, a per-user storage model, and a client-side PDF exporter. This modular approach keeps safety checks close to the network request and keeps the rules readable in a separate module.",
"Concept generation prioritized user comprehension, low target impact, manageable implementation effort, and demonstrable safeguards. The objective was not to maximize the number of scan rules. Adding checks without corresponding explanation, scope boundaries, and validation would make the dashboard look broader than its evidence supports."
])
image(IMG/"design-options.png",6.15); caption("Figure 3.1: Three alternative project concepts")
sub("3.2","Evaluation and selection of design alternatives",[
"A weighted decision matrix was used as a design aid. The scores are engineering judgments on a five-point scale, with five representing stronger fit. The weights emphasize user value, safety, and feasibility because the project is an individual academic build with a limited assessment scope. The matrix makes the design tradeoff explicit instead of treating the selected solution as inevitable.",
"The passive dashboard scores well on safety and feasibility while providing more usability than a manual checklist. The active scanner could achieve broader coverage, but its increased impact, authorization burden, and validation complexity make it a poor fit for this project's requirements. The manual approach is low-risk but offers limited automation and weak reproducibility."
])
add_table(["Criterion","Weight","Manual checklist","Active scanner","Passive dashboard"],[
("User accessibility","20%","2","4","5"),("Target impact","25%","5","1","5"),("Implementation feasibility","20%","5","2","4"),("Repeatability","15%","2","4","4"),("Coverage depth","10%","1","5","2"),("Scope clarity","10%","4","2","5"),("Weighted score / 5","100%","3.35","2.80","4.40")],[1.85,.8,1.2,1.2,1.35],9)
para("Decision matrix method: weighted total = sum of (criterion weight × alternative rating). Ratings are qualitative engineering judgments for this project and were not produced by a user survey or formal expert panel.",italic=True)
sub("3.3","Functional requirements",[
"Functional requirements describe visible behavior that can be checked through the application flow. Authentication gates scan history and scan submission. The API validates the target length and format before calling the scanner. The request module controls outbound activity. The report builder creates the fields consumed by the React dashboard and the PDF exporter.",
"The requirements are intentionally traceable to code modules. This makes it possible to identify which functions have direct evidence and which would need additional implementation. No requirement claims that the scanner can detect all vulnerability classes or verify the legitimacy of a website."
])
add_table(["ID","Requirement","Priority","Implementation location"],[
("FR-01","Register using a valid email and password of at least 10 characters","Must","server/server.js; AuthScreen"),
("FR-02","Hash the password before persisting the account","Must","bcryptjs hash with cost 12"),
("FR-03","Sign in and establish a regenerated server session","Must","/api/auth/login; establishSession"),
("FR-04","Submit a URL for one assessment","Must","POST /api/scans; scanner.js"),
("FR-05","Reject unsupported protocols, credentials and private targets","Must","scanner/request.js"),
("FR-06","Evaluate transport, selected headers, cookies and disclosure headers","Must","scanner/report.js"),
("FR-07","Show score, counts, response facts and recommendations","Must","src/App.jsx"),
("FR-08","Keep recent account scan history and reopen reports","Must","models/Scan.js; GET /api/scans"),
("FR-09","Export report in A4 PDF format","Should","src/exportPdf.js"),
("FR-10","Sign out and clear current client state","Must","/api/auth/logout; signOut")],[.65,2.55,.65,1.95],8)
sub("3.4","Non-functional requirements",[
"Non-functional requirements guide performance, security, privacy, usability, maintainability, and portability. The implementation has measurable bounds for outbound request time and body size. It uses a focused set of modules and schemas. The following requirements describe both implemented behavior and areas where additional evidence is needed.",
"The application should provide readable feedback, preserve report ownership by account, and keep configuration secrets outside source control. The user manual directs operators to use a private environment file for database credentials and a strong session secret. A deployment should also consider HTTPS termination, secure cookie configuration, monitoring, backup, and database least privilege."
])
add_table(["Quality attribute","Target or principle","Evidence / qualification"],[
("Performance","Bound a target request to 10 seconds","Request timeout is explicit; end-to-end user latency varies"),
("Resource use","Retain at most 512 KiB of response body","Implemented in fetchPage response handler"),
("Availability","Show a recoverable message when the API is unavailable","Client catches API failures; hosting availability not evaluated"),
("Security","Protect outbound request boundary and account routes","Several safeguards present; independent security audit not performed"),
("Privacy","Keep account histories separated by per-user DB name","Access control code inspected; multi-tenant penetration test not performed"),
("Usability","Present severity, detail and recommendation in one report","Screenshots demonstrate presentation; formal usability study not performed"),
("Maintainability","Separate request, report, server, and UI responsibilities","Modular source files"),
("Portability","Build with Node.js 20+ and browser client","README documents local and production commands")],[1.25,2.55,2.0],8)
sub("3.5","Design constraints and regulations",[
"Economic constraints include the cost and availability of a MongoDB Atlas instance, hosting resources, and development time. The application is a student project with a modest scope, so it uses a conventional web stack and a small rule engine rather than commercial scanning infrastructure. The report does not estimate operational costs because no deployment scale or billing data was supplied.",
"Environmental constraints are primarily resource use. A single GET with a body cap and timeout consumes less target and scanner capacity than broad crawling, although actual impact depends on the target's response behavior and network path. The design avoids repeated requests within a scan and records duration for transparent reporting.",
"Health and safety concerns include safe use of assessment tools and avoidance of unauthorized probing. Professional and ethical practice requires permission, minimal impact, truthful reporting, and care not to publish sensitive findings. The scanner displays a public-target scope and the README advises using only authorized sites. The project provides no mechanism to verify the user's authorization; this remains an operational and governance requirement.",
"Legal requirements vary by jurisdiction and by the target's terms and network policy. The report therefore does not offer legal advice or claim that a public target is automatically available for testing. The safe-use boundary is to assess only systems the user owns or is authorized to assess. The UI and report should keep this condition visible.",
"Political and social considerations arise because security labels can influence trust decisions. A low score could wrongly discourage use of a legitimate service, while a high score could create false confidence. The product must avoid trust verdict wording and explain that the score covers a small set of response indicators."
])
add_table(["Constraint or issue","Design response","Remaining limitation"],[
("Unauthorized target activity","One GET; explicit authorized-use guidance","User authorization is not technically verified"),
("Private-network reachability","Reject non-public addresses; pin socket; revalidate redirects","Requires continued review as IP handling evolves"),
("Misleading security verdict","Use “surface score” and scope note","Users may still overinterpret numeric scores"),
("Operational resource use","Timeout, response cap, redirect cap","No global scan rate limit at the scan route is shown"),
("Data privacy","Authentication and user-specific scan databases","Database permissions and backups remain deployment risks"),
("Accessibility","Semantic labels, keyboard history activation and text findings","Formal WCAG audit not performed")],[1.45,2.5,1.85],8)
sub("3.6","Selected architecture",[
"The user interacts with a React single-page application built with Vite. The Express server exposes health, authentication, and scan endpoints. Session middleware uses a MongoDB-backed store. Authenticated scan requests pass into scanTarget, which coordinates fetching and report construction. The scan schema is stored in a database derived from the user ID. The browser renders the report and builds a downloadable A4 PDF using jsPDF.",
"The architecture separates public-facing presentation from target acquisition and evaluation. The request layer validates hostnames and redirects and pins the selected address to the outbound socket. The report module evaluates only the response values it is given. This separation makes the implementation easier to reason about, but the absence of a formal unit-test suite means rule behavior should be tested before any production reliance.",
"The server binds to 127.0.0.1 and serves the built application in production. Local development uses Vite and a watched Express process. The server requires MONGODB_URI to start, while the sample environment file's first comment states that scans still run without it; that text conflicts with the actual startup guard. This discrepancy should be corrected before a clean installation is documented."
])
image(IMG/"architecture.png",6.2); caption("Figure 3.2: Client, API, scanner, database and target relationships")
sub("3.7","Request acquisition and destination validation",[
"The fetch layer begins by parsing the requested URL. It accepts only HTTP and HTTPS, rejects embedded username or password credentials, requires a hostname, and explicitly blocks localhost names. For a literal IP address it parses the address directly; otherwise it resolves DNS with all answers returned. It rejects the target if any resolved address is not globally routable according to the IP classification library.",
"After validation, the scanner selects an IPv4 address when available and supplies a custom lookup callback so the request connects to the validated address. TLS certificate verification remains enabled and the requested hostname is used for server name indication. This reduces the chance that the socket will resolve again to an unintended address after the safety check. OWASP's SSRF guidance similarly emphasizes validating all resolved addresses and ensuring the HTTP client connects only to a validated destination [13].",
"When the response is a supported redirect, the destination is resolved and validated again before the next request. The scanner follows no more than three redirects. This prevents a public URL from redirecting the backend to a private destination without rechecking it. The outgoing request uses GET, a fixed user agent, and an Accept header. The client stops after the timeout or response-body cap.",
"These measures reduce risk but do not constitute a full formal proof against every parser edge case, IPv6 representation, proxy behavior, or future dependency change. The implementation should be reviewed whenever URL parsing, IP classification, Node.js networking, or redirect handling changes. A network-level egress policy can provide an additional layer of defense."
])
image(IMG/"security-controls.png",6.15); caption("Figure 3.3: Request safeguards applied before and during outbound activity")
sub("3.8","Response analysis and rule engine",[
"The report builder receives the original target, final URL, normalized response headers, response body, and status code. It determines whether the final URL is HTTPS. HTTPS produces an informational certificate-validated observation because the request completed with verification enabled; HTTP produces a high-severity HTTPS-not-enabled observation. The checks then evaluate missing CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, clickjacking controls, and HSTS for HTTPS pages.",
"For each Set-Cookie response value, the rule engine derives the cookie name and parses attribute names. On HTTPS it reports a missing Secure attribute; for all cookies it reports missing HttpOnly or SameSite. Server and X-Powered-By fields generate low-severity information-disclosure findings. If the content type contains HTML, the scanner extracts a bounded page title from the already-capped body.",
"The findings are sorted by severity and then category and title. Severity weights reduce a starting score of 100: critical 35 points, high 20, medium 10, low 3, and info 0. A floor of zero prevents negative scores. The score is deterministic for the finding set but has not been calibrated against real-world incidents, exploitability, or expert risk assessment."
])
sub("3.9","Scoring and severity design",[
"A simple weighted deduction model was chosen because it is easy to explain and reproduce. Let n_c, n_h, n_m, n_l, and n_i be the number of critical, high, medium, low, and informational findings. The score is max(0, 100 - 35n_c - 20n_h - 10n_m - 3n_l - 0n_i). The user interface maps scores of at least 80 to Strong, 55 through 79 to Needs attention, and below 55 to At risk.",
"For the two supplied reports, the score is 100 - (3 × 10) - (4 × 3) = 58. The one informational certificate observation has zero deduction. Both reports therefore receive the same numeric score and severity counts. This calculation is internally consistent with the rules shown in the source code and the values in the exported PDFs.",
"The model has limitations. A missing low-level header is assigned the same three-point deduction regardless of page function. Multiple findings can accumulate for one underlying configuration decision. The score can remain high even when an important scenario is outside the rules. A score is not a probability, grade from an independent standard, or guarantee. Future versions should consider grouping related observations, adding rule rationale, and documenting every weight with a validation method."
])
add_table(["Severity","Deduction","Example implemented observation","Interpretation"],[
("Critical","35","No critical rule currently defined","Highest score impact if a future rule is added"),
("High","20","HTTPS is not enabled","Significant transport configuration concern"),
("Medium","10","Missing CSP, HSTS, clickjacking control, or cookie attribute","Requires review; context and deployment matter"),
("Low","3","Missing referrer, MIME-sniffing, or permissions policy; server disclosure","Lower-priority configuration signal"),
("Info","0","HTTPS certificate validated","Positive observation; no deduction")],[.85,.8,2.75,1.4],9)
sub("3.10","Data model and persistence",[
"The User schema contains a unique lowercase trimmed email and a passwordHash that is excluded from normal query selection. Registration hashes passwords using bcrypt with a work factor of 12. Passwords must be at least ten characters and no more than 72 UTF-8 bytes. The authentication route is rate-limited to ten attempts per fifteen-minute window using standard rate-limit headers.",
"A scan record stores the original target, final URL, host, timestamp, duration, status code, content type, page title, redirects, score, findings, summary, and scope note. Each account's scan model is bound to a database named surface_user_<user-id>, using a scans collection. Sessions are persisted in the default database through connect-mongo. These design choices separate scan history by user in the database topology and require the database account to have permissions to create and read/write these per-user databases.",
"The scan endpoint returns the current report after storing it. The history endpoint returns at most the 30 most recent reports. Existing pre-account scan records in the former shared collection are not automatically migrated, as stated in the README. The project does not describe a deletion/export privacy workflow, retention policy, backup schedule, or database encryption configuration; these should be designed before a public deployment."
])
image(IMG/"data-model.png",6.1); caption("Figure 3.4: User records, sessions and per-user scan storage")
sub("3.11","Authentication and session design",[
"The client checks the current session through /api/auth/me before showing the application. Registration and login submit credentials as JSON. On successful authentication the server regenerates the session identifier, records the user ID, and saves the session. Protected routes look up the user before continuing. Logout destroys the session and clears the cookie.",
"The session cookie is HTTP-only and SameSite=Lax. Secure is enabled when NODE_ENV is production, and the session lifetime is seven days. The session secret is read from the environment; if omitted in development, a random secret is generated at process startup. Production startup rejects a missing secret. A secret generated at runtime changes after restart and is unsuitable for reliable persistent sessions, so deployments must set a strong stable secret.",
"The code shows several prudent account controls, but the report does not claim a complete authentication review. The same-site cookie attribute is useful but does not replace CSRF analysis. A production review should confirm HTTPS at the application boundary, reverse-proxy trust settings, session expiration and invalidation, account enumeration behavior, password recovery requirements, rate-limit behavior across deployment instances, and database least privilege."
])
sub("3.12","Interface and report design",[
"The interface uses a dark visual theme with an orange accent, a persistent identity bar, an account state indicator, a prominent URL field, a score ring, severity cards, a donut chart, response facts, and a findings list. Each finding contains severity, category, explanatory detail, and a recommendation. The interface sorts findings by the same severity order as the report builder.",
"The history table displays host, scan time, score, high-priority count, medium count, and a navigation affordance. The user can select a previous report, rescan the current target, export a PDF, or sign out. If a scan has no findings, the interface includes a statement that the absence of configured checks returning a finding is not a guarantee of security.",
"The exported PDF uses A4 dimensions and includes the site, score, severity counts, scan time, response status, duration, redirect count, findings, recommendations, and scope note. It is a two-page report for the two supplied targets. The academic report supplements it with context and methodology rather than presenting the PDF as a full security assessment."
])
sub("3.13","Project implementation plan and flow",[
"Implementation follows a dependency-aware sequence. Requirements and scope precede the request boundary because the scanning behavior determines risk. The report schema is defined before the dashboard because the UI renders its fields. Persistence and authentication are integrated after the scan flow is defined. The result evidence is captured only after the reporting path is usable.",
"The project can be managed as an iterative build: implement a vertical slice, verify the endpoint and display, add safety constraints, connect persistence, refine the interface, and capture result evidence. Each change to the request code should be followed by a targeted review of redirect handling, destination classification, timeout, size cap, and failure behavior."
])
image(IMG/"scan-flow.png",6.15); caption("Figure 3.5: Implementation and assessment algorithm")
add_table(["Phase","Key tasks","Exit evidence"],[
("1. Define","Need, scope, user, acceptance criteria","Requirements matrix approved for project"),
("2. Design","Alternatives, architecture, rules, schema","Design diagrams and rationale"),
("3. Build core","URL validation, fetch, redirects, response cap","Source review and safe request behavior"),
("4. Build product","Auth, report UI, history, PDF export","End-to-end workflow visible"),
("5. Evaluate","Known test URLs, expected findings, output capture","Two exported reports and screenshot"),
("6. Refine","Supervisor feedback, documentation, fixes","Final reviewed report and application")],[1.0,2.8,2.0],9)
sub("3.14","Testing strategy designed for the project",[
"A test strategy should separate pure rule tests from network safety tests and user workflow tests. Pure rule tests can construct response objects with known headers and assert exact findings, ordering, summaries, and scores. Request tests can use controlled local fixtures to verify that unsupported protocols, private IPs, credential-bearing URLs, redirect loops, excessive redirects, slow responses, and oversized bodies are rejected or bounded.",
"End-to-end tests can verify registration, login, scan submission, history isolation, report reopening, and PDF export. They should use a controlled local test server or authorized test domains and must not issue unsolicited requests to arbitrary third-party sites. The provided repository does not include a test script or test files, so the formal suite described here is a recommended validation plan rather than evidence of tests already run.",
"The two supplied PDF reports provide output-level evidence for two successful HTTPS GET requests. They do not validate negative cases, rule unit behavior, authentication isolation, failure handling, or PDF rendering across multiple viewers. The report keeps this distinction visible in the results chapter."
])

# Chapter 4: implementation, results and validation
chapter(4,"Results Analysis and Validation")
sub("4.1","Implementation environment and engineering tools",[
"The inspected project uses React 19 and React DOM for the browser interface, Vite 6 for local development and production bundling, Express 4 for the API, Node.js for server-side request handling, Mongoose 8 for MongoDB models, connect-mongo for session storage, bcryptjs for password hashing, express-rate-limit for authentication throttling, ipaddr.js for address classification, and jsPDF for client-side report export. Lucide React supplies interface icons.",
"The architecture is represented in source modules rather than in a separate modeling tool. The request and report logic are split into server/scanner/request.js and server/scanner/report.js, with server/scanner.js coordinating them. Authentication and route handling reside in server/server.js. User and scan schemas are in models/User.js and models/Scan.js. The React workflow is implemented in src/App.jsx, styling in src/styles.css, and PDF generation in src/exportPdf.js.",
"The project README specifies Node.js 20 or newer, installation with npm, a MongoDB Atlas connection string, a stable SESSION_SECRET, a Vite development workflow, and a production build. This report does not claim a specific operating-system build was executed during evaluation; the code and supplied browser screenshots are the evidence sources used here."
])
sub("4.2","Implemented workflow",[
"A visitor first sees the sign-in page, with a switch to account registration. Registration validates an email and password length before sending credentials to the API. The server applies an authentication rate limiter, hashes the password, creates a unique account, creates a user scan collection, and establishes a regenerated session. A signed-in user is shown a URL field and recent assessment history.",
"When the user submits a URL, the browser sends JSON to the authenticated scan endpoint. The server checks the URL length, invokes scanTarget, stores the resulting report in the user's scan database, and returns the saved record. The interface refreshes history, sets the report state, and scrolls the assessment into view. A previous report can be opened from the history table. The user can export the visible report in A4 PDF or sign out.",
"The flow is synchronous from the user's perspective. The interface displays an assessing state while the network operation completes and shows an error banner if the endpoint rejects the target or cannot be reached. The API binds to loopback and the local development setup uses Vite's URL. A production deployment must place the application behind an appropriate HTTPS boundary and configure secure environment variables."
])
sub("4.3","Results capture protocol",[
"The results in this chapter come from two user-supplied PDF exports and one dashboard screenshot for example.com. The NeverSSL result is documented in a separate PDF export. The timestamps were recorded by the application on 1 November 2026. The assessment reports show the final URL, score, severity counts, HTTP status, request duration, redirect count, page title where present, findings, recommendations, and scope note.",
"The two target names are used only to identify the supplied snapshots. This report does not assert that the targets were owned or authorized by the student; the ethical requirement remains that scans must be run only against systems the user owns or has permission to assess. This academic analysis does not repeat the requests or independently verify that the sites still return the same responses.",
"The sample size is n=2. The targets are not a random or representative sample of the web. No population-level inference, ranking of domain safety, statistical confidence interval, or causal conclusion is made. The scan dates and measured durations are treated as properties of those specific requests."
])
add_table(["Target","Report time shown","Final URL","HTTP","Duration","Redirects","Score"],[
("example.com","1 Nov 2026, 2:43:03 PM","https://example.com/","200","60 ms","0","58/100"),
("neverssl.com","1 Nov 2026, 1:44:27 PM","https://neverssl.com/","200","4071 ms","0","58/100")],[1.05,1.45,1.5,.55,.7,.7,.75],8)
sub("4.4","Summary of measured results",[
"Both supplied reports show a surface score of 58/100 and eight findings. Each report has zero critical findings, zero high findings, three medium findings, four low findings, and one informational finding. The score can be reproduced directly from the implemented weights: three medium deductions of ten points each and four low deductions of three points each reduce 100 to 58. The informational transport observation has no penalty.",
"The responses were reached over HTTPS, returned status 200, and had zero recorded redirects. The HTTPS certificate validation observation appears in the report, indicating that the Node.js HTTPS request completed with certificate verification enabled. This does not verify company identity, content authenticity, or page safety.",
"Both reports show the same set of six missing protection headers plus Server disclosure and a certificate-valid informational observation. No cookie findings are listed. Based on the scanner's rule set, this means no observed Set-Cookie value triggered the implemented attribute checks in those response snapshots. It should not be generalized to other routes or later responses."
])
add_table(["Severity","example.com","neverssl.com","Interpretation"],[
("Critical","0","0","No critical rule triggered in either report"),
("High","0","0","HTTPS was enabled in the observed final response"),
("Medium","3","3","Clickjacking protection, CSP and HSTS missing"),
("Low","4","4","Three auxiliary header controls and Server disclosure"),
("Info","1","1","Certificate validation completed over HTTPS"),
("Total","8","8","Same count and pattern in the two snapshots")],[1.0,1.1,1.1,2.7],9)
image(IMG/"results-summary.png",6.2); caption("Figure 4.1: Surface scores and finding summaries from the two supplied reports")

sub("4.5","Detailed finding analysis",[
"The first medium observation is missing clickjacking protection. The response did not include X-Frame-Options and did not include a CSP frame-ancestors directive. The scanner recommends setting one of these controls. A site operator should check whether the page is intentionally embeddable and choose a policy consistent with its product flow; a blanket denial can break legitimate integrations.",
"The second medium observation is missing Content Security Policy. The response did not include content-security-policy. CSP can mitigate some injection consequences when a suitable policy is deployed, but the scanner does not test the page for cross-site scripting or grade policy directives. The finding reflects absence only and should not be interpreted as evidence that an exploit exists.",
"The third medium observation is missing HSTS on an HTTPS response. HSTS helps a browser remember an HTTPS-only policy for the host after a secure response, but its duration and subdomain scope require operational review. Both supplied tests were HTTPS; the finding indicates that the response snapshot lacked Strict-Transport-Security.",
"Low findings include missing X-Content-Type-Options, Referrer-Policy, and Permissions-Policy. Each is a browser-facing control with specific behavior and context. The recommendation is to set an explicit suitable policy, but the owner should account for actual application requirements and resource behavior.",
"The fourth low finding is exposed Server header. This may disclose a software identifier, although a header alone does not show that the software is vulnerable. Removing or minimizing the field may reduce easy fingerprinting but does not replace patch management or other secure deployment practices.",
"The informational finding is HTTPS certificate validated. It is positive evidence about this request's TLS handshake and certificate verification setting. It is not a claim that the domain's operator is honest, that the site content is benign, or that the endpoint is free from security defects."
])
add_table(["Finding","Severity","Observed evidence","Recommended operator review"],[
("Clickjacking protection is missing","Medium","No X-Frame-Options or frame-ancestors observed","Decide whether framing is needed; set a matching policy"),
("Content Security Policy is missing","Medium","No Content-Security-Policy response field","Develop and test an application-specific policy"),
("HSTS is missing","Medium","No Strict-Transport-Security on HTTPS response","Confirm HTTPS coverage, then plan max-age and subdomains"),
("MIME-sniffing protection is missing","Low","No X-Content-Type-Options","Review content types and set nosniff where suitable"),
("Referrer-Policy is missing","Low","No Referrer-Policy","Select a privacy-appropriate referrer policy"),
("Permissions-Policy is missing","Low","No Permissions-Policy","Disable unneeded browser features carefully"),
("Server header is exposed","Low","Server response field present","Remove or reduce unnecessary implementation detail"),
("HTTPS certificate validated","Info","HTTPS handshake completed with validation on","Keep certificate lifecycle and HTTPS coverage monitored")],[1.55,.55,1.75,2.1],8)
sub("4.6","example.com dashboard evidence",[
"The dashboard screenshot for example.com shows the latest assessment heading, final HTTPS URL, scan time, score ring, severity summary cards, donut chart, response status, duration, redirects, page title, and the beginning of the findings list. It shows a score of 58 and eight observations across three categories. The screenshot is a cropped viewport, so the complete findings are taken from the accompanying two-page exported PDF rather than inferred from the visible portion.",
"The visual hierarchy gives prominence to the score and to critical/high counts, then provides a scan-specific list. The first visible row identifies the missing clickjacking protection as a medium HTTP-header finding. This layout supports quick triage, although the score label and green/amber palette should remain carefully explained to avoid a trust certification interpretation.",
"The user-provided screenshot includes the example.com URL and scan timestamp. It does not expose a password or account secret. For a formal submission, the student may wish to replace the sample email displayed in the authentication screenshots with a neutral dummy address if the academic reviewer considers it personal information."
])
image(IMG/"example-dashboard.png",6.25); caption("Figure 4.2: Surface Watch assessment dashboard for example.com, as supplied")

sub("4.7","PDF report inspection",[
"The exported reports use a two-page layout. Page one presents the site, score, category counts, scan metadata, and the first four findings. Page two contains the remaining findings and the passive-scope note. This separation keeps recommendation text legible and includes the count of findings and the response metadata on the first page.",
"The example.com PDF and the neverssl.com PDF record identical scores and finding sets but different response times. This is a useful demonstration that the tool's score is driven by the finding set, not by latency. Duration is reported as a measurement fact and is not a scoring input.",
"The PDF exporter is implemented in the browser and creates an A4 document with a footer and page numbering. Its layout code checks vertical space before writing findings, which allows long reports to continue onto additional pages. The supplied exports appear as two pages and include all eight findings."
])
sub("4.8","Validation against expected behavior",[
"The available validation is evidence review rather than an executed automated test suite. The source implementation was compared with the values serialized in the two supplied PDFs. The scores, counts, metadata, and finding names are internally consistent with the code's rule table and deduction weights. This cross-check supports the conclusion that the outputs reflect the intended current rule set.",
"A stronger validation should use fixture responses with known headers and cookies. For each fixture, the expected findings should be specified in advance and compared to the built report. Network-boundary cases should be tested with a controlled local harness so that no request is sent to a third-party service. User-flow tests should confirm authentication gating and cross-account history isolation.",
"The table below distinguishes evidence already available from cases that require additional test work. It avoids labeling unexecuted checks as passed. The supplied PDF results demonstrate successful HTTPS request paths for two targets; they do not verify rejection behavior or performance under extreme conditions."
])
add_table(["Test ID","Scenario","Expected result","Evidence status"],[
("T-01","HTTPS response with certificate verification succeeds","Informational transport finding; final report created","Observed in both supplied reports"),
("T-02","HTTP response without HTTPS","High transport finding","Source rule inspected; no supplied report"),
("T-03","Missing CSP and framing policy","Medium missing-policy findings","Observed in both supplied reports"),
("T-04","Cookie without Secure/HttpOnly/SameSite","Corresponding findings when conditions apply","Source rule inspected; no supplied cookie case"),
("T-05","Target resolves to loopback/private address","Reject before outbound request","Source guard inspected; no execution evidence"),
("T-06","Redirect to private address","Revalidate and reject redirect target","Source flow inspected; no execution evidence"),
("T-07","Slow response exceeds timeout","Terminate request and show error","Source timeout inspected; no execution evidence"),
("T-08","Response exceeds 512 KiB","Stop reading after cap","Source handler inspected; no execution evidence"),
("T-09","Unauthenticated scan/history API request","Return sign-in required","Source route guard inspected; no execution evidence"),
("T-10","User exports report","A4 PDF contains metadata, findings and scope note","Two supplied PDFs inspected")],[.55,1.7,2.1,1.55],8)

sub("4.9","Data validity, repeatability and interpretation",[
"The primary output is a snapshot of response data observed at a particular time through one request path. The result depends on DNS answers, network routing, TLS negotiation, the requested hostname, redirect chain, server/CDN response, geolocation, user agent, and time. A subsequent request may observe different headers or a different backend.",
"The two reports are internally consistent and provide a repeatable description of their recorded outcomes. However, independent repeatability would require rescans under documented conditions and comparison of raw response fields, not just score values. Since raw header dumps are not included in the PDF, an auditor cannot independently reconstruct every normalized header from the exported evidence.",
"The PDFs display the findings and recommendations but not the complete Set-Cookie values or all response headers. This is a privacy-conscious choice, yet it limits reproducibility. A future export could add an optional sanitized evidence appendix that records only the header names and normalized check outcomes needed to support each finding."
])
sub("4.10","Interpretation of the two-site sample",[
"Both sites received a score of 58. This does not mean that the sites have identical overall security, operational maturity, or risk. It means that the current rules emitted the same number and severities of findings for the two captured URL responses. Other security controls or pages may differ substantially.",
"The response durations differ markedly: 60 milliseconds for example.com and 4071 milliseconds for neverssl.com. A single latency observation is sensitive to network and server variation and is not a performance benchmark. The dashboard reports duration as context only and does not include it in the score.",
"The sample contains two test destinations, so no estimate can be made about the fraction of websites missing a given header. The number of findings should not be compared with large-scale research studies without aligning their date, population, URL selection, redirect behavior, rule definitions, and measurement method."
])
sub("4.11","Project management and communication",[
"The project is an individual build, so planning and traceability are important. The work packages and timeline connect the stated objective to the implemented modules and available artifacts. The architecture diagram communicates data movement; the finding table explains what the scanner observed; the user manual instructs a student or operator how to use the local application.",
"Communication choices include consistent naming for severity levels, a concise recommendation per finding, the scope note in the report, and explanations of what the score does not mean. The supplied screenshots support user-facing communication by showing sign-in, registration, and the assessment view. A future usability session with representative users could measure whether they understand the difference between configuration observations and website legitimacy.",
"The report is structured for supervisor review. The bonafide certificate includes spaces for signatures, designations, dates, and institutional address completion. These administrative fields must be completed by the student and institution; they are not inferred from code or from the supplied format."
])
sub("4.12","Implementation observations and limitations",[
"The scan pipeline and response rule set are clearly separated, and the outbound request code contains multiple defensive checks. The account system uses password hashing, session regeneration, a persistent session store, and protected scan routes. The application provides a coherent workflow from authentication through export.",
"The score weights are fixed constants and are not backed by empirical calibration. The scan endpoint has no scan-specific rate limit visible in the inspected server file, although each request is time- and size-bounded. Only 30 reports are returned in history, and no in-app deletion mechanism was observed. The history data is separated by user database names, making MongoDB permissions and model selection important.",
"The sample environment file labels MongoDB as optional for temporary scans, but the current server startup code requires MONGODB_URI and exits when it is missing. This inconsistency affects the accuracy of setup instructions. Before distributing the project, either the server should support a documented temporary-storage mode or the sample configuration comment should state that MongoDB is required.",
"The assessment does not evaluate target-side content, JavaScript behavior, form security, authentication, software dependencies, TLS versions or ciphers, DNS configuration, certificate expiry dates, or application logic. These gaps are a direct consequence of the selected bounded scope and should be stated near any generated score."
])
sub("4.13","Validation summary",[
"The available evidence supports a narrow conclusion: Surface Watch can produce a report for two HTTPS test destinations and the displayed results match the implemented severity model. Both reports include a clear scope note, a bounded-request statement, recommendations, and response metadata. The user-provided interface screenshot aligns with the PDF report for example.com.",
"The available evidence does not support a claim that all security rules are correct, that private-network requests are blocked under every possible input encoding, or that the application has passed a security review. Those claims require repeatable automated and manual tests. The next validation phase should focus on request safety, session isolation, score explanation, malformed responses, and accessibility."
])

# Chapter 5 conclusion
chapter(5,"Conclusion and Future Work")
sub("5.1","Conclusion",[
"Surface Watch implements a focused web dashboard for presenting selected website transport and response configuration signals. It combines an authenticated React interface, an Express API, a bounded network fetcher, a deterministic finding engine, per-user scan storage, report history, and a client-side PDF export. The implementation uses one GET request per redirect hop and includes controls intended to reduce SSRF risk and resource consumption.",
"The two user-supplied scan reports show the same score of 58/100 and the same eight findings for example.com and neverssl.com. The responses returned HTTP 200 over HTTPS, the certificate validation completed, and no redirects were recorded. The missing policies and Server disclosure are useful prompts for an operator to review. The findings do not establish that the sites are fraudulent or vulnerable, and the successful certificate validation does not prove that the sites are legitimate.",
"The project meets its narrow objective of making a limited set of response observations visible and exportable. It only partially addresses the broader user need to avoid scams. Determining whether a site is legitimate requires additional signals and user guidance beyond what this scanner implements. This distinction is central to responsible interpretation of the dashboard."
])
sub("5.2","Deviation from expected results and wider need",[
"The initial user problem was described as enabling users to check whether a website is legitimate and okay, to help avoid scams. The completed implementation measures TLS certificate validation, selected headers, cookies, and server disclosure. It does not inspect a site's business identity, domain registration history, brand impersonation, content, payment workflow, reputation, or reports of abuse.",
"The project therefore deviates from the broad expectation if interpreted as a definitive scam detector. The implementation outcome is narrower and safer: it provides configuration indicators and explains that they are not a trust verdict. A future product definition should either keep the narrow scope and describe it accordingly, or add independently validated anti-phishing and identity signals with careful source attribution and uncertainty handling.",
"The sample test results also did not produce different score values; both sites scored 58. This is not a failed experiment. It shows that under the current rule set both responses triggered the same deductions. It also reveals that the score has limited ability to distinguish sites when only a handful of header presence checks are used."
])
sub("5.3","Major contributions",[
"The main engineering contribution is an end-to-end implementation in which UI, API, request safety, finding construction, storage, and export are connected. The request module validates public routability, rechecks redirects, pins outbound sockets to validated IP addresses, verifies TLS, limits body size, and enforces a timeout. The report module produces structured observations and recommendations that are consumed consistently by the dashboard and PDF exporter.",
"The project also provides a clear example of the tradeoff between scan breadth and target impact. Rather than attempting a full vulnerability scan, it focuses on a small number of observable browser-facing controls. The result is easier to explain to a beginner and easier to constrain, but it leaves many classes of risk unassessed.",
"The academic contribution is a documented design rationale, a small transparent scoring model, results from two supplied snapshots, and explicit limits. The project does not claim a new scoring standard or broad empirical finding."
])
sub("5.4","Limitations",[
"The largest limitation is coverage. A single GET response cannot establish the behavior of other routes, subdomains, user sessions, or browser states. It cannot test whether a missing or present header leads to an exploitable vulnerability. It cannot identify deceptive business practices, phishing, malicious content, or compromise.",
"The rules are primarily presence checks. They do not fully parse policy directives, validate policy quality, classify cookie purposes, or assess whether a recommendation is appropriate for a particular site. The score is a transparent but unvalidated weighted sum; its labels may encourage users to overinterpret a number.",
"The evaluation sample includes only two supplied scan reports. The sample is small, non-random, and collected on one date. The PDF exports do not include raw response headers, so some evidence cannot be independently reconstructed from the report alone. No automated tests, usability study, performance benchmark, or third-party security audit are included in the provided project artifacts.",
"The deployment design also has limitations. MongoDB configuration is required by the startup code, despite the sample environment file's optional wording. There is no scan-specific API rate limit visible, no report deletion flow in the interface, and no documented retention or backup policy. These matters should be addressed before public deployment."
])
sub("5.5","Future work",[
"Future work should begin with automated unit and integration tests for every rule and request boundary. Controlled fixtures can test URL parsing, IPv4 and IPv6 public/private classification, redirect revalidation, timeout handling, body limits, cookie attribute parsing, severity ordering, score arithmetic, and HTML title extraction without contacting arbitrary third-party sites.",
"The score should become more transparent and calibrated. The user should be able to expand a finding to see its rule definition, evidence, rationale, limits, and remediation examples. Scoring could distinguish high-impact transport issues from informational positives and avoid double counting related observations. Any new numeric thresholds should be evaluated with security practitioners and user comprehension studies.",
"Coverage can expand gradually while preserving scope boundaries. Candidate additions include parsing the value and quality of CSP, checking HSTS max-age and subdomain directives, identifying unsupported or unsafe cookie values, verifying a controlled list of HTTP-to-HTTPS redirect behavior, and allowing a user to assess multiple explicitly chosen paths. Each extension needs a test plan and a visible statement of how it affects scan intensity.",
"To address scam avoidance more directly, a separate user education module could explain that TLS verifies a connection to a domain, not the honesty of the site operator. Future integrations might consult carefully selected, transparent sources for domain age, certificate transparency, abuse reporting, or known phishing indicators. Such data can be stale or incomplete and must not be collapsed into a definitive legitimacy verdict.",
"Operational improvements include scan-specific rate limiting, report deletion and retention controls, a single-database tenant model with explicit account scoping if appropriate, stronger deployment guidance, and network egress controls. Setup documentation should be reconciled with the actual MongoDB requirement, and secrets should be managed through a secure deployment mechanism.",
"A larger evaluation should recruit a defined sample of authorized sites, publish a date and method, preserve sanitized request evidence, compare findings with manual review, and report precision and recall only for rules that have a defensible ground truth. A user study could check whether the interface causes false confidence or helps users understand concrete configuration limitations."
])
sub("5.6","Way ahead",[
"The immediate next steps are to complete the administrative title-page and certificate details, reconcile the MongoDB setup instructions, add test coverage for the safe request pipeline, obtain supervisor review of the scoring and security language, and run controlled tests that document expected and observed outcomes. Once those steps are complete, the project can be presented as a student prototype for passive configuration awareness.",
"The most important product decision is whether Surface Watch will remain a configuration dashboard or evolve toward a wider scam-risk service. The former can retain its narrow, low-impact design and focus on strong explanations. The latter would require additional data sources, a distinct threat model, operational monitoring, user research, and careful treatment of uncertainty. The two paths should not be conflated in the score."
])
add_table(["Expected outcome","Observed outcome","Disposition"],[
("Provide a quick site trust decision","Provides configuration observations only","Clarify product wording; trust claim remains out of scope"),
("One understandable score","Both sample responses score 58/100","Implemented; calibration and transparency are future work"),
("Safe limited assessment","Controls are implemented in request code","Needs automated negative-case validation"),
("Store private scan history","Per-user database model and auth guards are present","Needs multi-account isolation testing and retention design"),
("Demonstrate with test sites","Two reports and one UI screenshot supplied","Demonstrated for n=2; no population inference")],[2.05,2.05,1.8],9)

# References: numeric labels preserve the in-text citation keys; entries are alphabetized by author.
page(); heading("REFERENCES",1)
refs=[
"[4] Barth, A. (2011). HTTP State Management Mechanism. RFC 6265. Internet Engineering Task Force. https://www.rfc-editor.org/rfc/rfc6265.html",
"[7] Buchanan, W. J., Helme, S., and Woodward, A. (2018). Analysis of the adoption of security headers in HTTP. IET Information Security, 12(2), 118-126. https://doi.org/10.1049/iet-ifs.2016.0621",
"[9] Calzavara, S., Urban, T., Tatang, D., Steffens, M., and Stock, B. (2021). Reining in the Web's Inconsistencies with Site Policy. Network and Distributed System Security Symposium. https://doi.org/10.14722/ndss.2021.23091",
"[1] Fielding, R., Nottingham, M., and Reschke, J. (Eds.). (2022). HTTP Semantics. RFC 9110. Internet Engineering Task Force. https://www.rfc-editor.org/rfc/rfc9110.html",
"[6] Franken, G., Van Goethem, T., Desmet, L., and Joosen, W. (2023). A Bug's Life: Analyzing the Lifecycle and Mitigation Process of Content Security Policy Bugs. 32nd USENIX Security Symposium, 3673-3690. https://www.usenix.org/conference/usenixsecurity23/presentation/franken",
"[3] Hodges, J., Jackson, C., and Barth, A. (2012). HTTP Strict Transport Security (HSTS). RFC 6797. Internet Engineering Task Force. https://www.rfc-editor.org/rfc/rfc6797.html",
"[12] Kishnani, U., and Das, S. (2024). Securing the Web: Analysis of HTTP Security Headers in Popular Global Websites. arXiv:2410.14924. Preprint. https://arxiv.org/abs/2410.14924",
"[8] Lavrenovs, A., and Melón, F. J. R. (2018). HTTP Security Headers Analysis of Top One Million Websites. 10th International Conference on Cyber Conflict (CyCon), 345-370. https://doi.org/10.23919/CYCON.2018.8405025",
"[11] OWASP Foundation. (2026). HTTP Headers Cheat Sheet. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html",
"[13] OWASP Foundation. (2026). Server Side Request Forgery Prevention Cheat Sheet. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html",
"[2] Rescorla, E. (2026). The Transport Layer Security (TLS) Protocol Version 1.3. RFC 9846. Internet Engineering Task Force. https://www.rfc-editor.org/rfc/rfc9846.html",
"[10] Tyson, G., Huang, S., Cuadrado, F., Castro, I., Perta, V. C., Sathiaseelan, A., and Uhlig, S. (2017). Exploring HTTP Header Manipulation In-The-Wild. Proceedings of the 26th International Conference on World Wide Web, 451-458. https://doi.org/10.1145/3038912.3052571",
"[5] World Wide Web Consortium. (2026). Content Security Policy Level 3. W3C Working Draft. https://www.w3.org/TR/CSP3/"
]
for ref in refs:
    p=DOC.add_paragraph(); p.paragraph_format.line_spacing=1.0; p.paragraph_format.space_after=Pt(8); p.alignment=WD_ALIGN_PARAGRAPH.LEFT; p.add_run(ref)

# Appendix 1: step-by-step manual with supplied UI and report evidence.
page(); heading("APPENDIX 1  USER MANUAL",1)
para("This manual describes how to run Surface Watch locally, create an account, assess an authorized public website, review a report, and export it. A MongoDB connection is required by the current server startup code. Use the application only for websites that you own or are authorized to assess.")
heading("A1.1 Operating requirements",2)
add_table(["Requirement","Description"],[
("Node.js","Version 20 or newer, as stated in the project README"),
("MongoDB","MongoDB Atlas or another reachable MongoDB deployment"),
("Environment file","MONGODB_URI, PORT if required, and a stable SESSION_SECRET"),
("Browser","Chrome was used for the supplied interface evidence"),
("Network access","The local service binds to 127.0.0.1; outbound DNS and HTTP/HTTPS must be available")],[1.45,4.55],9)
heading("A1.2 Prepare the application",2)
for s in [
"Open the project folder in a terminal and install the dependencies with npm install.",
"Create a private .env file from .env.example. Set MONGODB_URI to the database connection string and set SESSION_SECRET to a long random value. Keep this file private and do not include it in source control or screenshots.",
"Start the development application with npm run dev. Wait for the Vite development URL and the Express API startup message. The API expects MongoDB to connect before it begins listening.",
"Open the local Vite URL in Chrome. The application should first display the account access screen."
]: numbered(s)
para("Setup note: the current .env.example comment says scans may run without MongoDB, but server/server.js requires MONGODB_URI at startup. Follow the server requirement until the project is updated.")
heading("A1.3 Sign in",2)
para("Enter the email address and password for an existing account, then select Sign in. The sign-in screen explains that the account provides access to private scan history. If you do not have an account, choose Create an account.")
image(IMG/"signin-screen.png",6.1); caption("Figure A1.1: Sign-in screen supplied by the student")
heading("A1.4 Create an account",2)
for s in [
"On the account access screen, choose Create an account.",
"Enter a valid email address and a password that is at least ten characters long. The server also rejects passwords over 72 UTF-8 bytes.",
"Select Create account. If the email is already registered, sign in with that account instead.",
"After successful registration, the application opens the private scan workspace."
]: numbered(s)
image(IMG/"registration-screen.png",6.1); caption("Figure A1.2: Account creation screen supplied by the student")
heading("A1.5 Enter an authorized website URL",2)
para("Use the website URL field on the dashboard and enter a public HTTP or HTTPS URL. The scanner rejects unsupported schemes, embedded username or password credentials, localhost, and destinations that resolve to non-public addresses. Each redirect is checked before the next request. Use only a site you own or have permission to assess.")
para("The scan button starts one bounded GET request. The application displays an assessing state while the server performs the request. It does not crawl links, submit forms, inject payloads, try website credentials, or exploit vulnerabilities.")
heading("A1.6 Read the assessment",2)
para("The assessment view shows the host, final URL, scan time, score, severity counts, severity chart, HTTP status, duration, redirect count, and page title. The findings list is sorted by severity. Each row includes a category, evidence detail, and recommendation. Review the details instead of relying on the score alone.")
image(IMG/"example-dashboard.png",6.15); caption("Figure A1.3: Assessment dashboard for example.com supplied by the student")
para("Interpretation rule: Surface Watch reports a small set of configuration indicators for one response. HTTPS and a valid certificate do not prove that an organization is legitimate or that its content is safe. A score of 100 would still not mean that the website is vulnerability-free.")
heading("A1.7 Review a specific finding",2)
for s in [
"Read the severity label and category to understand the application's prioritization.",
"Read the evidence sentence to see which response field or condition was observed.",
"Read the recommendation and verify that it is appropriate for the target's actual architecture before changing a production configuration.",
"For CSP, HSTS, and framing controls, test the change on a staging environment and check legitimate resources and integrations before broad deployment."
]: numbered(s)
heading("A1.8 Open scan history",2)
para("Scroll to Recent assessments. The table lists the latest 30 reports associated with the signed-in account. Select a row to reopen the report. The history table includes target host, scan time, score, and high and medium finding counts. The storage indicator shows whether MongoDB is connected.")
para("Reports created before account support are stored separately in an older shared scans collection and are not automatically assigned to a new account. The current interface does not provide a report deletion control.")
heading("A1.9 Rescan and export",2)
para("Select Rescan to submit the current URL again. A rescan is a new observation and may differ because the server configuration, CDN response, DNS answer, network path, or time changed. Select Export PDF to create a two-page A4 report containing the score, response facts, findings, recommendations, and scope note.")
para("When sharing a report, check that its target, timestamp, and content are appropriate to disclose. The report is not a certification document and does not prove authorization.")
heading("A1.10 Sign out",2)
para("Select the sign-out icon in the top bar. The server destroys the session and the client clears its visible report, URL, and history state. Close the browser when using a shared computer.")
heading("A1.11 Troubleshooting",2)
add_table(["Symptom","Likely reason","Action"],[
("Sign-in page never finishes loading","API or database unavailable","Check that the server is running and MongoDB is reachable"),
("Could not create account database","Database user lacks permissions or URI is invalid","Verify the connection string and database create/read/write permission"),
("Localhost/private destination rejected","Target is outside the allowed public scope","Use an authorized globally routable public URL"),
("Hostname could not be resolved","DNS returned no usable address","Check the domain spelling and DNS availability"),
("Too many redirects","More than three redirect hops or redirect loop","Enter the final public URL if authorized and retry"),
("Request timed out","Target did not complete within ten seconds","Retry later or review target availability"),
("Report differs from an earlier scan","Response or network path changed","Compare timestamps and findings; each report is a separate snapshot")],[1.7,2.1,2.2],8)

# Appendix 2: test cases and traceability.
page(); heading("APPENDIX 2  TEST CASES AND TRACEABILITY",1)
para("The table separates observed evidence from recommended test execution. Only the two supplied HTTPS report outputs are counted as observed scan runs in this report. Network safety and authentication tests below are specified for future controlled validation and must not be represented as completed without recorded results.")
heading("A2.1 Requirements traceability",2)
add_table(["Objective","Requirement","Implementation artifact","Evidence"],[
("O1","FR-04","src/App.jsx and POST /api/scans","Dashboard workflow and supplied scan PDFs"),
("O2","FR-05","server/scanner/request.js","Source inspection; negative-case tests pending"),
("O3","FR-05","Timeout, response cap and redirect bound","Source inspection"),
("O4","FR-06","server/scanner/report.js","Two report PDFs"),
("O5","FR-07","FindingRow, score ring, severity chart","Supplied dashboard screenshot and PDFs"),
("O6","FR-08","requireAuth and per-user Scan model","Source inspection; isolation tests pending"),
("O7","FR-09","src/exportPdf.js","Two exported PDF reports"),
("O8","Evaluation","example.com and neverssl.com","Two supplied snapshots, n=2")],[.65,.8,2.1,2.45],8)
heading("A2.2 Safe network test cases",2)
cases=[
("N-01","Valid HTTPS hostname resolves only to public IPs","Complete one GET and produce report","Pending controlled test"),
("N-02","URL uses ftp scheme","Reject before DNS or HTTP request","Pending"),
("N-03","URL contains embedded credentials","Reject with public website URL error","Pending"),
("N-04","Hostname is localhost or subdomain of localhost","Reject without outbound request","Pending"),
("N-05","DNS returns loopback or private address","Reject destination","Pending"),
("N-06","DNS returns mixed public and private addresses","Reject because all answers must be public","Pending"),
("N-07","Public target redirects to private address","Revalidate and reject second hop","Pending"),
("N-08","More than three redirects","Stop with too-many-redirects error","Pending"),
("N-09","Target does not respond before timeout","Terminate request at approximately ten seconds","Pending"),
("N-10","Target streams a response above 512 KiB","Retain no more than response cap and stop reading","Pending"),
("N-11","HTTPS certificate is invalid","Reject connection because certificate validation is enabled","Pending"),
("N-12","Hostname cannot resolve","Return resolution error without report","Pending")]
add_table(["ID","Input condition","Expected result","Status"],cases,[.55,2.15,2.5,.8],8)
heading("A2.3 Rule engine tests",2)
add_table(["ID","Fixture response","Expected observation","Status"],[
("R-01","HTTPS, certificate valid, no security headers","HTTPS info plus missing header findings and score","Source-reviewed; test pending"),
("R-02","HTTPS with CSP frame-ancestors","No missing clickjacking finding","Test pending"),
("R-03","HTTPS with X-Frame-Options but no frame-ancestors","No missing clickjacking finding","Test pending"),
("R-04","HTTPS with Set-Cookie lacking Secure","Medium cookie finding","Test pending"),
("R-05","HTTP response with Set-Cookie lacking Secure","No Secure cookie check from this condition; HTTP transport high finding","Test pending"),
("R-06","Cookie with HttpOnly and SameSite but no Secure over HTTPS","Secure finding only","Test pending"),
("R-07","Server and X-Powered-By both present","Two low disclosure findings","Test pending"),
("R-08","No findings returned","Score and summary remain consistent; UI caveat appears","Test pending"),
("R-09","Findings shuffled in input","Output sorted by severity/category/title","Test pending"),
("R-10","Three medium and four low findings","Score equals 58","Observed in both supplied reports")],[.55,2.0,2.7,.75],8)
heading("A2.4 Account and report workflow cases",2)
add_table(["ID","Test","Expected behavior","Status"],[
("A-01","Register valid new account","Hash password and create user/session","Source-reviewed; execution pending"),
("A-02","Register duplicate email","Return conflict response","Source-reviewed; execution pending"),
("A-03","Password shorter than ten characters","Reject registration","Source-reviewed; execution pending"),
("A-04","Login incorrect password","Return generic authentication error","Source-reviewed; execution pending"),
("A-05","Call scan route without session","Return 401 and do not scan","Source-reviewed; execution pending"),
("A-06","Open one user's scan history as another user","Only that account's records returned","Per-user model intended; isolation test pending"),
("A-07","Logout then call protected route","Session no longer accepted","Source-reviewed; execution pending"),
("A-08","Export report","A4 PDF contains all findings and scope note","Two supplied exports observed")],[.55,2.0,2.7,.75],8)

# Appendix 3: selected technical reference and code excerpts.
page(); heading("APPENDIX 3  TECHNICAL REFERENCE AND SELECTED CODE",1)
para("This appendix summarizes selected implementation patterns from the inspected source. It is not a complete source listing. Identifiers and behavior are described as they appear in the project at report preparation time.")
heading("A3.1 Request limits",2)
add_table(["Constant","Value","Purpose"],[
("MAX_RESPONSE_BYTES","512 × 1024","Bounds body bytes retained for a response"),
("MAX_REDIRECTS","3","Bounds followed redirect hops"),
("REQUEST_TIMEOUT_MS","10,000","Terminates slow requests"),
("Allowed protocols","http:, https:","Rejects other URL schemes"),
("HTTP method","GET","No form submission or write request")],[1.65,1.25,3.05],9)
heading("A3.2 Score calculation",2)
code=("const points = { critical: 35, high: 20, medium: 10, low: 3, info: 0 };\\n"
      "const lostPoints = findings.reduce((total, item) => total + points[item.severity], 0);\\n"
      "return Math.max(0, 100 - lostPoints);")
p=DOC.add_paragraph(); p.paragraph_format.left_indent=Inches(.3); p.paragraph_format.line_spacing=1.0
r=p.add_run(code); r.font.name="Consolas"; r.font.size=Pt(9)
para("For the supplied reports, the deduction is 3 × 10 + 4 × 3 = 42, yielding a score of 58. The informational observation has a zero-point weight.")
heading("A3.3 Safe destination validation overview",2)
for t in [
"Parse the URL using the platform URL parser.",
"Require HTTP or HTTPS; reject embedded credentials and missing hostnames.",
"Reject localhost names.",
"Parse literal IP addresses or resolve all DNS answers.",
"Reject the host if any answer is not classified as globally routable.",
"Pin the HTTP client's lookup callback to the selected validated address.",
"For each redirect, resolve and validate the new destination before requesting it.",
"Stop after three redirects, ten seconds, or 512 KiB of response data."
]: numbered(t)
heading("A3.4 Authentication and session properties",2)
add_table(["Property","Implementation detail"],[
("Password storage","bcryptjs hashing, work factor 12; passwordHash excluded from default query results"),
("Password policy","At least 10 characters; no more than 72 UTF-8 bytes"),
("Login limiter","10 attempts per 15 minutes on auth routes"),
("Session identifier","Regenerated after successful registration or login"),
("Cookie flags","httpOnly, SameSite=Lax; Secure in production"),
("Session lifetime","Seven days"),
("Session store","MongoDB collection named sessions"),
("User scan data","Database named surface_user_<user-id>, collection scans")],[1.5,4.5],9)
heading("A3.5 API route inventory",2)
add_table(["Method and route","Access","Purpose"],[
("GET /api/auth/me","Session optional","Return current user or null"),
("POST /api/auth/register","Rate limited","Create account, scan collection and session"),
("POST /api/auth/login","Rate limited","Verify credentials and establish session"),
("POST /api/auth/logout","Session optional","Destroy session"),
("GET /api/health","Public","Report database connection state"),
("GET /api/scans","Authenticated","Return up to 30 recent scans"),
("POST /api/scans","Authenticated","Validate URL, scan, save and return report")],[1.8,1.2,3.0],9)
heading("A3.6 Scan record fields",2)
add_table(["Field group","Fields","Purpose"],[
("Target","target, finalUrl, host","Original and resolved identity of assessed endpoint"),
("Timing","scannedAt, durationMs","Snapshot time and measured processing duration"),
("Response","statusCode, contentType, pageTitle, redirects","Basic response context"),
("Assessment","score, findings, summary","Structured observation output"),
("Scope","scopeNote","Limits carried with the report")],[1.2,2.6,2.2],9)
heading("A3.7 Setup discrepancy requiring correction",2)
para("The sample environment file says the MongoDB URI is optional and suggests that scans still run with temporary history. The current server implementation requires MONGODB_URI in startServer and does not show a memory-backed authentication or scan mode. The project README correctly states that the URI is required for authentication and per-user databases. The environment-file comment should be updated, or a genuine temporary mode should be implemented and documented.")

# Appendix 4: planning and risk register.
page(); heading("APPENDIX 4  PROJECT PLANNING AND RISK REGISTER",1)
heading("A4.1 Project schedule",2)
add_table(["Work item","Aug 2026","Sep 2026","Oct 2026","Nov 2026","Next"],[
("Define need and scope","●","●","","",""),
("Review standards and studies","","●","●","",""),
("Design architecture and request controls","","●","●","",""),
("Implement scan and report workflow","","","●","●",""),
("Capture two sample results","","","","●",""),
("Automated safety and rule tests","","","","","●"),
("Supervisor feedback and final revisions","","","","","●")],[2.45,.65,.65,.65,.65,.65],8)
para("The schedule is an approximate sequencing aid based on the student-provided start date and project state. It does not imply that a task was completed on every marked date.")
heading("A4.2 Risk register",2)
add_table(["Risk","Likelihood","Impact","Mitigation / response"],[
("User interprets score as proof of legitimacy","Medium","High","Prominent scope note and future user comprehension study"),
("Scanner reaches internal service through URL or redirect","Low-Medium","High","Public IP validation, socket pinning, redirect revalidation and controlled tests"),
("Target response consumes excessive resources","Low","Medium","Timeout, response cap, redirect bound"),
("Unauthorized assessment creates complaints","Medium","High","Use only owned/authorized targets; consent workflow recommended"),
("Database credentials or session secret exposed","Medium","High","Keep .env private; use secrets manager in deployment"),
("Cross-account history exposure","Low-Medium","High","Authenticated routes and per-user database model; test isolation"),
("Score fails to reflect application risk","High","High","Explain weights, avoid certification language, calibrate before reliance"),
("MongoDB setup instructions contradict code","Medium","Medium","Correct .env.example or implement temporary storage mode"),
("Small sample is overgeneralized","Medium","Medium","Report n=2 and prohibit population inference"),
("Policy recommendation breaks target application","Medium","Medium","Advise contextual review and staging before changes")],[2.25,.75,.75,2.0],8)
heading("A4.3 Professional and ethical use checklist",2)
for t in [
"Confirm ownership or written authorization before assessing a website.",
"Use the scanner only for the documented passive GET workflow.",
"Do not treat a public URL as permission to test the service.",
"Do not publish a target report without considering privacy and disclosure impact.",
"Describe observations, dates, request scope, and limitations accurately.",
"Do not present the score as proof of safety, identity, compliance, or trustworthiness.",
"Use a controlled test server for negative network-safety tests."
]: bullet(t)
heading("A4.4 Project completion snapshot",2)
para("The project has produced a working individual prototype that connects an authenticated dashboard to a bounded scanner, a deterministic findings engine, per-user scan persistence, report history, and A4 PDF export. The supplied evidence includes sign-in and account-creation screens, an example.com assessment screenshot, and exported assessment PDFs for example.com and neverssl.com. Both supplied reports were processed into a documented results analysis. No awards, certificates, publications, or external competition results were reported by the student as of November 2026.")

# Appendix 5: detailed rule catalog and interpretation cards.
page(); heading("APPENDIX 5  RULE CATALOG AND INTERPRETATION NOTES",1)
para("This catalog expands the scanner's current rule set into an operator-facing reference. Each rule describes the observable response condition, why it can matter, what Surface Watch does, and what the finding cannot prove. The policy value of any remediation depends on the site's architecture and browser support.")
heading("A5.1 Transport and certificate observation",2)
para("For an HTTPS final URL, the scanner records “HTTPS certificate validated” as an informational finding after the Node.js HTTPS request completes with certificate verification enabled. This indicates that this client accepted the TLS connection under its configured verification behavior for that hostname at this time. It is evidence about the connection, not a guarantee that the organization is genuine or the page is benign.")
para("For a final HTTP URL, the scanner records “HTTPS is not enabled” as a high finding. A site operator should configure HTTPS and direct users to it, then consider HSTS after confirming the site and required subdomains are consistently available over TLS. Surface Watch does not inspect certificate expiry dates, certificate transparency, revocation status, supported protocol versions, ciphers, or mixed content.")
add_table(["Rule outcome","Severity","Score effect","Interpretation boundary"],[
("HTTPS connection verified","Info","0","Does not validate business identity or content"),
("Final URL uses HTTP","High","-20","One final response observed without TLS")],[1.8,.85,1.0,2.1],9)
heading("A5.2 Strict-Transport-Security",2)
para("The rule reports HSTS missing only when the final response URL is HTTPS and the response has no Strict-Transport-Security field. The browser uses a valid policy to remember that a host should be accessed over secure transport. A site administrator should choose a max-age that fits the site's operational readiness, and should enable includeSubDomains only when every affected subdomain can support HTTPS [3].")
para("The current implementation does not verify that max-age is present or positive, whether the header is syntactically valid, whether it is sent on all relevant responses, or whether the host is submitted to a preload list. Presence is therefore the sole observed signal. A header can exist and still be ineffective or risky.")
heading("A5.3 Content Security Policy",2)
para("The rule reports CSP missing when the response does not contain content-security-policy. CSP can constrain resource loading and script execution, but policy quality depends on directives, source expressions, nonce or hash use, browser behavior, and the application's legitimate dependencies. Start with report-only testing where available, inspect violations, then enforce a restrictive policy that matches the application.")
para("Surface Watch does not parse CSP directives or assess whether sources are overly broad. The separate framing check searches for the text frame-ancestors in the lowercased header value; it does not validate syntax or semantic effect. A false sense of safety can result if a present policy is malformed or permissive.")
heading("A5.4 Framing and clickjacking protection",2)
para("The rule reports missing clickjacking protection when neither X-Frame-Options nor a CSP frame-ancestors substring is observed. Framing restrictions can reduce the chance that a sensitive page is embedded by an untrusted site and visually overlaid to trick a visitor. Operators should decide which pages can be embedded and by which trusted origins.")
para("The check is presence-oriented. It does not parse allowed framing origins, test behavior in browsers, account for legacy browser differences, or assess UI redress attacks using techniques other than framing. A JSON API or a page without user-action controls may have a different risk context.")
heading("A5.5 X-Content-Type-Options",2)
para("The rule reports the absence of X-Content-Type-Options. Setting the value to nosniff tells supporting browsers not to reinterpret a response's MIME type in certain contexts. Operators should ensure that Content-Type values are correct and that nosniff is compatible with the site's JavaScript, CSS, and asset delivery.")
para("The scanner only checks whether the field exists. It does not validate the value or inspect each content type and resource. The finding is not evidence that a browser actually executed content under an incorrect MIME interpretation.")
heading("A5.6 Referrer-Policy",2)
para("The rule reports the absence of Referrer-Policy. The policy controls how much referring URL information is sent in outgoing requests initiated from a document. A policy can reduce leakage of sensitive path or query data to third-party sites while retaining expected analytics or navigation behavior.")
para("Surface Watch does not inspect page links or measure what a particular browser sends. The operator should choose a policy based on privacy requirements, cross-origin workflows, and compatibility. A missing field does not by itself establish that sensitive information has leaked.")
heading("A5.7 Permissions-Policy",2)
para("The rule reports the absence of Permissions-Policy. The header can constrain selected browser features for the document and embedded contexts. Disabling features that a site does not need can reduce unnecessary capability exposure, but values must be chosen deliberately to preserve product behavior.")
para("The rule does not parse directives, inspect feature use, or determine whether a feature is actually sensitive for the target. A present policy may still allow more than intended, and a restrictive policy may break legitimate functionality.")
heading("A5.8 Cookie Secure attribute",2)
para("For each observed Set-Cookie value on an HTTPS response, the scanner reports a medium finding when Secure is absent. Secure instructs the browser to send the cookie only over secure transport under the cookie processing model. This is commonly important for session identifiers and other sensitive state [4].")
para("The scanner does not determine whether a cookie is sensitive, whether it is a session token, or whether it will be used on HTTP endpoints. It checks each response cookie mechanically. Operators should pair Secure with correct HTTPS redirection and review cookie scope and application session handling.")
heading("A5.9 Cookie HttpOnly and SameSite attributes",2)
para("The scanner reports a medium finding when HttpOnly is absent and a low finding when SameSite is absent. HttpOnly limits access through non-HTTP script APIs; SameSite controls cross-site cookie sending behavior according to the selected policy. Their value depends on the application and on how state-changing requests are protected.")
para("The current implementation does not inspect SameSite values such as Strict, Lax, or None, whether None is paired with Secure, or whether client-side scripts need access. It also does not test CSRF behavior. Absence is a prompt for review, not proof of exploitation.")
heading("A5.10 Server and X-Powered-By disclosure",2)
para("When Server or X-Powered-By appears, the scanner creates a low-severity information-disclosure finding. Minimizing unnecessary version detail may reduce easy fingerprinting. It does not prevent an attacker from identifying software through other protocol behavior, page content, or public files; patching and secure configuration remain the primary controls.")
para("The implementation reports the field's presence but does not include its raw value in the finding detail. This reduces unnecessary disclosure in the report while retaining enough context for the owner to review server configuration.")
heading("A5.11 Rule applicability and false-positive sources",2)
para("The scanner evaluates the final response after following up to three redirects. A security policy may differ between the original URL, a canonical host, language-specific path, CDN edge, or authenticated workflow. A field may also be applied at a proxy or web application firewall that produces different responses based on request headers or location.")
para("The same rule can be more or less important depending on page purpose. A global marketing page, a login page, a static image, and an API response do not have identical requirements. Because the scanner currently targets the entered URL only, all findings require contextual review.")
heading("A5.12 Remediation review checklist",2)
for t in [
"Confirm the target and response path match the page that needs protection.",
"Check the raw response in a controlled browser or server log before changing production settings.",
"Review the recommendation against site functionality, third-party integrations, and subdomain ownership.",
"Test policy changes in a staging environment and monitor browser reports where available.",
"Record the change owner, date, rollback procedure, and post-change verification.",
"Rescan the same authorized URL and compare the new observation with the previous snapshot."
]: bullet(t)

# Appendix 6: operations and maintenance.
page(); heading("APPENDIX 6  OPERATIONS AND MAINTENANCE GUIDE",1)
para("This guide is for a student or maintainer who runs the application locally or prepares it for a controlled deployment. It expands the README into operational tasks and highlights configuration decisions that need an owner.")
heading("A6.1 Environment configuration",2)
para("Keep MONGODB_URI and SESSION_SECRET out of source files and public screenshots. Use a private environment file for local development and a managed secret store for production. Give the database account only the permissions needed for user records, session storage, and the per-user scan databases. Avoid printing connection strings in logs or error reports.")
para("The code expects MongoDB to connect before Express starts listening. Check the startup log and database health endpoint before inviting users. The environment sample should be corrected to remove the suggestion that the URI is optional unless an actual temporary-storage mode is added and tested.")
heading("A6.2 Database permissions and data separation",2)
para("At registration, the server creates a scan collection in a database named for the new user ID. The database identity is derived from a trusted server-side user record, not from a request parameter. Protected routes resolve the session user before selecting the scan model. This design should be tested with two accounts to ensure no report can be read or written across account boundaries.")
para("Before deployment, document how user account records, sessions, and scan reports are backed up, retained, restored, and deleted. The current interface does not provide report deletion. A retention period and deletion workflow should be selected before collecting real user histories.")
heading("A6.3 Session configuration",2)
para("Set a long random SESSION_SECRET and keep it stable across server restarts and application instances. Set NODE_ENV to production so the session cookie uses Secure. Confirm that TLS terminates only at a trusted proxy and that trust-proxy configuration matches the actual deployment topology. The code sets one trusted proxy hop; this must be reviewed before use behind a different proxy chain.")
para("The session lasts seven days. Define whether this is appropriate for the data sensitivity and user expectations. Consider a shorter idle timeout, explicit account logout on password changes, and an administrative session revocation procedure. The current project does not include a password reset or account recovery flow.")
heading("A6.4 Network deployment",2)
para("The Express server binds to loopback at 127.0.0.1. A production setup typically places a controlled reverse proxy or platform gateway in front of it and serves the browser application over HTTPS. Do not expose the development Vite server directly to the public internet. Restrict outbound traffic at the network layer where practical, in addition to the application-level destination checks.")
para("The scanner validates redirects and pins a socket to a checked IP. Changes to Node.js, ipaddr.js, URL parsing, proxy behavior, or DNS resolution should trigger a security review of this boundary. Outbound egress controls should deny private ranges and metadata endpoints as an independent layer.")
heading("A6.5 Resource and abuse monitoring",2)
para("Each request is bounded by a timeout, body cap, and redirect cap. The scan endpoint does not show an explicit per-user or global scan rate limit in the inspected code. If the application is shared, add a scan-specific rate limit, concurrency cap, queue policy, and monitoring for repeated failures or unexpected outbound volume.")
para("Record operational metrics without logging secrets or full target response bodies. Useful measurements include scan success and error counts, average duration, timeout rate, database availability, and rate-limit events. Avoid collecting more user target history than is necessary for the service.")
heading("A6.6 Build and release procedure",2)
for s in [
"Review code and dependency changes, especially in the outbound request path, session middleware, and report rules.",
"Run the automated rule, redirect, private-address, authentication, and report-export tests in a controlled environment.",
"Build the React client with the documented production build command.",
"Start the production server with NODE_ENV, MONGODB_URI, SESSION_SECRET, and PORT configured.",
"Verify health, registration, login, scan, report history, logout, and PDF export with test accounts.",
"Record the release version and rule-set version in the report metadata so later readers can compare results."
]: numbered(s)
heading("A6.7 Backup, retention and recovery",2)
para("A scan report is a snapshot that can include a target URL and assessment time. Define whether users may delete individual reports or their account, how long records are kept, and whether backups include per-user scan databases. A recovery exercise should verify that account and scan data can be restored without cross-account mixing.")
para("The README describes that reports saved before account support remain in the previous shared collection and are not automatically assigned to new accounts. If historical data is migrated, use an explicit account-mapping process with audit logging. Do not infer ownership from email or domain names.")
heading("A6.8 Incident response and disclosure",2)
para("If a scanner request reaches an unexpected destination or a report reveals sensitive information, suspend the scan function while preserving safe diagnostic evidence. Review the submitted URL, DNS answers, redirect chain, resolved socket address, and server logs. Do not retain credentials or response bodies unless they are essential for a controlled investigation.")
para("If a target owner reports unwanted activity, stop further requests and document the request time and scope. The tool's single-request design reduces impact but does not replace authorization. A clear contact and disclosure process should be prepared before a hosted service accepts user scans.")
heading("A6.9 Accessibility and user comprehension",2)
para("The interface uses semantic labels and clear text for findings, with interactive history rows supporting keyboard focus and Enter activation. A future review should test the full flow with keyboard-only use, screen reader output, zoom, color contrast, and mobile viewport sizes. Severity colors should never be the only means of communicating priority.")
para("A comprehension review should ask users what a score of 58 means, whether they think the site is safe, what certificate validation establishes, and what the tool actually requested. The product should be refined if users infer legitimacy or exploit testing from the dashboard wording.")
heading("A6.10 Maintenance checklist",2)
add_table(["Frequency","Task","Record"],[
("Each release","Review dependencies and scan safety code","Version, changes and reviewer"),
("Monthly or per operations plan","Check MongoDB access, backups and retention","Backup result and owner"),
("After policy updates","Reassess rule wording and scoring impact","Rule-set change log"),
("After network changes","Recheck proxy trust and egress controls","Deployment diagram and test evidence"),
("Before external use","Review authorization, privacy and user comprehension","Approval and scope statement"),
("At project handoff","Correct setup documentation and supervisor details","Final checklist")],[1.35,2.8,1.85],8)

# Appendix 7: full evidence archive pages from supplied exports.
page(); heading("APPENDIX 7  ORIGINAL SCAN EVIDENCE",1)
para("The following report pages are reproduced from the PDFs supplied by the student. They retain the original report content and layout and are included so the observations can be reviewed alongside the academic analysis. The scans are dated snapshots; this appendix does not repeat the network requests.")
heading("A7.1 example.com export",2)
for i in (1,2):
    fp=IMG/f"example-report-{i}.png"
    if fp.exists():
        image(fp,6.15); caption(f"Figure A7.{i}: example.com exported report, page {i} of 2")
        if i==1: page()
heading("A7.2 neverssl.com export",2)
for i in (1,2):
    fp=IMG/f"neverssl-report-{i}.png"
    if fp.exists():
        image(fp,6.15); caption(f"Figure A7.{i+2}: neverssl.com exported report, page {i} of 2")
        if i==1: page()

# Appendix 8: expanded glossary for non-specialist readers.
page(); heading("APPENDIX 8  EXPANDED GLOSSARY",1)
glossary=[
("Address resolution","The process of translating a hostname into one or more IP addresses."),
("API","A defined interface through which one software component requests an operation from another."),
("Browser","A client application that retrieves web resources and applies browser security policies."),
("Certificate","A signed digital statement associating a public key with a name or identity under a validation system."),
("Certificate validation","A client check of the certificate chain and hostname according to configured trust rules."),
("Clickjacking","A UI redress technique that can trick a user into interacting with a framed page."),
("Cookie","A name/value state item exchanged through HTTP request and response fields."),
("CSP","A response policy that constrains content sources and browser behaviors."),
("DNS rebinding","A class of technique that changes DNS answers to bypass a check performed only before connection."),
("Finding","A structured observation generated by an implemented scanner rule."),
("Globally routable address","An IP address classified as publicly reachable rather than loopback, private, or reserved."),
("HSTS","A browser policy that tells user agents to use secure transport for a host for a stated duration."),
("HTTP status code","A three-digit response value summarizing the outcome of an HTTP request."),
("HttpOnly","A cookie attribute that limits access through non-HTTP script interfaces."),
("HTTPS","HTTP carried over a TLS-protected channel."),
("IP pinning","Connecting to the exact IP address that passed a prior destination-validation check."),
("MIME sniffing","A browser's attempt to infer a response media type from content rather than relying only on metadata."),
("MongoDB","A document-oriented database used by this project for accounts, sessions, and scan records."),
("Permissions-Policy","A response header used to control selected browser features for a document."),
("Public target","A hostname or address that resolves only to globally routable IPs under the scanner's current checks."),
("Redirect","An HTTP response that directs the client to request a different URL."),
("Referrer-Policy","A response policy that controls referrer information sent with outgoing requests."),
("Response cap","The maximum amount of response body data the scanner retains for a request."),
("SameSite","A cookie attribute that controls when the browser sends a cookie in cross-site contexts."),
("Score","A weighted deduction summary over the configured findings; not a probability or certification."),
("Secure cookie attribute","An attribute that limits a browser to sending a cookie over secure transport."),
("Server header","A response field that may identify server software or related details."),
("Session","Server-side state associated with a browser through a session identifier."),
("Severity","A project-defined priority label assigned to a finding."),
("SSRF","Server-Side Request Forgery, where an application is induced to make unintended server-side requests."),
("TLS","Transport Layer Security, a protocol family for protected communication channels."),
("URL","A structured identifier for a web resource, including scheme, host, path, and other components."),
("X-Content-Type-Options","A response header used to prevent certain browser MIME type reinterpretation."),
("X-Frame-Options","A response header that controls whether a page may be framed in supported browsers."),
("X-Powered-By","A response field that may reveal an application framework or software family.")
]
for term,meaning in glossary:
    p=DOC.add_paragraph(); p.paragraph_format.line_spacing=1.15; p.paragraph_format.space_after=Pt(5)
    r=p.add_run(term+": "); r.bold=True; r.font.name="Times New Roman"; r.font.size=Pt(11)
    r=p.add_run(meaning); r.font.name="Times New Roman"; r.font.size=Pt(11)

# Appendix 9: threat model and misuse analysis.
page(); heading("APPENDIX 9  THREAT MODEL AND MISUSE ANALYSIS",1)
para("The scanner accepts a URL from an authenticated user and makes a server-side request. This makes the scan endpoint a potential pivot point even though its intended use is benign. The threat model below identifies assets, trust boundaries, misuse cases, and mitigations visible in the code. It is a project-level analysis, not a completed penetration test.")
heading("A9.1 Assets and trust boundaries",2)
add_table(["Asset","Boundary","Security concern"],[
("Database credentials","Environment to application","Credential disclosure enables database access"),
("Session secret","Environment to session middleware","Weak or changing value can undermine session protection"),
("User account and scan history","Authenticated API to per-user model","Cross-account record exposure"),
("Outbound network access","Server to user-selected URL","SSRF to internal services or metadata endpoints"),
("Response body and headers","Target to scanner memory","Unexpected volume or malformed values"),
("User trust decisions","Dashboard to user","Score may be mistaken for legitimacy proof")],[1.55,2.05,2.4],8)
heading("A9.2 Misuse cases",2)
add_table(["Misuse case","Attacker action","Relevant control","Residual concern"],[
("Internal network probe","Submit localhost/private IP URL","Reject non-public destinations","Unseen parsing or future dependency weaknesses"),
("Redirect escape","Use public URL redirecting to private target","Revalidate each redirect","Must be tested with controlled fixtures"),
("DNS rebinding","Change DNS from public to private answer","Validate all answers and pin socket","Network egress policy adds defense in depth"),
("Resource exhaustion","Slow or oversized response","Timeout and 512 KiB cap","Concurrent requests and scan rate are not capped"),
("Account brute force","Repeated sign-in attempts","10 attempts per 15-minute auth limiter","Distributed attack and limiter store behavior need review"),
("Cross-user access","Request another user's history","Session-based user lookup and per-user DB","Requires integration test with multiple accounts"),
("Trust manipulation","Share a high score as a safety guarantee","Scope note and cautious wording","User testing should measure misunderstanding")],[1.3,1.65,1.75,1.3],8)
heading("A9.3 Defensive layers",2)
para("The most important layers are protocol allowlisting, credential rejection, hostname checks, public-address classification, connection pinning, redirect revalidation, TLS verification, bounded response reads, request timeout, authentication, and per-user report selection. These controls operate at different stages and should not be treated as substitutes for each other.")
para("Additional defenses suitable for a hosted service include network egress filtering, scan-specific rate limiting, concurrency caps, structured security logging, dependency update review, explicit user authorization confirmation, and a privacy-aware retention policy. Such additions should preserve the project's low-impact design.")
heading("A9.4 Abuse response priorities",2)
for t in [
"Disable or rate-limit the scan endpoint if an unexpected destination pattern is detected.",
"Preserve minimal metadata needed to review time, URL host, redirect count, and validated address without retaining secrets.",
"Confirm that the account and session boundary held and that no cross-user history was exposed.",
"Patch the cause, add a controlled regression test, and review network egress controls.",
"Notify affected target owners through an approved disclosure process when warranted."
]: numbered(t)

# Appendix 10: evaluation framework and worked score examples.
page(); heading("APPENDIX 10  EVALUATION FRAMEWORK AND SCORE EXAMPLES",1)
heading("A10.1 Evaluation dimensions",2)
add_table(["Dimension","Question","Evidence available"],[
("Functional completeness","Does each planned workflow element exist?","Source and supplied screenshots"),
("Request safety","Are private destinations and resource overuse bounded?","Code review only; negative tests pending"),
("Finding correctness","Do implemented conditions map to expected findings?","Two report outputs; unit tests pending"),
("Usability","Can users distinguish a configuration signal from trust?","Visual screens only; study pending"),
("Repeatability","Can the same response fixture reproduce the same report?","Deterministic rules; fixture run not supplied"),
("Persistence isolation","Can one user access only their own history?","Code design present; integration test pending")],[1.25,2.55,2.05],9)
heading("A10.2 Worked score examples",2)
para("Example A, the supplied reports: three medium findings and four low findings give 100 - (3 × 10) - (4 × 3) = 58. One informational finding contributes zero deduction. The output score is therefore 58/100.")
para("Example B, hypothetical single HTTP-only finding: one high finding reduces the score to 80. The UI label would be Strong because its score threshold is 80. This example demonstrates a weakness in threshold interpretation: a serious transport finding can coexist with the top label. The label should be revisited or a rule-based override added.")
para("Example C, hypothetical one critical finding and several low findings: a critical deduction of 35 points may still leave the score above 55. Users should therefore read severity counts and finding details, not infer that the score threshold alone expresses urgency.")
heading("A10.3 Suggested improvements to the scoring model",2)
for t in [
"Use explicit rule identifiers and version each rule set.",
"Document evidence and rationale for every severity and weight.",
"Consider a severity override so critical or high findings cannot be hidden by a high aggregate score.",
"Group findings that share one underlying configuration cause to reduce double counting.",
"Test representative scenarios with security reviewers and intended users.",
"Label the score as a project-defined indicator and display its coverage denominator."
]: bullet(t)
heading("A10.4 Small-sample reporting checklist",2)
for t in [
"State sample size, target-selection method, scan date and local context.",
"Use descriptive counts only for non-random test examples.",
"Avoid population percentages and causal claims.",
"Retain the exact rule set and scoring version used for each report.",
"Describe whether raw response evidence is available for independent review."
]: bullet(t)

page(); heading("ACHIEVEMENTS",1)
para("The project has produced a working individual prototype that connects an authenticated dashboard to a bounded scanner, a deterministic findings engine, per-user scan persistence, report history, and A4 PDF export. The supplied evidence includes sign-in and account-creation screens, an example.com assessment screenshot, and exported assessment PDFs for example.com and neverssl.com. Both supplied reports were processed into a documented results analysis. No awards, certificates, publications, or external competition results were reported by the student as of November 2026.")

# Add page numbers, metadata, and write the editable report.
DOC.core_properties.title="Surface Watch: A Web Application Vulnerability Dashboard"
DOC.core_properties.subject="Individual BE CSE project report, Chandigarh University"
DOC.core_properties.author="Aman Kumar"
DOC.core_properties.keywords="Surface Watch, website security, HTTP headers, TLS, project report"
output=ROOT/"Surface_Watch_Project_Report.docx"
DOC.save(output)
print(output)

