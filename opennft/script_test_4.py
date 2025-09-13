import re
from pathlib import Path
import time

# Define parameters
watch_folder = 'C:\\rtExport\\s11100000'
target_file_pattern = 'i.*.MRDC.(.*)'  # Pattern to capture index only

# Initialize parameters
NrOfSlices = 48  # Number of slices per volume
NrOfVolumes = 5  # Total number of volumes expected
watch_path = Path(watch_folder)

# 1. Compile the regex pattern
file_pattern = re.compile(target_file_pattern)


def getFileSearchStringGE(file_path):
    """Generate a search string pattern from a file path"""
    if file_path.exists():
        # Get the filename parts to create search pattern
        fname = file_path.stem.split('.')[0]  # Gets the 'i12991151' part
        extensions = file_path.suffixes

        # Create the search string pattern
        search_string = '%s%s%s' % (fname, extensions[0], extensions[1])
    else:
        search_string = ""
    return search_string


def check_files_for_iteration(iteration, max_wait_time=30):
    """Check for all files in the iteration range, continue searching after timeout"""
    max_wait_seconds = max_wait_time / 1000  # Convert ms to seconds (30ms = 0.03s)

    start_index = (iteration - 1) * NrOfSlices + 1
    end_index = iteration * NrOfSlices
    expected_indices = set(range(start_index, end_index + 1))

    print(f"Expected file indices: {start_index} to {end_index}")

    found_files = {}
    start_time = time.time()
    timeout_reached = False
    missing_indices = set(expected_indices)  # Initialize with all expected indices

    while True:  # Continue searching indefinitely
        current_time = time.time()

        # Check if timeout period has elapsed (for initial intensive search)
        if not timeout_reached and (current_time - start_time) >= max_wait_seconds:
            print("⚠ Initial search timeout reached, but continuing to look for missing files...")
            timeout_reached = True

        # Scan directory for files in the target range
        for file_path in watch_path.glob('i*.MRDC.*'):
            match = file_pattern.match(file_path.name)
            if match:
                try:
                    file_index = int(match.group(1))
                    if start_index <= file_index <= end_index and file_index not in found_files:
                        found_files[file_index] = file_path
                        missing_indices.discard(file_index)  # Remove found index from missing
                        #print(f"✓ Found index {file_index}: {file_path.name}")
                except ValueError:
                    continue

        # Check if all expected files are found
        if not missing_indices:
            #print(f"✓ All {NrOfSlices} files found for iteration {iteration}")
            break

        # If timeout reached, sleep longer to reduce CPU usage
        if timeout_reached:
            #print(f"  Still missing {len(missing_indices)} files: {sorted(missing_indices)[:5]}...")
            time.sleep(0.03)  # 30ms between scans after timeout
        else:
            # Intensive scanning during initial wait period
            time.sleep(0.001)  # 1ms between scans

    return found_files, missing_indices  # Return the final missing_indices


# Process each iteration separately (from 1 to NrOfVolumes INCLUSIVE)
for iteration in range(1, NrOfVolumes + 1):

    # Check for files in this iteration's range
    found_files, missing_indices = check_files_for_iteration(iteration, max_wait_time=30)

    # Provide the path of the iteration*NrOfSlices file as output
    last_file_index = iteration * NrOfSlices
    last_file_path = found_files.get(last_file_index)

    # Call the separate function to generate search string
    search_string = getFileSearchStringGE(last_file_path)

    print(f"✓ Search pattern for similar files: {search_string}")

    print(f"{'=' * 50}")


