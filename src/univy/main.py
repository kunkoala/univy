import os

from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

# args
pdf_file_name = "VVAFER_Paper.pdf"  # replace with the real pdf path
name_without_suff = pdf_file_name.split(".")[0]

# prepare env
local_md_dir = "output"
md_dir = str(os.path.basename(local_md_dir))
os.makedirs(local_md_dir, exist_ok=True)

md_writer = FileBasedDataWriter(local_md_dir)


# read bytes
reader1 = FileBasedDataReader("")
pdf_bytes = reader1.read(pdf_file_name)  # read the pdf content

# proc
# Create Dataset Instance
ds = PymuDocDataset(pdf_bytes)

# inference
if ds.classify() == SupportedPdfParseMethod.OCR:
    infer_result = ds.apply(doc_analyze, ocr=True)
    pipe_result = infer_result.pipe_ocr_mode(None)
else:
    infer_result = ds.apply(doc_analyze, ocr=False)
    pipe_result = infer_result.pipe_txt_mode(None)

# get markdown content
md_content = pipe_result.get_markdown(md_dir)

pipe_result.dump_md(md_writer, f"{name_without_suff}.md", md_dir)
