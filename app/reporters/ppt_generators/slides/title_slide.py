from app.reporters.ppt_generators.slides.colors import hex_to_rgb, change_text_color
from app.reporters.ppt_generators.slides.images import sanitize_image

def add_title_slide(prs, title_heading, primary_color_hex, logo_base64):
    try:
        # Add title slide
        title_layout = [layout for layout in prs.slide_layouts 
                        if layout.name == "Title Slide"][0]
        title_slide = prs.slides.add_slide(title_layout)
        
        # Access existing placeholders
        title = title_slide.placeholders[0]  
        subtitle = title_slide.placeholders[1]  
        
        # Set the text
        title.text = title_heading
        subtitle.text = "MEDIA REPORT"
        
        # Text color
        text_color_rgb = hex_to_rgb(primary_color_hex)
        change_text_color(title, text_color_rgb)
        change_text_color(subtitle, text_color_rgb)
        
        # Set cover image
        cover_image_placeholder = title_slide.placeholders[12]
        report_cover_img = './templates/report-cover.jpg'
        report_cover_img_stream = sanitize_image(report_cover_img)
        cover_image_placeholder.insert_picture(report_cover_img_stream)
        
        # set logo
        logo_placeholder = title_slide.placeholders[15]
        logo_img_stream = sanitize_image(logo_base64)
        logo_placeholder.insert_picture(logo_img_stream)

    except Exception as e:
        print(f"Error creating title slide: {e}")
