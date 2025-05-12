import os
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod


class PdfParserApp:
    def __init__(self, pdf_file_name, output_dir="output"):
        self.pdf_file_name = pdf_file_name
        self.name_without_suff = os.path.splitext(
            os.path.basename(pdf_file_name))[0]

        # initialize directories
        self.output_dir = output_dir
        self.local_image_dir = os.path.join(output_dir, "images")
        self.local_md_dir = output_dir
        self.image_dir = os.path.basename(self.local_image_dir)

        os.makedirs(self.local_image_dir, exist_ok=True)
        os.makedirs(self.local_md_dir, exist_ok=True)

        # initialize writers
        self.image_writer = FileBasedDataWriter(self.local_image_dir)
        self.md_writer = FileBasedDataWriter(self.local_md_dir)

        # initialize reader
        self.reader1 = FileBasedDataReader("")
        self.pdf_bytes = self.reader1.read(self.pdf_file_name)

        # initialize dataset
        self.ds = PymuDocDataset(self.pdf_bytes)

        # initialize inference result
        self.infer_result = None
        self.pipe_result = None
        self.md_content = None
        self.content_list_content = None
        self.middle_json_content = None

    '''
    Parse the PDF file and save the results to the output directory.
    '''

    def parse_pdf(self):
        print(f"Parsing PDF: {self.pdf_file_name}")
        try:
            if self.ds.classify() == SupportedPdfParseMethod.OCR:
                self.infer_result = self.ds.apply(doc_analyze, ocr=True)
                self.pipe_result = self.infer_result.pipe_ocr_mode(
                    self.image_writer)
            else:
                self.infer_result = self.ds.apply(doc_analyze, ocr=False)
                self.pipe_result = self.infer_result.pipe_txt_mode(
                    self.image_writer)

            self.md_content = self.pipe_result.get_markdown(self.image_dir)
            self.content_list_content = self.pipe_result.get_content_list(
                self.image_dir)
            self.middle_json_content = self.pipe_result.get_middle_json()
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return False

    def save_markdown(self):
        print(f"Saving markdown to {self.local_md_dir}")
        try:
            self.pipe_result.dump_md(
                self.md_writer, f"{self.name_without_suff}.md", self.image_dir)
            return True
        except Exception as e:
            print(f"Error saving markdown: {e}")
            return False

    def draw_spans(self):
        print(f"Drawing spans to {self.local_md_dir}")
        try:
            self.pipe_result.draw_span(os.path.join(
                self.local_md_dir, f"{self.name_without_suff}_spans.pdf"))
        except Exception as e:
            print(f"Error drawing spans: {e}")

    '''
    Save all the results to the output directory.
    '''

    def save_all(self):
        if not self.infer_result or not self.pipe_result:
            raise RuntimeError(
                "You must call parse_pdf() before saving results.")
        # Draw and dump all outputs
        self.infer_result.draw_model(os.path.join(
            self.local_md_dir, f"{self.name_without_suff}_model.pdf"))
        self.pipe_result.draw_layout(os.path.join(
            self.local_md_dir, f"{self.name_without_suff}_layout.pdf"))
        self.pipe_result.draw_span(os.path.join(
            self.local_md_dir, f"{self.name_without_suff}_spans.pdf"))
        self.pipe_result.dump_md(
            self.md_writer, f"{self.name_without_suff}.md", self.image_dir)
        self.pipe_result.dump_content_list(
            self.md_writer, f"{self.name_without_suff}_content_list.json", self.image_dir)
        self.pipe_result.dump_middle_json(
            self.md_writer, f'{self.name_without_suff}_middle.json')

    def get_markdown(self):
        return self.md_content

    def get_content_list(self):
        return self.content_list_content

    def get_middle_json(self):
        return self.middle_json_content


if __name__ == "__main__":
    app = PdfParserApp("test_papers/web2.pdf")
    app.parse_pdf()
    app.save_all()
    print(app.get_markdown())
    print(app.get_content_list())
    print(app.get_middle_json())
