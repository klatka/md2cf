import os
import sys
import yaml
from md2cf import Confluence
from atlassian import Confluence as AtlassianConfluence
import argparse

def upload_to_confluence(confluence, file_path, parent_id, suffix):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Extract YAML front matter
    yaml_end_index = content.find('---', 4)
    if yaml_end_index != -1:
        yaml_data = yaml.safe_load(content[4:yaml_end_index])
        if 'title' in yaml_data and 'labels' in yaml_data:
            title = yaml_data['title']
            labels = yaml_data['labels']

            # Generate new title with suffix
            new_title = f"{title} {suffix}"

            # Upload content to Confluence
            page_id = confluence.create_page(parent_id, new_title, content)

            print(f"Uploaded '{new_title}' to Confluence (Page ID: {page_id})")

            # Check if there's a directory matching the title
            dir_name = title.replace(' ', '_')  # Ensure a valid directory name
            if os.path.isdir(os.path.join(os.path.dirname(file_path), dir_name)):
                child_parent_id = page_id
                child_root_path = os.path.join(os.path.dirname(file_path), dir_name)
                md2cf_repo(child_root_path, child_parent_id, suffix)

def md2cf_repo(root_path, parent_id, suffix):
    confluence = Confluence()  # Initialize md2cf Confluence API connection
    atl_confluence = AtlassianConfluence(url='https://your-confluence-url.com', username='your-username', password='your-password')

    # Retrieve all child pages under the specified parent_id
    child_pages = atl_confluence.get_all_pages_from_space(parent_id)

    for root, _, files in os.walk(root_path):
        for file_name in files:
            if file_name.endswith('.md'):
                file_path = os.path.join(root, file_name)
                upload_to_confluence(confluence, file_path, parent_id, suffix)

    # Filter pages created by this script based on labels
    script_created_pages = [page for page in child_pages if 'gitlab-sync' in page['labels']]

    # Identify pages created by this script
    script_created_titles = set(page['title'] for page in script_created_pages)
    expected_titles = set()

    for root, _, files in os.walk(root_path):
        for file_name in files:
            if file_name.endswith('.md'):
                with open(os.path.join(root, file_name), 'r', encoding='utf-8') as file:
                    content = file.read()
                    yaml_end_index = content.find('---', 4)
                    if yaml_end_index != -1:
                        yaml_data = yaml.safe_load(content[4:yaml_end_index])
                        if 'title' in yaml_data:
                            expected_titles.add(f"{yaml_data['title']} {suffix}")

    # Find differences
    extra_pages = script_created_titles - expected_titles
    missing_pages = expected_titles - script_created_titles

    if extra_pages:
        print("Extra pages created by script:")
        print("\n".join(extra_pages))

    if missing_pages:
        print("Pages expected but not created by script:")
        print("\n".join(missing_pages))

def parse_arguments():
    parser = argparse.ArgumentParser(description="Upload Markdown files to Confluence and compare created pages")

    parser.add_argument("working_directory", type=str, help="Path to the working directory containing Markdown files")
    parser.add_argument("root_parent_id", type=str, help="Root parent page ID in Confluence")
    parser.add_argument("suffix", type=str, help="Suffix to append to the Confluence page titles")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    working_directory = args.working_directory
    root_parent_id = args.root_parent_id
    suffix = args.suffix

    md2cf_repo(working_directory, root_parent_id, suffix)
