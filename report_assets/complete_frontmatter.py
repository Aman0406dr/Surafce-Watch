from pathlib import Path
import re
from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from pypdf import PdfReader

ROOT=Path(r"D:\cyberproject - Copy")
DOCX=ROOT/"Surface_Watch_Project_Report.docx"
PDF=ROOT/"report_assets"/"render"/"qa3.pdf"

def norm(value):
    return re.sub(r"[^a-z0-9]+","",value.lower())

def roman(number):
    values=[(1000,"m"),(900,"cm"),(500,"d"),(400,"cd"),(100,"c"),(90,"xc"),(50,"l"),(40,"xl"),(10,"x"),(9,"ix"),(5,"v"),(4,"iv"),(1,"i")]
    out=""
    for value,symbol in values:
        while number>=value:
            out+=symbol; number-=value
    return out

reader=PdfReader(str(PDF))
page_texts=[page.extract_text() or "" for page in reader.pages]
normalized_pages=[norm(x) for x in page_texts]
def find_page(text):
    query=norm(text)
    for i,value in enumerate(normalized_pages,1):
        if query and query in value:
            return i
    return None

def page_label(page_no):
    if page_no is None: return "?"
    if page_no<=12: return roman(page_no)
    return str(page_no-12)

doc=Document(str(DOCX))

def insert_entries(start_title,end_title,entries,font_size=10,spacing=1.1):
    paras=doc.paragraphs
    start=next(p for p in paras if p.style.name=="Heading 1" and norm(p.text)==norm(start_title))
    end=next(p for p in paras if p.style.name=="Heading 1" and norm(p.text)==norm(end_title))
    children=list(start._element.getparent())
    si=children.index(start._element); ei=children.index(end._element)
    for element in children[si+1:ei]:
        element.getparent().remove(element)
    for label,page_no in entries:
        p=end.insert_paragraph_before(style="Normal")
        p.paragraph_format.line_spacing=spacing
        p.paragraph_format.space_after=Pt(1)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(6.15),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        run=p.add_run(label+"\t"+page_label(page_no))
        run.font.name="Times New Roman"; run.font.size=Pt(font_size)

def top_page(title):
    return find_page(title)

toc_titles=[
("Bonafide Certificate","BONAFIDE CERTIFICATE"),
("Acknowledgement","ACKNOWLEDGEMENT"),
("Table of Contents","TABLE OF CONTENTS"),
("List of Figures","LIST OF FIGURES"),
("List of Tables","LIST OF TABLES"),
("Abstract","ABSTRACT"),
("Graphical Abstract","GRAPHICAL ABSTRACT"),
("Abbreviations, Symbols and Nomenclature","ABBREVIATIONS SYMBOLS AND NOMENCLATURE"),
("Chapter 1  Introduction","CHAPTER 1 INTRODUCTION"),
("Chapter 2  Literature Survey","CHAPTER 2 LITERATURE SURVEY"),
("Chapter 3  Design Flow and Process","CHAPTER 3 DESIGN FLOW AND PROCESS"),
("Chapter 4  Results, Analysis and Validation","CHAPTER 4 RESULTS ANALYSIS AND VALIDATION"),
("Chapter 5  Conclusion and Future Work","CHAPTER 5 CONCLUSION AND FUTURE WORK"),
("References","REFERENCES"),
("Appendix 1  User Manual","APPENDIX 1 USER MANUAL"),
("Appendix 2  Test Cases and Traceability","APPENDIX 2 TEST CASES AND TRACEABILITY"),
("Appendix 3  Technical Reference and Selected Code","APPENDIX 3 TECHNICAL REFERENCE AND SELECTED CODE"),
("Appendix 4  Project Planning and Risk Register","APPENDIX 4 PROJECT PLANNING AND RISK REGISTER"),
("Appendix 5  Rule Catalog and Interpretation Notes","APPENDIX 5 RULE CATALOG AND INTERPRETATION NOTES"),
("Appendix 6  Operations and Maintenance Guide","APPENDIX 6 OPERATIONS AND MAINTENANCE GUIDE"),
("Appendix 7  Original Scan Evidence","APPENDIX 7 ORIGINAL SCAN EVIDENCE"),
("Appendix 8  Expanded Glossary","APPENDIX 8 EXPANDED GLOSSARY"),
("Appendix 9  Threat Model and Misuse Analysis","APPENDIX 9 THREAT MODEL AND MISUSE ANALYSIS"),
("Appendix 10  Evaluation Framework and Score Examples","APPENDIX 10 EVALUATION FRAMEWORK AND SCORE EXAMPLES"),
("Achievements","ACHIEVEMENTS"),
]
toc_entries=[(label,top_page(search)) for label,search in toc_titles]
insert_entries("TABLE OF CONTENTS","LIST OF FIGURES",toc_entries,font_size=10.5,spacing=1.12)

figure_captions=[]
table_captions=[]
for p in doc.paragraphs:
    if p.style.name=="Caption":
        text=p.text.strip()
        if text.startswith("Figure "):
            figure_captions.append((text,find_page(text)))
        elif text.startswith("Table "):
            table_captions.append((text,find_page(text)))

insert_entries("LIST OF FIGURES","LIST OF TABLES",figure_captions,font_size=9.5,spacing=1.05)
insert_entries("LIST OF TABLES","ABSTRACT",table_captions,font_size=9,spacing=1.0)

doc.save(str(DOCX))
print(f"Updated contents: {len(toc_entries)} sections, {len(figure_captions)} figures, {len(table_captions)} tables; source pagination was {len(reader.pages)} pages.")
