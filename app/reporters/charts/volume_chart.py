import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import DateFormatter
import io
import base64
from matplotlib.ticker import MaxNLocator
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
from app.reporters.ppt_generators.slides.colors import hex_to_rgb
from pptx.dml.color import RGBColor

def create_volume_chart(dates, values, date_format='auto'):
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

def create_volume_chart_ppt(placeholder, dates, values, date_format, color_hex):
    if placeholder.is_placeholder:
        # Prepare the chart data
        chart_data = CategoryChartData()

        if date_format == 'hourly':
            categories = [date.strftime("%H:%M") for date in dates]
            chart_data.categories = categories
        elif date_format == 'daily':
            categories = [date.strftime("%d %b").lstrip("0") for date in dates]
            chart_data.categories = categories

        chart_data.add_series("Mentions", values)

        # Add a line chart to the placeholder
        chart = placeholder.insert_chart(
            XL_CHART_TYPE.AREA, chart_data 
        ).chart

        # Format Series
        chart.has_title = False
        chart.series[0].format.fill.solid()
        chart_rgb_color = hex_to_rgb(color_hex)
        chart.series[0].format.fill.fore_color.rgb = RGBColor(*chart_rgb_color)