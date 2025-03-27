import matplotlib.pyplot as plt
import io
import base64
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

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

def create_bar_chart_ppt(placeholder, categories, values, chart_colors):
    if placeholder.is_placeholder:
        # Add chart data
        chart_data = CategoryChartData()
        chart_data.categories = categories
        chart_data.add_series('Series 1', values)

        # Add chart to slide
        chart = placeholder.insert_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            chart_data
        ).chart
        
        # Format Chart
        chart.has_title = False
        # Apply different colors to individual bars (if single series)
        for i, point in enumerate(chart.series[0].points):
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = RGBColor(*chart_colors[i])
            
        # Customize legend
        chart.has_legend = True                        
        chart.legend.position = XL_LEGEND_POSITION.RIGHT                 
        chart.legend.font.size = Inches(0.2)           
        chart.legend.include_in_layout = False 
        
        # Add data labels to the chart
        for series in chart.series:
            series.data_labels.show_percentage = True
            series.data_labels.number_format = "0%"   
            series.data_labels.font.size = Inches(0.2)