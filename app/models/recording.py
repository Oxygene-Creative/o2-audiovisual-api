from typing import Dict, List
from datetime import datetime, timedelta

class SegmentRecording:
    @staticmethod
    def create_segment_recordings_from_dict(data: dict) -> List[Dict]:
        segment_recordings = []

        # Iterate over each segment in the JSON data
        for segment in data.get("segments", []):
            if not isinstance(segment, dict):  # Ensure segment is a valid dictionary
                print(f"Invalid segment format: {segment}")
                continue

            # Ensure `raw_text` exists and has enough words
            raw_text = segment.get("raw_text", "").strip()
            word_count = len(raw_text.split())  # Count the number of words

            if not raw_text or word_count < 5: 
                continue
            # Derive the absolute timestamp for the segment
            timestamp = datetime.fromisoformat(data["timestamp"]) + timedelta(seconds=segment.get("start", 0.0))

            # Safely handle 'timestamp' and calculate segment timestamp
            try:
                base_timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
                timestamp = base_timestamp + timedelta(seconds=segment.get("start", 0.0))
            except (ValueError, TypeError) as e:
                print(f"Error parsing timestamp: {e}")
                timestamp = datetime.now()  # Fallback to current time
            
            # Create a dictionary representing the segment recording
            try:
                stream_type = "TV Station" if data.get("type") == "video" else "Radio Station"
                
                segment_record = {
                    "recording_id": data.get("id", ""),
                    "stream_id": data.get("stream_id", ""),
                    "source": { "name": data.get("stream_name", ""), "type": stream_type },
                    "timestamp": timestamp.isoformat(),
                    "duration": segment.get("duration", 0.0),
                    "raw_text": segment.get("raw_text", ""),
                    "language": segment.get("language", ""),
                    "language_score": segment.get("language_score", 0.0),
                    "sentiment": segment.get("sentiment", ""),
                    "emotions": segment.get("emotions", []),
                    "embeddings": segment.get("embeddings", []),
                    "tags": [
                        {**tag} for tag in segment.get("tags", []) if isinstance(tag, dict)
                    ],
                    "topics": [
                        {**topic} for topic in segment.get("topics", []) if isinstance(topic, dict)
                    ],
                    "ads": [
                        {
                            "brand": ad.get("brand", ""),
                            "product": ad.get("product", ""),
                            "start": ad.get("start", 0.0),
                            "stop": ad.get("stop", 0.0),
                        }
                        for ad in segment.get("ads", []) if isinstance(ad, dict)
                    ],
                    "engagement": [
                        {
                            "platform": engagement.get("platform", ""),
                            "identifier": engagement.get("identifier", ""),
                            "context": engagement.get("context", ""),
                            "start": engagement.get("start", 0.0),
                            "stop": engagement.get("stop", 0.0),
                        }
                        for engagement in segment.get("engagement", []) if isinstance(engagement, dict)
                    ],
                    "gcp_blob": data.get("gcp_blob", ""),
                    "gcp_path": segment.get("gcp_path", ""),
                    "file_size": segment.get("file_size", 0.0),
                    "host": segment.get("show_metadata", {}).get("host", ""),
                    "program_name": segment.get("show_metadata", {}).get("program_name", ""),
                }

                segment_recordings.append(segment_record)
            except Exception as e:
                print(f"Error creating segment recording dictionary: {e}")

        return segment_recordings


class Recording:

    @staticmethod
    def create_from_analysis_model(data: dict) -> Dict:
        # Safely handle 'timestamp'
        try:
            timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())).isoformat()
        except (ValueError, TypeError) as e:
            print(f"Error parsing timestamp: {e}")
            timestamp = datetime.now().isoformat()  # Fallback to current time

        # Safely extract activity metrics
        activity = data.get("activity", {})
        male = activity.get("male", 0.0)
        female = activity.get("female", 0.0)
        music = activity.get("music", 0.0)
        noise = activity.get("noise", 0.0)
        no_energy = activity.get("noEnergy", 0.0)

        # Safely calculate file size and duration
        total_file_size = sum(
            segment.get("file_size", 0.0) for segment in data.get("segments", []) if isinstance(segment, dict)
        )
        total_duration = sum(
            segment.get("duration", 0.0) for segment in data.get("segments", []) if isinstance(segment, dict)
        )

        # Safely determine the stream type
        stream_type = "TV_STREAM" if data.get("type") == "video" else "RADIO_STREAM"

        # Assemble the recording as a dictionary
        try:
            recording = {
                "id": data.get("id", ""),
                "timestamp": timestamp,
                "stream_name": data.get("stream_name", "Unknown Stream Name"),
                "stream_id": data.get("stream_id", "Unknown Stream ID"),
                "type": stream_type,
                "male": male,
                "female": female,
                "music": music,
                "noise": noise,
                "no_energy": no_energy,
                "file_size": total_file_size,
                "duration": total_duration,
            }
            print(recording)
            return recording
        except Exception as e:
            print(f"Error creating recording dictionary: {e}")
            return {}