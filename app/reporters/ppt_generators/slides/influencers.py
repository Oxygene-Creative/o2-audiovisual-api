from app.reporters.ppt_generators.slides.colors import hex_to_rgb, change_text_color
from app.reporters.ppt_generators.slides.header import slide_header
import requests
from io import BytesIO

def add_influencers_slide(prs, data, report_date, title="TOP INFLUENCERS"):
    try:
        # Add inluencers slide
        influencers_layout = [layout for layout in prs.slide_layouts 
                            if layout.name == "influencers Slide"][0]
        slide = prs.slides.add_slide(influencers_layout)
        
        primary_color_rgb = hex_to_rgb(data['account']['brand_colors']['primary'])
        text_color_rgb = hex_to_rgb("#666666")
        slide_header(report_date, data, slide, prs.slide_width, 21)
        
        heading = slide.placeholders[20] 
        heading.text = title.upper()
        change_text_color(heading, primary_color_rgb)
        
        # Get all placeholders
        placeholders = slide.placeholders
        placeholder_indices = [
            {'pic': 11, 'name': 22, 'handle': 23, 'followers': 24},     
            {'pic': 25, 'name': 26, 'handle': 27, 'followers': 28},     
            {'pic': 29, 'name': 30, 'handle': 31, 'followers': 32},
            {'pic': 33, 'name': 34, 'handle': 35, 'followers': 36},     
            {'pic': 37, 'name': 38, 'handle': 39, 'followers': 40},     
            {'pic': 41, 'name': 42, 'handle': 43, 'followers': 44},
            {'pic': 45, 'name': 46, 'handle': 47, 'followers': 48},     
            {'pic': 49, 'name': 50, 'handle': 51, 'followers': 52},     
            {'pic': 53, 'name': 54, 'handle': 55, 'followers': 56},
        ]  
        
        # Process influencers
        for idx, (indices, influencer) in enumerate(zip(placeholder_indices, data['influencers'])):
            try:
                # Get placeholders using indices
                pic = placeholders[indices['pic']]
                name = placeholders[indices['name']]
                handle = placeholders[indices['handle']]
                followers = placeholders[indices['followers']]
                
                # Populate data
                if influencer.get('avatar'):
                    # Download the image
                    response = requests.get(influencer['avatar'])
                    if response.status_code == 200:
                        image_stream = BytesIO(response.content)
                        pic.insert_picture(image_stream)
                name.text = influencer.get('name', '')
                handle.text = f"@{influencer.get('screen_name', '')}"
                change_text_color(handle, primary_color_rgb)
                followers.text = f"{str(influencer.get('followers', ''))} followers"
                change_text_color(followers, text_color_rgb)
                
            except requests.RequestException as e:
                print(f"Error downloading image for influencer {idx + 1}: {e}")
            except KeyError as e:
                print(f"Couldn't find placeholder: {e}")
            except Exception as e:
                print(f"Error processing influencer {idx + 1}: {e}")  
        
        # Get indices to remove
        num_influencers = len(data['influencers'])
        indices_to_remove = []
        for idx, indices in enumerate(placeholder_indices[num_influencers:]):
            indices_to_remove.extend(indices.values())
        
        # Remove shapes that match our unused indices
        for idx in indices_to_remove:
            shape = placeholders[idx]
            try:
                element = shape._element
                element.getparent().remove(element)
            except Exception as e:
                print(f"Error removing placeholder {idx}: {e}")
        
    except Exception as e:
        print(f"Error creating influencers slide: {e}")
        raise
