import subprocess

def test_raw_extraction(file_path):
    print(f"Testing RAW extraction from: {file_path}")
    
    cmd = [
        'ffmpeg',
        '-i', file_path,
        '-map', '0:1',
        '-codec', 'copy',
        '-f', 'data',
        '-'
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    # Read first 100 bytes
    raw_data = process.stdout.read(100)
    print(f"Read {len(raw_data)} bytes.")
    print(f"Hex: {raw_data.hex()}")
    
    if len(raw_data) > 0:
        print("SUCCESS: Data stream is accessible.")
    else:
        print("FAILURE: No data read.")

if __name__ == "__main__":
    test_raw_extraction("test_videos/geoint/Day Flight.mpg")

