from univy.celery_config.celery_univy import app

@app.task
def parse_pdf(pdf_file_path):
    pass