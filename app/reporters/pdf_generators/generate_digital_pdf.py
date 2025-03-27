from datetime import datetime
from weasyprint import HTML, CSS
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
import json
from app.reporters.charts.volume_chart import create_volume_chart
from app.reporters.charts.donurt_chart import create_donut_chart
from app.reporters.charts.wordcloud import create_word_cloud
from app.reporters.charts.pie_chart import create_pie_chart

def calculate_bar_widths(metrics):
    max_retweets = max(float(m['retweets']) for m in metrics)
    max_comments = max(int(m['comments']) for m in metrics)
    
    for metric in metrics:
        metric['retweets_width'] = (float(metric['retweets']) / max_retweets) * 100
        metric['comments_width'] = (int(metric['comments']) / max_comments) * 100
    
    return metrics

def generate_pdf(data, output_path):
    css = CSS('templates/reports.css')
    env = Environment(loader=FileSystemLoader('./templates'))
    template = env.get_template('digital_report.html')
    
    # Generate charts
    # Create volume chart
    volume_chart = create_volume_chart(
        data['volume_data']['dates'],
        data['volume_data']['values'], 
        date_format='hourly'
    )
    
    # Create volume chart
    reach_chart = create_volume_chart(
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
        # account details
        account_name=data['account']['name'],
        account_logo=data['account']['logo'],
        brand_colors=data['account']['brand_colors'],
        report_date=datetime.now().strftime('%d %b %Y'),
        # volume of mentions
        volume_summary=data['volume_summary'],
        volume_mentions_summary=data['volume_mentions_summary'],
        volume_chart=volume_chart,
        # sentiment
        sentiment_summary=data['sentiment_summary'],
        sentiment_mentions_summary=data['sentiment_mentions_summary'],
        sentiment_chart=sentiment_chart,
        sentiment_sources_chart=sentiment_sources_chart,
        sentiment_mentions=data['sentiment_mentions'],
        # reach and impressions
        reach_chart=reach_chart,
        reach_summary=data['reach_summary'],
        reach_mentions_summary=data['reach_mentions_summary'],
        # share of voice
        sov_summary=data['sov_summary'],
        share_of_voice_chart=share_of_voice_chart,
        # trends
        trends_summary=data['trending_topics_summary'],
        trending_topics_chart=trending_topics_chart,
        # demgraphics
        gender_chart=gender_chart,
        gender_summary=data['gender_summary'],
        # influencers
        influencers=data['influencers'],
        # engagement
        engagement_summary=data['engagement_summary'],
        engagement_metrics=data['engagement_metrics'],
        # mentions
        mentions=data['mentions'],
        # others
        app_base_url="http://ai.oxygene.co.ke"
    )
    
    HTML(string=html_content).write_pdf(target=output_path, stylesheets=[css])

# if __name__ == "__main__":
#     # Sample data
#     with open('./reporters/samples/data/digital_safaricom_data.json', 'r', encoding='utf-8') as f:
#         digital_data = json.load(f)
#     generate_pdf(digital_data, "./reporters/samples/reports/digital_safaricom.pdf")

