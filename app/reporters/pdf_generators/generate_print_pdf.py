from datetime import datetime
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import json
# from shared.attachments import MediaFetcher
from app.reporters.charts.donurt_chart import create_donut_chart
from app.reporters.charts.wordcloud import create_word_cloud
from app.reporters.charts.pie_chart import create_pie_chart
from app.reporters.charts.bar_chart import create_horizontal_bar_chart
# from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import os

def generate_pdf(data, output_path):
    css = CSS('templates/reports.css')
    env = Environment(loader=FileSystemLoader('./templates'))
    template = env.get_template('print_report.html')
    
    # Generate charts
    # Create volume chart
    volume_chart = create_horizontal_bar_chart(
        data['volume_data']['labels'],
        data['volume_data']['values'],
        data['volume_data']['colors']
    )
    
    # Create sentimet chart
    sentiment_chart = create_donut_chart(
        data['sentiment']['labels'],
        data['sentiment']['values'],
        data['sentiment']['colors'],
        legend_position='bottom'
    )
    
    # Create sources chart
    sentiment_sources_chart = create_donut_chart(
        data['sentiment_sources']['labels'],
        data['sentiment_sources']['values'],
        data['sentiment_sources']['colors']
    )
    
    # create share of voice chart
    share_of_voice_chart = create_pie_chart(
        data['share_of_voice']['labels'],
        data['share_of_voice']['values'],
        data['share_of_voice']['colors']
    )
    # create trends wordcloud
    trending_topics_chart = create_word_cloud( data['trending_topics'])
    
    # Render template
    html_content = template.render(
        account_name=data['account']['name'],
        account_logo=data['account']['logo'],
        report_date=datetime.now().strftime('%d %b %Y'),
        volume_summary=data['volume_summary'],
        volume_mentions_summary=data['volume_mentions_summary'],
        sentiment_summary=data['sentiment_summary'],
        sentiment_mentions_summary=data['sentiment_mentions_summary'],
        volume_chart=volume_chart,
        sov_summary=data['volume_summary'],
        trends_summary=data['volume_summary'],
        sentiment_chart=sentiment_chart,
        sentiment_sources_chart=sentiment_sources_chart,
        brand_colors=data['brand_colors'],
        sentiment_mentions=data['sentiment_mentions'],
        trending_topics_chart=trending_topics_chart,
        share_of_voice_chart=share_of_voice_chart,
        app_base_url="http://ai.oxygene.co.ke",
        mentions=data['mentions']
    )
    
    HTML(string=html_content).write_pdf(target=output_path,stylesheets=[css])
    
    # # Use BytesIO for memory handling
    # pdf_bytes = BytesIO(pdf)
    # reader = PdfReader(pdf_bytes)
    # writer = PdfWriter()
    
    # # Copy pages
    # for page in reader.pages:
    #     writer.add_page(page)
    
    # # Add attachments
    # for root, dirs, files in os.walk("generated/attachments"):
    #     for file in files:
    #         file_path = os.path.join(root, file)
    #         with open(file_path, 'rb') as f:
    #             writer.add_attachment(file, f.read())
    
    # # Save final PDF
    # output = BytesIO()
    # writer.write(output)
    # # return output.getvalue()

    # # Write final PDF to disk
    # with open(output_path, 'wb') as output_file:
    #     writer.write(output_file)
    
    
if __name__ == "__main__":
    # Sample data
    with open('generated/data/print_safaricom_data.json', 'r', encoding='utf-8') as f:
        print_data = json.load(f)
    generate_pdf(print_data, "generated/reports/print_safaricom.pdf")
