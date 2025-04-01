from pptx import Presentation
import json
from app.reporters.ppt_generators.slides.title_slide import add_title_slide
from app.reporters.ppt_generators.slides.volume_of_mentions import add_volume_mentions_slide_area_chart
from app.reporters.ppt_generators.slides.sentiment import add_sentiment_slide
from app.reporters.ppt_generators.slides.trends import add_trends_topics_slide
from app.reporters.ppt_generators.slides.share_of_voice import add_share_of_voice_slide
from app.reporters.ppt_generators.slides.demographics import add_demographics_slide
from app.reporters.ppt_generators.slides.influencers import add_influencers_slide
from app.reporters.ppt_generators.slides.mentions import add_mentions_slide
from app.reporters.ppt_generators.slides.source_title_slide import add_source_title_slide
from datetime import datetime

def check_data(data: dict, key_to_check: str) -> bool:
    # Check if data exists and is dictionary
    if not data or not isinstance(data, dict):
        return False
    
    # Check if key exists
    if key_to_check not in data:
        return False
    
    return True


def generate_pptx(data, template_path, output_path, date_format, report_date):
    try:
        # Can use either .potx or .pptx
        prs = Presentation(template_path)
        
        # title slide
        add_title_slide(
            prs, 
            "DIGITAL", 
            data['account']['brand_colors']['primary'],
            data['account']['logo']
        )
        
        
        sources_data = [
            {
                "source": key, 
                "data": {**value, "account": data["account"]}
            } 
            for key, value in data.items() 
            if key != "account"
        ]
        
        for source in sources_data:
            
            # source title slide
            add_source_title_slide(
                prs, 
                source['source'], 
                data['account']['brand_colors']['primary'],
                data['account']['logo']
            )
            
            volume_mentions_render = check_data(source['data'], 'volume_mentions')
            
            if volume_mentions_render and isinstance(source['data']['volume_mentions']['dates'], list) and len(source['data']['volume_mentions']['dates']) > 0:
                # volume of mentions
                add_volume_mentions_slide_area_chart(
                    prs, 
                    source['data'], 
                    date_format,
                    report_date,
                    f"Volume Of Mentions - {source['source']}"
                )

            # sentiments
            sentiments_render = check_data(source['data'], 'sentiment')
            sentiment_mentions_render = check_data(source['data'], 'sentiment_mentions')
            if sentiments_render and sentiment_mentions_render:
                add_sentiment_slide(
                    prs, 
                    source['data'], 
                    report_date, 
                    f"Sentiment Analysis - {source['source']}")
        
            # trending topics and keywords slide
            trending_topics_render = check_data(source['data'], 'trending_topics')
            if trending_topics_render:
                add_trends_topics_slide(
                    prs, 
                    source['data'], 
                    report_date,
                    f"TRENDING TOPICS AND KEYWORDS - {source['source']}"
                )
        
            # share of voice slide
            share_of_voice_render = check_data(source['data'], 'share_of_voice')
            if share_of_voice_render:
                add_share_of_voice_slide(
                    prs, 
                    source['data'], 
                    report_date,
                    f"SHARE OF VOICE - {source['source']}"
                )
        
            # demographics slide
            demographics_render = check_data(source['data'], 'gender_data')
            if demographics_render:
                add_demographics_slide(
                    prs, 
                    source['data'], 
                    report_date,
                    f"DEMOGRAPHICS - {source['source']}"
                )
        
            # influencers slide
            influencers_render = check_data(source['data'], 'influencers')
            if influencers_render:
                add_influencers_slide(
                    prs, 
                    source['data'], 
                    report_date,
                    f"TOP INFLUENCERS - {source['source']}"
                )
        
        # mentions slides
        # add_mentions_slide(prs, data, report_date, "digital")
        
        prs.save(output_path)
        print(f"Presentation saved successfully to {output_path}")
    except Exception as e:
        print(f"Error generating presentation: {e}")
        raise