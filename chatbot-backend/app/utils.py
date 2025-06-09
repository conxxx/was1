import re

def remove_markdown(text):
    """
    Removes Markdown formatting from a given text string.
    """
    # Remove headers
    text = re.sub(r'#+\s', '', text)
    # Remove bold and italics
    text = re.sub(r'(\*\*|__)(.*?)(\*\*|__)', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)(\*|_)', r'\2', text)
    # Remove strikethrough
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    # Remove inline code
    text = re.sub(r'`(.*?)`', r'\1', text)
    # Remove links
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
    # Remove blockquotes
    text = re.sub(r'^\>+\s', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'---', '', text)
    text = re.sub(r'\*\*\*', '', text)
    # Remove lists
    text = re.sub(r'^\s*[\*\-\+]\s', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s', '', text, flags=re.MULTILINE)
    return text
