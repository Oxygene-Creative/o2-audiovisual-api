from app.reporters.ppt_generators.slides.colors import hex_to_rgb, change_text_color
from app.reporters.ppt_generators.slides.images import sanitize_image
from pathlib import Path

def add_source_title_slide(prs, title_heading, primary_color_hex, logo_base64):
    try:
        # Add title slide
        title_layout = [layout for layout in prs.slide_layouts 
                        if layout.name == "Sources Title Slide"][0]
        title_slide = prs.slides.add_slide(title_layout)
        
        # Access existing placeholders
        title = title_slide.placeholders[0]  
        
        # Set the text
        title.text = title_heading.upper()
        
        # Text color
        text_color_rgb = hex_to_rgb(primary_color_hex)
        change_text_color(title, text_color_rgb)

    except Exception as e:
        print(f"Error creating title slide: {e}")
