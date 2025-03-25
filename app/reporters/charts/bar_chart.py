import matplotlib.pyplot as plt
import io
import base64

def create_bar_chart(labels, values, colors):
    plt.figure(figsize=(12, 8))
    
    # Set font properties
    plt.rcParams.update({
        'font.size': 14,
        'font.weight': 'normal',
    })
    
    # Create bar chart
    bars = plt.bar(
        labels,
        values,
        color=colors,
        width=0.6
    )
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center',
            va='bottom',
            size=14,
            weight='bold'
        )
    
    # Customize grid
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Customize axes
    plt.xlabel('Categories', fontsize=12, labelpad=10)
    plt.ylabel('Values', fontsize=12, labelpad=10)
    
    # Add legend
    plt.legend(
        bars,
        labels,
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        frameon=False,
        fontsize=12
    )
    
    # Adjust layout
    plt.tight_layout()
    
    # Convert to base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300, pad_inches=0.2)
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()

def create_horizontal_bar_chart(labels, values, colors):
    plt.figure(figsize=(16, 8))
    
    # Set font properties
    plt.rcParams.update({
        'font.size': 14,
        'font.weight': 'normal',
    })
    
    # Create horizontal bar chart
    bars = plt.barh(
        labels,
        values,
        color=colors,
        height=0.6
    )
    
    # Add value labels at the end of bars
    for bar in bars:
        width = bar.get_width()
        plt.text(
            width,
            bar.get_y() + bar.get_height()/2.,
            f'{int(width)}',
            ha='left',
            va='center',
            size=14,
            weight='bold',
        )
    
    # Customize grid
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Customize axes
    plt.xlabel('Values', fontsize=12, labelpad=10)
    plt.ylabel('Categories', fontsize=12, labelpad=10)
    
    # Add legend
    plt.legend(
        bars,
        labels,
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        frameon=False,
        fontsize=12
    )
    
    # Adjust layout
    plt.tight_layout()
    
    # Convert to base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300, pad_inches=0.2)
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()