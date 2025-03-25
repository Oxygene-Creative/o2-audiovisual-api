import matplotlib.pyplot as plt
import io
import base64
from wordcloud import WordCloud

def create_word_cloud(word_frequencies):
    # Create WordCloud object
    wordcloud = WordCloud(
        width=600,
        height=400,
        background_color='white',
        colormap='viridis',  # Color scheme
        max_words=100,
        min_font_size=10,
        max_font_size=150,
        prefer_horizontal=0.7,  # 70% of words will be horizontal
        random_state=42  # For reproducibility
    ).generate_from_frequencies(word_frequencies)
    
    # Create figure and display word cloud
    plt.figure(figsize=(16, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  # Hide axes
    
    # Convert to base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300, pad_inches=0)
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()
