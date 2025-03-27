from PIL import Image
from app.reporters.ppt_generators.slides.colors import hex_to_rgb, change_text_color
from app.reporters.ppt_generators.slides.header import slide_header
from app.reporters.charts.wordcloud import create_word_cloud
from app.reporters.ppt_generators.slides.images import base64_to_image

def add_trends_topics_slide(prs, data, report_date):
    try:
        # Add trending topics slide
        side_picture_layout = [layout for layout in prs.slide_layouts 
                            if layout.name == "Side Picture Slide"][0]
        slide = prs.slides.add_slide(side_picture_layout)
        
        primary_color_rgb = hex_to_rgb(data['account']['brand_colors']['primary'])
        text_color_rgb = hex_to_rgb("#666666")
        slide_header(report_date, data, slide, prs.slide_width, 12)
        
        heading = slide.placeholders[20] 
        heading.text = "TRENDING TOPICS AND KEYWORDS"
        change_text_color(heading, primary_color_rgb)
        
        summary = slide.placeholders[21] 
        summary.text = data['trending_topics_summary']
        change_text_color(summary, text_color_rgb)
        
        # create wordcloud
        trending_topics_chart = create_word_cloud( data['trending_topics'])
        trending_topics_chart_stream = base64_to_image(trending_topics_chart)
        
        # insert wordcloud
        wordcloud_placeholder = slide.placeholders[11]
        
        if wordcloud_placeholder.is_placeholder:
            trending_topics_image = Image.open(trending_topics_chart_stream)
            image_width, image_height = trending_topics_image.size 
            image_aspect_ratio = image_width / image_height
            
            picture = wordcloud_placeholder.insert_picture(trending_topics_chart_stream)  
            # Resize the picture to fit the aspect ratio properly
            # if picture.width / picture.height != image_aspect_ratio:
            #     picture.height = int(picture.width / image_aspect_ratio)

        
    except Exception as e:
        print(f"Error creating trends and topics slide: {e}")
        raise
    