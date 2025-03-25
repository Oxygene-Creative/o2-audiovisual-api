import matplotlib.pyplot as plt
import io
import base64

def create_pie_chart(labels, values, colors):
    plt.figure(figsize=(12, 8))
    
    # Set font properties
    plt.rcParams.update({
        'font.size': 14,
        'font.weight': 'normal',
    })
    
    # Create pie chart
    patches, texts, autotexts = plt.pie(
        values,
        labels=labels,
        colors=colors,
        autopct='%d%%',  # Show percentages as integers
        startangle=90,    # Rotate start of pie
        pctdistance=0.85, # Distance of percentage labels from center
    )
    
    # Format percentage labels
    plt.setp(autotexts, size=14, weight='bold', color='white')
    plt.setp(texts, size=14)
    
    # Add legend
    plt.legend(
        patches,
        labels,
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        frameon=False,
        fontsize=12
    )
    
    plt.axis('equal')
    
    # Convert to base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300, pad_inches=0.2)
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()
