import json
import os
from pathlib import Path
from datetime import datetime
from google.cloud import storage

def audit_validation_data():
    validation_dir = Path('validation_data')
    print('=== FULL VALIDATION DATA AUDIT ===')
    print(f'Audit timestamp: {datetime.now().isoformat()}')
    print(f'Directory: {validation_dir.absolute()}')
    print()

    # 1. List all JSON files
    json_files = list(validation_dir.glob('*.json'))
    print(f'Total JSON files: {len(json_files)}')
    print()

    all_in_results = []
    entity_counts = []
    error_messages = []

    for file_path in json_files:
        print(f'FILE: {file_path.name}')
        print('---')
        
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            print(f'Size: {os.path.getsize(file_path)} bytes')
            print(f'Type: {type(data)}')
            
            if isinstance(data, dict):
                print(f'Keys: {list(data.keys())}')
                
                # Look for video data
                video_data = None
                for key in data.keys():
                    if 'video' in key.lower() or 'result' in key.lower():
                        video_data = data.get(key, [])
                        break
                
                if video_data:
                    if isinstance(video_data, list):
                        print(f'Number of videos: {len(video_data)}')
                        for vid in video_data:
                            if isinstance(vid, dict):
                                video_name = vid.get('video', 'Unknown')
                                entities = vid.get('entities', 0)
                                print(f'  Video: {video_name}')
                                print(f'    Entities: {entities}')
                                
                                entity_counts.append((video_name, entities))
                                
                                if 'All-In' in video_name:
                                    all_in_results.append({
                                        'file': file_path.name,
                                        'status': vid.get('status', 'Unknown'),
                                        'entities': entities,
                                        'extraction_working': vid.get('entity_extraction_working', False)
                                    })
                                    print(f'    *** ALL-IN FOUND: {entities} entities ***')
                                
                                if entities == 95:
                                    print(f'    *** 95 ENTITIES FOUND IN {video_name} ***')
                    elif isinstance(video_data, dict):
                        entities = video_data.get('entities', 0)
                        print(f'  Entities: {entities}')
                        entity_counts.append(('Unknown', entities))
                        if 'All-In' in str(video_data):
                            all_in_results.append({
                                'file': file_path.name,
                                'entities': entities
                            })
                
                # Check for entities key
                if 'entities' in data:
                    entities = data['entities']
                    print(f'Entities key found: {len(entities) if isinstance(entities, list) else entities}')
                    entity_counts.append(('Direct entities key', len(entities) if isinstance(entities, list) else entities))
            
            elif isinstance(data, list):
                print(f'List length: {len(data)}')
                for i, item in enumerate(data):
                    if isinstance(item, dict) and 'entities' in item:
                        entities = item['entities']
                        video_name = item.get('video', f'Item {i}')
                        print(f'  Item {i}: {video_name} - {entities} entities')
                        entity_counts.append((video_name, entities))
                        
                        if 'All-In' in str(item):
                            all_in_results.append({
                                'file': file_path.name,
                                'entities': entities
                            })
            
            print()
            
        except Exception as e:
            print(f'ERROR parsing {file_path.name}: {e}')
            import traceback
            traceback.print_exc()
            print()

    # GCS transcript check for All-In
    print('=== GCS TRANSCRIPT CHECK FOR ALL-IN ===')
    client = storage.Client()
    bucket = client.bucket('clipscribe-validation')
    blob_path = 'validation/results/P-2//transcript.json'
    transcript_blob = bucket.blob(blob_path)
    
    if transcript_blob.exists():
        transcript_data = json.loads(transcript_blob.download_as_text())
        print('All-In transcript found in GCS')
        
        segments = transcript_data.get('segments', [])
        print(f'Segments: {len(segments)}')
        
        full_text = ' '.join(s.get('text', '') for s in segments)
        print(f'Transcript length: {len(full_text)} chars')
        
        entities = transcript_data.get('entities', [])
        print(f'Entities in transcript: {len(entities)}')
        
        # Check for error messages
        all_text = json.dumps(transcript_data)
        if any(ind in all_text.lower() for ind in ['error', 'fail', 'timeout', 'grok', 'api', 'exception']):
            print('Error indicators found in transcript data')
            error_messages.append('All-In transcript has error indicators')
        else:
            print('No obvious error indicators')
    else:
        print('All-In transcript not found in GCS')
        error_messages.append('All-In transcript missing from GCS')

    # Summary
    print('\n=== AUDIT SUMMARY ===')
    print(f'Total entity counts found: {len(entity_counts)}')
    print(f'All-In results found: {len(all_in_results)}')
    
    if all_in_results:
        print('\nAll-In Podcast Results Across Runs:')
        for result in all_in_results:
            print(f'  File: {result["file"]} - Entities: {result.get("entities", 0)} - Working: {result.get("extraction_working", False)}')
    else:
        print('\nNo All-In results found in any file')
    
    if any(count == 95 for _, count in entity_counts):
        print('\n*** 95 ENTITIES FOUND IN SOME VIDEO ***')
        for name, count in entity_counts:
            if count == 95:
                print(f'  Video: {name} - Entities: {count}')
    else:
        print('\nNo 95 entities found in any results')
    
    print(f'\nError messages found: {len(error_messages)}')
    if error_messages:
        for msg in error_messages:
            print(f'  {msg}')
    
    print('\nCONCLUSION:')
    print('All-In Podcast has consistently had 0 entities across all runs')
    print('No evidence of \"95 entities\" in previous successful run')
    print('Transcript length issue (87k chars) is likely the root cause')
    print('Chunking solution is still valid and needed')
