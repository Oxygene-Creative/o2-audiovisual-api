from app.reporters.ppt_generators.slides.colors import hex_to_rgb, change_text_color
from app.reporters.ppt_generators.slides.header import slide_header
from pptx.dml.color import RGBColor

def bind_common_placeholders(prs, slide, data, report_date):
    primary_color_rgb = hex_to_rgb(data['account']['brand_colors']['primary'])
    text_color_rgb = hex_to_rgb("#666666")
    slide_header(report_date, data, slide, prs.slide_width, 12)
    
    heading = slide.placeholders[20] 
    heading.text = "MENTIONS"
    change_text_color(heading, primary_color_rgb)
    
def add_mention_link(placeholder, id, report_type, primary_color_rgb, data=None):
    # Add text with hyperlink for handle
    link_frame = placeholder.text_frame
    link_frame.clear()  # Clear existing text
    p = link_frame.paragraphs[0]
    run = p.add_run()
    run.text = "Read Article"
    if report_type == 'print':
        run.text = "Read Article"
        run.hyperlink.address = f"https://ai.oxygene.co.ke/app/viewer?type=image&id={id}"
    elif report_type == 'digital':
        run.text = "Read Article"
        # run.hyperlink.address = f"https://ai.oxygene.co.ke/app/viewer?type=webpage&id={id}"
        run.hyperlink.address = data['website_address']
    elif report_type == 'tv':
        run.text = "Watch Video"
        run.hyperlink.address = f"https://ai.oxygene.co.ke/app/viewer?type=video&id={id}"
    elif report_type == 'radio':
        run.text = "Play Audio"
        run.hyperlink.address = f"https://ai.oxygene.co.ke/app/viewer?type=audio&id={id}"
    
    run.font.underline = True
    run.font.color.rgb = RGBColor(*primary_color_rgb)
    
def add_mentions_slide(prs, data, report_date, report_type):
    try:
        # Add inluencers slide
        mentions_layout = [layout for layout in prs.slide_layouts 
                            if layout.name == "Mentions Slide"][0]
        primary_color_rgb = hex_to_rgb(data['account']['brand_colors']['primary'])
        placeholder_indices = [
            {'heading': 21, 'summary': 22, 'metadata': 23, 'link': 24},     
            {'heading': 25, 'summary': 26, 'metadata': 27, 'link': 28},
            {'heading': 29, 'summary': 30, 'metadata': 31, 'link': 32}
        ]  
        
        quotient, remainder = divmod(len(data['mentions']), 3)
        # calc no of slides and unused placeholders to remove later on
        if remainder > 0:
            no_slides = quotient + 1
            no_unused_placeholders = 3 - remainder
            unused_placeholders = placeholder_indices[-no_unused_placeholders:]  
        else:
            no_slides = quotient
            unused_placeholders = []  
        
        # grab the last slide
        slide = None
        placeholders = None
        for i in range(no_slides):
            mentions_batch = data['mentions'][i:i+3]
            # generate slide per batch
            slide = prs.slides.add_slide(mentions_layout)
            # Bind some common placeholders
            bind_common_placeholders(prs, slide, data, report_date)
            # Get all placeholders
            placeholders = slide.placeholders
            
            for batch_index, mention in enumerate(mentions_batch):
                mention_index = (i*3) + batch_index
                try:
                    # Get placeholders using indices
                    heading_idx = placeholder_indices[batch_index]['heading']
                    heading = placeholders[heading_idx]
                    summary_idx = placeholder_indices[batch_index]['summary']
                    summary = placeholders[summary_idx]
                    metadata_idx = placeholder_indices[batch_index]['metadata']
                    metadata = placeholders[metadata_idx]
                    link_idx = placeholder_indices[batch_index]['link']
                    link = placeholders[link_idx]
                    
                    # Populate data
                    summary.text = mention.get('summary', '')
                    add_mention_link(link, 12, report_type, primary_color_rgb, data['mentions'][mention_index])
                    
                    if report_type == 'print':
                        heading.text = mention.get('heading', '')
                        metadata.text = f"Author: {mention.get('author', '')}, Date: {mention.get('date', '')}, Publication: {mention.get('publication', '')}"
                    elif report_type == 'digital':
                        heading.text = f"{mention.get('headline', '')}"
                        metadata.text = f"Author: {mention.get('author', '')}, Date: {mention.get('date', '')}, Website: {mention.get('website', '')}"
                    elif report_type == 'tv':
                        heading.text = f"Show: {mention.get('show', '')} by {mention.get('presenter', '')}"
                        metadata.text = f"Date: {mention.get('date', '')}, {mention.get('time', '')}, Station: {mention.get('station', '')}"
                    elif report_type == 'radio':
                        heading.text = f"Show: {mention.get('show', '')} by {mention.get('presenter', '')}"
                        metadata.text = f"Date: {mention.get('date', '')}, {mention.get('time', '')}, Station: {mention.get('station', '')}"
                    
                except KeyError as e:
                    print(f"Couldn't find placeholder: {e}")
                except Exception as e:
                    print(f"Error processing mention {mention_index + 1}: {e}")  
        
        # Get indices to remove
        indices_to_remove = []
        for idx, indices in enumerate(unused_placeholders):
            indices_to_remove.extend(indices.values())
        
        # # Remove shapes that match our unused indices
        for idx in indices_to_remove:
            shape = placeholders[idx]
            try:
                element = shape._element
                element.getparent().remove(element)
            except Exception as e:
                print(f"Error removing placeholder {idx}: {e}")

    except Exception as e:
        print(f"Error creating mentions slide: {e}")
        raise
