from jinja2 import Environment, FileSystemLoader
from app.reporters.charts import create_donut_chart, create_pie_chart, create_volume_chart, create_wordcloud
from weasyprint import HTML
import json
from datetime import datetime

def generate_av_report(data):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('templates/av_spdf_template.html')
    
    # Generate charts
    volume_chart = create_volume_chart(data['volume_data'])
    sources_chart = create_donut_chart(
        data['sources'], 
        data['sources']['labels'], 
        data['sources']['values']
    )
    sentiment_chart = create_donut_chart(
        data['sentiment'],
        data['sentiment']['labels'],
        data['sentiment']['values']
    )
    
    # Create wordcloud
    wordcloud_image = create_wordcloud(data['trending_topics'])
    
    # Create pie chart
    pie_chart = create_pie_chart(
        data['sov_labels'],
        data['sov_values'],
        data['sov_colors']
    )

    # Render template
    html_content = template.render(
        report_date=datetime.now().strftime('%d OCTOBER %Y'),
        volume_summary=data['volume_summary'],
        sentiment_summary=data['sentiment_summary'],
        volume_chart=volume_chart,
        sources_chart=sources_chart,
        sentiment_chart=sentiment_chart,
        wordcloud_image=wordcloud_image,
        pie_chart=pie_chart,
        trends_summary=data['trends_summary'],
        sov_summary=data['sov_summary'],
        plotly_js='<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
    )

    # Generate PDF
    HTML(string=html_content).write_pdf('report.pdf')