import os
import re
import argparse

parser = argparse.ArgumentParser(description="Clean JSON Slack export lines for LLM ingestion.")
parser.add_argument('--input_dir', default='./path/to/json/files', help='Directory containing the JSON files')
parser.add_argument('--output_file', default='cleaned_consolidated_output.txt', help='Output file name')
parser.add_argument('--org_prefix', default='orgname/', help='Organization prefix to remove (e.g., "orgname/"). Set empty if none.')
parser.add_argument('--org_fallback_pattern', default=r'\[orgname\/[^]]+\] ', help='Regex pattern to remove org-specific fallback info. Set empty if none.')
args = parser.parse_args()

input_dir = args.input_dir
output_file = args.output_file
org_prefix = args.org_prefix
org_fallback_pattern = args.org_fallback_pattern

# Define the keywords to search for in lines
keywords = ['"fallback":', '"text":', '"title":', '"pretext":']

# Define the patterns to exclude
exclude_patterns = ['dependabot[bot]', 'Bump']

def clean_line(line):
    """Clean individual line based on specific rules."""
    # Remove escape characters and quotation marks
    line = line.replace('\\/', '/').replace('"', '')

    # Simplify URLs by removing the "https://github.com" part
    # Modify the substitution to handle 'issues' differently
    def replace_github_url(match):
        url_part = match.group(1)
        display_part = match.group(2)
        if 'issues' in url_part:
            # For issue URLs, keep both parts
            # Remove issue number from url_part
            url_part = re.sub(r'(/issues)/\d+', r'\1', url_part)
            return url_part + '|' + display_part
        else:
            # For other URLs, keep only the URL part before the '|'
            return url_part

    line = re.sub(r'<https:\/\/github\.com\/([^|>]+)\|([^>]+)>', replace_github_url, line)
    line = re.sub(r'https:\/\/github\.com\/', '', line)

    # Remove backticks around GitHub links
    line = re.sub(r'`([^`]+)`', r'\1', line)

    # Remove asterisks
    line = line.replace('*', '')

    # Remove the word "commit" and commit IDs
    line = re.sub(r'commit\/[a-f0-9]{40}\|', '', line)
    line = re.sub(r'[a-f0-9]{7,40}', '', line)
    # Remove trailing "/commit/"
    line = re.sub(r'/commit/', '', line)

    # Remove org-specific fallback line if pattern is provided and not empty
    if org_fallback_pattern.strip():
        line = re.sub(org_fallback_pattern, '', line)

    # Remove org prefix from repository paths if provided and not empty
    if org_prefix.strip():
        line = re.sub(r'\b' + re.escape(org_prefix), '', line)

    # Remove "/compare/..." from "pretext" lines
    line = re.sub(r'/compare/\.\.\.', '', line)

    # Remove the labels "fallback:", "text:", "title:", and "pretext:"
    line = re.sub(r'^\s*(fallback:|text:|title:|pretext:)\s*', '', line)

    # Remove unnecessary labels like 'branch', 'pushed to'
    line = re.sub(r'\bbranch\b', '', line)
    line = re.sub(r'\bpushed to\b', '', line)

    # Remove commit counts and underscores
    # Example: "1 new commit  _f/<branch>_ by <Name>" → "f/<branch> by <Name>"
    line = re.sub(r'^\s*\d+ new commit[s]?\s+_(.*?)_\s+by\s+(\w+)', r'\1 by \2', line)

    # Replace "Pull request opened by " and "Pull request merged by " with "PR by "
    line = re.sub(r'Pull request (opened|merged) by\s+', 'PR by ', line)

    # Remove specific substrings but keep the rest
    line = re.sub(r'\*What type of PR is this\? \(check all applicable\)\*', '', line)

    # Replace newline characters with spaces to consolidate multi-line entries
    line = line.replace('\\n', ' ').replace('\n', ' ')

    # Remove angle brackets
    line = re.sub(r'[<>]', '', line)

    # Remove multiple spaces
    line = re.sub(r'\s+', ' ', line)

    # Remove extra whitespace and trailing commas
    line = line.rstrip(',').strip()

    # Remove lines that have unnecessary content
    line = re.sub(r'^\s*(Comment|Comments|Edit|Reopen|Close|Labels|Assignees|Reviewers)\s*$', '', line)

    return line if line else None

def extract_relevant_lines(filename, content):
    extracted_lines = []
    previous_line = None  # Initialize previous_line to track duplicates
    for line in content.splitlines():
        # Check if the line contains any of the keywords and not any exclude patterns
        if any(keyword in line for keyword in keywords) and not any(pattern in line for pattern in exclude_patterns):
            # Special handling for "text": lines to remove GitHub link up to the hyphen
            if line.strip().startswith('"text":'):
                parts = line.split('`')
                if len(parts) > 1:
                    github_link = parts[1]
                    hyphen_index = github_link.find('-')
                    if hyphen_index != -1:
                        # Remove up to the hyphen
                        parts[1] = github_link[hyphen_index+1:]
                        line = '`'.join(parts)
            # Apply cleaning
            cleaned_line = clean_line(line)
            # Skip lines that are now empty after cleaning
            if cleaned_line:
                # Check for duplicates
                if cleaned_line != previous_line:
                    extracted_lines.append(cleaned_line)
                    previous_line = cleaned_line  # Update previous_line
    return extracted_lines

# Open the output file in write mode with UTF-8 encoding
with open(output_file, 'w', encoding='utf-8') as outfile:
    # Iterate over all JSON files in the directory
    for json_file in os.listdir(input_dir):
        if json_file.endswith('.json'):
            file_path = os.path.join(input_dir, json_file)
            with open(file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
                # Write the filename (without extension) to the output file
                outfile.write(f'{os.path.splitext(json_file)[0]}\n')
                # Extract relevant lines from the JSON content
                relevant_lines = extract_relevant_lines(json_file, content)
                # Write the extracted lines to the output file
                for line in relevant_lines:
                    outfile.write(f'{line}\n')
                # Add a newline to separate content from different files if there were relevant lines
                if relevant_lines:
                    outfile.write('\n')

print(f'Extraction and cleaning complete. Cleaned consolidated output saved to {output_file}')
