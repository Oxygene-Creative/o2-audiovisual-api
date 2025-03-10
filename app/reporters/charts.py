import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64

def create_volume_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['volumes'],
        fill='tozeroy'
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig.to_html(full_html=False)

def create_donut_chart(data, labels, values):
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.7
    )])
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig.to_html(full_html=False)

def create_wordcloud(text_data):
    wordcloud = WordCloud(
        width=800, 
        height=400,
        background_color='white',
        colormap='viridis'
    ).generate_from_frequencies(text_data)
    
    # Convert wordcloud to base64 image
    img = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0)
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()

def create_pie_chart(labels, values, colors):
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0,
        marker_colors=colors
    )])
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig.to_html(full_html=False)