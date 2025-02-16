from inaSpeechSegmenter import Segmenter
from inaSpeechSegmenter.export_funcs import seg2csv
import os
import pandas as pd
import uuid
from app.core.files import subfolder_check, delete_file

def speech_segments(df):
    # Drop rows where the label is 'music' and duration > 10
    df_filtered = df[~((df['labels'] == 'music') & (df['duration'] > 10))]

    # Drop rows where the label is 'noEnergy'
    df_filtered = df_filtered[~((df_filtered['labels'] == 'noEnergy'))]

    # Drop the 'duration' column if no longer needed
    df_filtered = df_filtered.drop('duration', axis=1)

    # Create a new column to identify whether rows should be grouped
    df_filtered['gap'] = (df_filtered['start'] - df_filtered['stop'].shift(1)) > 5  # True if gap exceeds 3 seconds
    df_filtered['group'] = df_filtered['gap'].cumsum()  # Create a group identifier by cumulative summing the `gap`

    # Create the new grouped DataFrame
    grouped_df = df_filtered.groupby('group', as_index=False).agg({
        'start': 'min',                    # Use the minimum start time of the group
        'stop': 'max'                      # Use the maximum stop time of the group
    })

    # Drop intermediate columns if necessary
    grouped_df = grouped_df.drop(columns='group')

    # Calculate the duration for each group
    grouped_df['duration'] = grouped_df['stop'] - grouped_df['start']

    return grouped_df.to_dict(orient='records')


def gender_music_segmentation(audio_file):
    # load segmentation model and segment audio file
    seg = Segmenter('smn', True)
    segmentation = seg(audio_file)

    # setup csv files
    subfolder_check(f"{os.getcwd()}/o2-files")
    csv_file = f"{os.getcwd()}/o2-files/{uuid.uuid4()}.csv"

    # Export results to CSV
    seg2csv(segmentation, csv_file)

    # add file name
    df = pd.read_table(csv_file)

    # Calculate the duration (stop - start)
    df['duration'] = df['stop'] - df['start']

    # Compute the aggregated length of all sequences by label
    df_aggregated = df[['labels', 'duration']].groupby("labels").sum().reset_index()

    # speech segments
    segments = speech_segments(df)

    delete_file(csv_file)

    return df_aggregated.to_dict(orient='records'), segments
    