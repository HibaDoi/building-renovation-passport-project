import teaser
import os

# Check TEASER installation path
teaser_path = teaser.__file__
print(f"TEASER installed at: {os.path.dirname(teaser_path)}")

# Check if template files exist
template_path = os.path.join(os.path.dirname(teaser_path), "teaser_out", "Project")
print(f"Looking for templates at: {template_path}")
print(f"Template directory exists: {os.path.exists(template_path)}")

if os.path.exists(template_path):
    print("Files in template directory:")
    print(os.listdir(template_path))