#!/bin/bash

# ==========================
# super_concat.sh
# ==========================
# This script concatenates files from multiple directories into a single output file.
# Each directory's contents are preceded by a banner with a fixed title.
# Supports whitelisting and blacklisting of file extensions.
# Includes a recursive option to process subdirectories.
#
# Usage:
#   ./super_concat.sh [-r]
#     -r: Enable recursive processing of subdirectories.
#
# Configuration:
#   - Define the directories and their associated titles in the CONFIGURATION SECTION below.
#   - Specify desired file extensions in WHITELIST_EXTS and BLACKLIST_EXTS arrays.

# ==========================
# Configuration Section
# ==========================

# Array of source directories to concatenate
# Each entry should be the path to the 'src' directory you want to process
# Example: "./path1/src" "./path2/src"
SRC_DIRS=(
    "./"
    # "/home/vega/Coding/Work/ohub/ohub-be"

    # Add more directories as needed, e.g., "./path2/src"
)

# Array of titles corresponding to each source directory
# Ensure that each title matches the directory at the same index in SRC_DIRS
TITLES=(
    "////// CHAT SERVER"
    # "////// OLD-OHUB-BE OLD SCRAPING CODE TO BE MIGRATED TO SCHEDULED DATA FETCHER AREA OF NEW SERVER"
    # Add more titles as needed, e.g., "////// CLIENT"
)

# Whitelist of file extensions (without the dot)
# Only files with these extensions will be included
# Example: "py" "txt"
WHITELIST_EXTS=(
    "py"
    # Add more extensions as needed
)

# Blacklist of file extensions (without the dot)
# Files with these extensions will be excluded, even if they are in the whitelist
# Example: "test" "ignore"
BLACKLIST_EXTS=(
    # "ignore_extension"
    # Add more extensions as needed
)

# Hardcoded path to the output file where the concatenated content will be saved
OUTPUT_FILE="./concat.py"

# ==========================
# Function Definitions
# ==========================

# Function to display usage information
usage() {
    echo "Usage: $0 [-r]"
    echo "  -r    Enable recursive processing of subdirectories."
    exit 1
}

# Function to check if an element is in an array
# Arguments:
#   $1: Element to search for
#   $2: Array name
# Returns:
#   0 (true) if found, 1 (false) otherwise
is_in_array() {
    local element="$1"
    shift
    local array=("$@")
    for e in "${array[@]}"; do
        if [[ "$e" == "$element" ]]; then
            return 0
        fi
    done
    return 1
}

# ==========================
# Argument Parsing
# ==========================

# Default: non-recursive
RECURSIVE=false

# Parse command-line options
while getopts ":r" opt; do
    case ${opt} in
        r )
            RECURSIVE=true
            ;;
        \? )
            echo "Invalid Option: -$OPTARG" 1>&2
            usage
            ;;
    esac
done
shift $((OPTIND -1))

# ==========================
# Validate Configuration
# ==========================

# Check that the number of directories matches the number of titles
if [ "${#SRC_DIRS[@]}" -ne "${#TITLES[@]}" ]; then
    echo "Error: The number of source directories and titles do not match."
    exit 1
fi

# ==========================
# Script Execution
# ==========================

# # Backup existing output file if it exists
# if [ -f "$OUTPUT_FILE" ]; then
#     cp "$OUTPUT_FILE" "${OUTPUT_FILE}.bak"
#     echo "Existing '$OUTPUT_FILE' backed up as '${OUTPUT_FILE}.bak'."
# fi

# Empty the output file or create it
> "$OUTPUT_FILE"

# Iterate over the directories and their corresponding titles
for index in "${!SRC_DIRS[@]}"; do
    DIR="${SRC_DIRS[$index]}"
    TITLE="${TITLES[$index]}"

    # Check if the source directory exists and is a directory
    if [ ! -d "$DIR" ]; then
        echo "Warning: Source directory '$DIR' does not exist or is not a directory. Skipping."
        continue
    fi

    # Add the banner for the current directory
    echo "$TITLE" >> "$OUTPUT_FILE"
    echo "========================================" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # Determine the find command based on recursion
    if [ "$RECURSIVE" = true ]; then
        # Find all regular files recursively
        FILES=$(find "$DIR" -type f)
    else
        # Find all regular files in the top-level directory
        FILES=$(find "$DIR" -maxdepth 1 -type f)
    fi

    # Iterate over each file
    while IFS= read -r file; do
        # Check if it's a regular file (redundant due to find, but safe)
        if [ -f "$file" ]; then
            FILENAME=$(basename "$file")
            # Extract the file extension
            EXTENSION="${FILENAME##*.}"

            # Check against blacklist first
            if is_in_array "$EXTENSION" "${BLACKLIST_EXTS[@]}"; then
                echo "Skipping '$file' due to blacklist."
                continue
            fi

            # If whitelist is not empty, check if the extension is whitelisted
            if [ "${#WHITELIST_EXTS[@]}" -gt 0 ]; then
                if ! is_in_array "$EXTENSION" "${WHITELIST_EXTS[@]}"; then
                    echo "Skipping '$file' as it is not in the whitelist."
                    continue
                fi
            fi

            # Determine the relative path for headers if recursive
            if [ "$RECURSIVE" = true ]; then
                REL_PATH="${file#$DIR/}"  # Remove the base directory path
                HEADER="///////////////////////////// $REL_PATH"
            else
                HEADER="///////////////////////////// $FILENAME"
            fi

            # Add the separator line with the filename or relative path
            echo "$HEADER" >> "$OUTPUT_FILE"

            # Concatenate the file's content
            cat "$file" >> "$OUTPUT_FILE"

            # Add a newline for readability
            echo -e "\n" >> "$OUTPUT_FILE"
        fi
    done <<< "$FILES"

    # Add a newline to separate different directory sections
    echo "" >> "$OUTPUT_FILE"
done

echo "All specified directories have been concatenated into '$OUTPUT_FILE'."
