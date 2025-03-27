from app.reporters.ppt_generators.slides.colors import hex_to_rgb, change_text_color
from app.reporters.ppt_generators.slides.header import slide_header
from app.reporters.charts.donurt_chart import create_donut_chart_ppt

def add_sentiment_slide(prs, data, report_date):
    try:
        # Add sentiments slide
        sentiment_layout = [layout for layout in prs.slide_layouts 
                            if layout.name == "Sentiment Slide"][0]
        slide = prs.slides.add_slide(sentiment_layout)
        
        primary_color_rgb = hex_to_rgb(data['account']['brand_colors']['primary'])
        text_color_rgb = hex_to_rgb("#666666")
        slide_header(report_date, data, slide, prs.slide_width, 12)
        
        heading = slide.placeholders[20] 
        heading.text = "SENTIMENT ANALYSIS"
        change_text_color(heading, primary_color_rgb)
        
        summary = slide.placeholders[21] 
        summary.text = data['sentiment_summary']
        change_text_color(summary, text_color_rgb)
        
        mentions_summary = slide.placeholders[22] 
        mentions_summary.text = data['sentiment_mentions_summary']
        change_text_color(mentions_summary, text_color_rgb)
        
        sentiment_chart = slide.placeholders[23]
        sentiment_chart_colors = [hex_to_rgb(color) for color in data['sentiment']['colors']]
        create_donut_chart_ppt(
            sentiment_chart,
            data['sentiment']['labels'],
            data['sentiment']['values'],
            sentiment_chart_colors
        )
        
        sentiment_sources_chart = slide.placeholders[24]
        sentiment_sources_chart_colors = [hex_to_rgb(color) for color in data['sentiment_sources']['colors']]
        create_donut_chart_ppt(
            sentiment_sources_chart,
            data['sentiment_sources']['labels'],
            data['sentiment_sources']['values'],
            sentiment_sources_chart_colors
        )
        
        total_sentiments = slide.placeholders[25]
        total_sentiments.text = str(data['sentiment_mentions']['total'])
        
        positive_sentiments = slide.placeholders[26]
        positive_sentiments.text = str(data['sentiment_mentions']['positive'])
        positive_sentiments_color = hex_to_rgb("#43B02A")
        change_text_color(positive_sentiments, positive_sentiments_color)
        
        negative_sentiments = slide.placeholders[27]
        negative_sentiments.text = str(data['sentiment_mentions']['negative'])
        negative_sentiments_color = hex_to_rgb("#FF4444")
        change_text_color(negative_sentiments, negative_sentiments_color)
        
        neutral_sentiments = slide.placeholders[28]
        neutral_sentiments.text = str(data['sentiment_mentions']['neutral'])
        neutral_sentiments_color = hex_to_rgb("#808080")
        change_text_color(neutral_sentiments, neutral_sentiments_color)
        
    except Exception as e:
        print(f"Error creating sentiment slide: {e}")
        raise
