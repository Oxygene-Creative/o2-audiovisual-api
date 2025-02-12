from inaSpeechSegmenter import Segmenter
from inaSpeechSegmenter.export_funcs import seg2csv
from app.core.audio import delete_file
import os

def gender_music_segmentation(audio_file, gcs_path):
    seg = Segmenter('smn', True)
    segmentation = seg(audio_file)
    csv_file = f"recordings/{os.path.basename(gcs_path)}.csv"
    # Export results to CSV
    seg2csv(segmentation, csv_file)
    # add file name
    df = pd.read_table(csv_file)
    df["length"] = df['stop'] - df['start']
    # Compute the aggregated length of all sequences by label
    df_aggregated = df[['labels', 'length']].groupby("labels").sum().reset_index()
    
    delete_file(audio_file)
    delete_file(csv_file)
    
    return df_aggregated.to_dict(orient='records')