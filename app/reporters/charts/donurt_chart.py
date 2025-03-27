import matplotlib.pyplot as plt
import io
import base64
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
from pptx.util import Inches, Pt

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

def create_donut_chart_ppt(placeholder, categories, series, chart_colors):
    if placeholder.is_placeholder:
        # Prepare the chart data
        chart_data = CategoryChartData()
        chart_data.categories = categories
        chart_data.add_series("Title", series)
        
        # Add a line chart to the placeholder
        chart = placeholder.insert_chart(
            XL_CHART_TYPE.DOUGHNUT, chart_data 
        ).chart
        
        # Format Chart
        chart.has_title = False
        # Apply colors to each segment of the donut based on the new RGBColor array
        for i, point in enumerate(chart.series[0].points):
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = RGBColor(*chart_colors[i])

        # Add data labels to the donut chart
        for series in chart.series:
            series.data_labels.show_percentage = True
            series.data_labels.number_format = "0%"   
            series.data_labels.font.size = Inches(0.2)
