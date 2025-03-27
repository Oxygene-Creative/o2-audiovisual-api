import matplotlib.pyplot as plt
import io
import base64
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import CategoryChartData
from pptx.util import Inches
from pptx.dml.color import RGBColor

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

def create_pie_chart_ppt(placeholder, categories, series, chart_colors):
    if placeholder.is_placeholder:
        # Define the chart data
        chart_data = CategoryChartData()
        chart_data.categories = categories
        chart_data.add_series("Series 1", series)
        
        # Add a line chart to the placeholder
        chart = placeholder.insert_chart(
            XL_CHART_TYPE.PIE, chart_data 
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
            
        # Enable and customize the legend
        chart.has_legend = True                        
        chart.legend.position = XL_LEGEND_POSITION.RIGHT                 
        chart.legend.font.size = Inches(0.2)           
        chart.legend.include_in_layout = False 
        