import os

def get_template_name(template_path, namespace=None):
    # Check if the extension is missing and add it if necessary
    if not template_path.endswith('.html'):
        template_path += '.html'
        
    if namespace:
        return os.path.join(namespace, template_path)
    else:
        return template_path