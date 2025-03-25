from datetime import datetime
from weasyprint import HTML, CSS
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
import json
from app.reporters.charts.volume_chart import create_volume_chart
from app.reporters.charts.donurt_chart import create_donut_chart
from app.reporters.charts.wordcloud import create_word_cloud
from app.reporters.charts.pie_chart import create_pie_chart

def generate_pdf(data, output_path):
    css = CSS('templates/reports.css')
    env = Environment(loader=FileSystemLoader('./templates'))
    template = env.get_template('radio_report.html')
    
    # Create volume chart
    volume_chart = create_volume_chart(
        data['volume_data']['dates'],
        data['volume_data']['values'], 
        date_format='hourly'
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
    
    # create gender chart
    gender_chart = create_donut_chart(
        data['gender_data']['labels'],
        data['gender_data']['values'],
        data['gender_data']['colors'],
        legend_position='right'
    )
    
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
        gender_chart=gender_chart,
        gender_summary=data['volume_summary'],
        app_base_url="http://ai.oxygene.co.ke",
        mentions=data['mentions']
    )
    
    HTML(string=html_content).write_pdf(target=output_path, stylesheets=[css])

if __name__ == "__main__":
    # Sample data
    with open('generated/data/radio_eabl_data.json', 'r', encoding='utf-8') as f:
        radio_data = json.load(f)
    generate_pdf(radio_data, "generated/reports/radio_eabl.pdf")
    
