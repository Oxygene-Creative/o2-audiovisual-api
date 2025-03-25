import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import DateFormatter
import io
import base64
from matplotlib.ticker import MaxNLocator
def create_volume_chart(dates, values, date_format='auto'):
    """
    Create a volume/area chart
    
    Parameters:
    dates: list of dates (can be strings or datetime objects)
    values: list of numerical values
    date_format: str, optional
        'auto': automatically detect format
        'monthly': for monthly data (e.g., '2023-01')
        'hourly': for datetime with hours (e.g., '2023-01-01 00:00') - will show only hours
        'daily': for daily data (e.g., '2023-01-01')
    """
    plt.figure(figsize=(12, 4))
    
    # Set the font sizes
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12
    })

    ax = plt.gca()
    
    # Convert dates and set formatter
    if isinstance(dates[0], str):
        if date_format == 'monthly':
            dates = pd.to_datetime(dates, format='%Y-%m')
            ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))
            
        elif date_format == 'hourly':
            # Convert datetime strings but show only hours
            dates = pd.to_datetime(dates)
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(MaxNLocator(min(len(dates), 12)))
            
        elif date_format == 'daily':
            dates = pd.to_datetime(dates)
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
            
        else:  # auto detect
            dates = pd.to_datetime(dates)
            if any(d.hour != 0 or d.minute != 0 for d in dates):
                ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
                ax.xaxis.set_major_locator(MaxNLocator(min(len(dates), 12)))
            else:
                ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    
    # Create the area chart
    plt.fill_between(dates, values, alpha=0.3, color='#4CAF50')
    plt.plot(dates, values, color='#4CAF50', linewidth=2)
    
    # Customize the chart
    plt.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
    
    # Remove padding/margins
    plt.margins(x=0, y=0)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save to bytes
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()