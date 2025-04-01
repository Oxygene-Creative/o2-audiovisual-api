from app.reporters.ppt_generators.slides.colors import hex_to_rgb, change_text_color
from app.reporters.ppt_generators.slides.header import slide_header
from app.reporters.charts.pie_chart import create_pie_chart_ppt

def add_share_of_voice_slide(prs, data, report_date, title="SHARE OF VOICE"):
    try:
        # Add share of voice slide
        side_chart_layout = [layout for layout in prs.slide_layouts 
                            if layout.name == "Side Chart Slide"][0]
        slide = prs.slides.add_slide(side_chart_layout)
        
        primary_color_rgb = hex_to_rgb(data['account']['brand_colors']['primary'])
        text_color_rgb = hex_to_rgb("#666666")
        slide_header(report_date, data, slide, prs.slide_width, 12)
        
        heading = slide.placeholders[20] 
        heading.text = title.upper()
        change_text_color(heading, primary_color_rgb)
        
        summary = slide.placeholders[21] 
        summary.text = data['sov_summary']
        change_text_color(summary, text_color_rgb)
        
        # create pie chart
        sov_chart = slide.placeholders[23]
        sov_chart_colors = [hex_to_rgb(color) for color in data['share_of_voice']['colors']]
        create_pie_chart_ppt(
            sov_chart,
            data['share_of_voice']['labels'],
            data['share_of_voice']['values'],
            sov_chart_colors
        )
        
    except Exception as e:
        print(f"Error creating share of voice slide: {e}")
        raise
