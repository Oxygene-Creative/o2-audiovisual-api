import matplotlib.pyplot as plt
import io
import base64

def create_donut_chart(labels, values, colors, legend_position='right'):
    """Create a donut chart"""
    plt.figure(figsize=(16, 16))
    
    plt.rcParams.update({
        'font.size': 18,        # Base font size
        'font.weight': 'bold',  # Make labels bold
    })
    
    # Create donut chart
    patches, texts, autotexts = plt.pie(
        values, 
        labels=None,  # Remove labels from pie itself
        colors=colors, 
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5)
    )
    
    # Format percentage labels
    plt.setp(autotexts, size=14, weight='bold', color='white')
    
    # Configure legend position
    legend_params = {
        'right': {'loc': 'center left', 'bbox_to_anchor': (1, 0.5)},
        'left': {'loc': 'center right', 'bbox_to_anchor': (0, 0.5)},
        'top': {'loc': 'lower center', 'bbox_to_anchor': (0.5, 1.15)},
        'bottom': {'loc': 'upper center', 'bbox_to_anchor': (0.5, -0.15)}
    }
    
    # Get legend parameters based on position
    legend_config = legend_params.get(
        legend_position.lower(),
        legend_params['right']  # default to right if invalid position given
    )
    
    # Add legend with horizontal layout at bottom
    plt.legend(
        patches,
        [f'{l} ({v}%)' for l, v in zip(labels, values)],
        frameon=False,
        fontsize=18,
        **legend_config
    )
    
    plt.axis('equal')
    
    # Adjust layout to prevent legend cutoff
    plt.tight_layout()
    
    # Save to bytes
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()
