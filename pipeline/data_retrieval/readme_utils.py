import re

# Function to remove HTML tags from text
def remove_html_tags(text):
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text

# Function to remove Markdown tags from text
def remove_markdown_tags(text):
    # Remove newlines inside brackets
    text = re.sub(r'\[([^\]]+)\]', lambda m: m.group(0).replace('\n', ''), text)
    # Remove code blocks (```code```)
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    # Remove headers
    text = re.sub(r'#+\s*', '', text)
    # Remove links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    # Remove bold **text** or __text__
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    # Remove italics *text* or _text_
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # Remove reference-style links ![alt][id]
    text = re.sub(r'!\[([^\]]+)\]\[[^\]]+\]', '', text)
    # Remove reference-style links [text][id]
    text = re.sub(r'\[([^\]]+)\]\[[^\]]+\]', r'\1', text)
    # Remove empty image tags ![]()
    text = re.sub(r'!\[\]\([^\)]+\)', '', text)
    # Remove inline images with links [![alt](url)][id]
    text = re.sub(r'\[\!\[([^\]]*)\]\([^\)]+\)\]\[[^\]]+\]', '', text)
    # Remove bullet or numbered lists
    #text = re.sub(r'^\s*[\*\-+]\s*', '', text, flags=re.MULTILINE)
    #text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
    return text

# Function to remove special characters
def remove_special_car(text):
    # Remove tabs
    text = re.sub(r'    ', ' ', text)
    # Remove 2+ successive newlines
    text = re.sub(r'\n{2,}', '\n', text)
    # Remove leading spaces
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    # Remove special characters
    text = re.sub(r'[^\w\s]', '', text)
    return text

# Function to remove all tags (HTML, Markdown, special characters)
def remove_all_tags(text):
    text = remove_html_tags(text)
    text = remove_markdown_tags(text)
    text = remove_special_car(text)
    return text