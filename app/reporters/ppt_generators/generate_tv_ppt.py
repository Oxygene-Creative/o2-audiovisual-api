from pptx import Presentation
from datetime import datetime
import json
from app.reporters.ppt_generators.slides.title_slide import add_title_slide
from app.reporters.ppt_generators.slides.volume_of_mentions import add_volume_mentions_slide_area_chart
from app.reporters.ppt_generators.slides.sentiment import add_sentiment_slide
from app.reporters.ppt_generators.slides.trends import add_trends_topics_slide
from app.reporters.ppt_generators.slides.share_of_voice import add_share_of_voice_slide
from app.reporters.ppt_generators.slides.demographics import add_demographics_slide
from app.reporters.ppt_generators.slides.mentions import add_mentions_slide

def generate_pptx(data, template_path, output_path, date_format, report_date):
    try:
        # Can use either .potx or .pptx
        prs = Presentation(template_path)
        
        # title slide
        add_title_slide(
            prs, 
            "RADIO BROADCAST", 
            data['account']['brand_colors']['primary'],
            data['account']['logo']
        )
        
        # volume of mentions
        add_volume_mentions_slide_area_chart(
            prs, 
            data, 
            date_format,
            report_date
        )
        
        # sentiments
        add_sentiment_slide(prs, data, report_date)
        
        # trending topics and keywords slide
        add_trends_topics_slide(prs, data, report_date)
        
        # share of voice slide
        add_share_of_voice_slide(prs, data, report_date)
        
        # demographics slide
        add_demographics_slide(prs, data, report_date)
        
        # mentions slides
        add_mentions_slide(prs, data, report_date, "tv")
        
        prs.save(output_path)
        print(f"Presentation saved successfully to {output_path}")
    except Exception as e:
        print(f"Error generating presentation: {e}")
        raise

# if __name__ == "__main__":
#     try:
#         template_path = "templates/ppt_template.pptx"  # Use .potx extension
#         output_path = "./reporters/samples/reports/tv_ncba.pptx"  # Save as .pptx

#         # Load sample data
#         with open('./reporters/samples/data/tv_ncba_data.json', 'r', encoding='utf-8') as f:
#             tv_data = json.load(f)
        
#         report_date = datetime.now().strftime('%d %B %Y')
        
#         generate_pptx(tv_data, template_path, output_path, "hourly", report_date)
#     except Exception as e:
#         print(f"Error in main: {e}")