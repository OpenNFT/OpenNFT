import re
from pathlib import Path

# Define parameters
watch_folder = 'C:\\rtExport\\s11100000'
target_file_pattern = 'i.*.MRDC.(.*)'  # Pattern to capture index only

# Initialize parameters
NrOfSlices = 48  # Number of slices per volume
NrOfVolumes = 203  # Total number of volumes expected
total_files_expected = NrOfVolumes * NrOfSlices  # Total files expected
watch_path = Path(watch_folder)

# 1. Compile the regex pattern
file_pattern = re.compile(target_file_pattern)

# 2. Find all files that match the pattern using glob for initial filtering
matching_files = []
for file_path in watch_path.glob('i*.MRDC.*'):  # Efficient initial filter
    match = file_pattern.match(file_path.name)
    if match:
        file_index = match.group(1)  # Extract only the index part
        matching_files.append((file_path, file_index))

print(f"Found {len(matching_files)} files in {watch_folder}")
print(f"Expected {total_files_expected} files ({NrOfVolumes} volumes × {NrOfSlices} slices per volume)")

# 3. Sort files by their index (convert to int for numerical sorting)
try:
    sorted_files = sorted(matching_files, key=lambda x: int(x[1]))
except ValueError:
    print("Error: Non-numeric indices found")
    sorted_files = []

file_paths_only = [file[0] for file in sorted_files]  # Extract just the Path objects

# 4. Process files for each iteration (1 to NrOfVolumes)
print(f"\nProcessing files for each iteration (1 to {NrOfVolumes}):")
for iteration in range(1, NrOfVolumes + 1):
    # Calculate the file range for this iteration: (iteration-1)*NrOfSlices to iteration*NrOfSlices
    start_idx = (iteration - 1) * NrOfSlices
    end_idx = iteration * NrOfSlices
    iteration_files = file_paths_only[start_idx:end_idx]  # Get files for this iteration

    print(
        f"Iteration {iteration}: files {start_idx + 1} to {min(end_idx, len(file_paths_only))} ({len(iteration_files)} slices)")

    # Process each file in the current iteration
    for f in iteration_files:
        # Your processing code here
        print(f"  Processing: {f.name}")
        # Example: copy files, analyze content, etc.

# 5. Verification against expected total
if len(matching_files) == total_files_expected:
    print(f"\n✓ SUCCESS: Found all {total_files_expected} expected files ({NrOfVolumes} complete volumes)")
elif len(matching_files) > total_files_expected:
    print(
        f"\n⚠ WARNING: Found {len(matching_files)} files, expected {total_files_expected} ({NrOfVolumes} volumes) - extra files present")
else:
    print(f"\n✗ ERROR: Found only {len(matching_files)} files, expected {total_files_expected} ({NrOfVolumes} volumes)")

# 6. Show volume completeness
if sorted_files:
    volumes_found = len(file_paths_only) // NrOfSlices
    incomplete_volume_slices = len(file_paths_only) % NrOfSlices
    print(f"Volume completeness: {volumes_found} full volumes + {incomplete_volume_slices} slices in partial volume")

# 7. Show index range found
if sorted_files:
    min_index = sorted_files[0][1]
    max_index = sorted_files[-1][1]
    print(f"Index range found: {min_index} to {max_index}")