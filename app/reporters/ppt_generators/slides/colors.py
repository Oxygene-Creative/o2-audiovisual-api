from pptx.dml.color import RGBColor

def hex_to_rgb(hex_color):
    """Convert hex color (e.g., '#FF5733') to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

def change_text_color(target, target_color_rgb):
    for paragraph in target.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(*target_color_rgb) 
