# json_to_streamlit_secrets.py
# Run this script to convert your JSON file to Streamlit secrets format

import json

def convert_json_to_streamlit_secrets(json_file_path):
    """Convert GCS service account JSON to Streamlit secrets format"""
    
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        # Create Streamlit secrets format
        secrets_content = f"""[gcp_service_account]
type = "{data['type']}"
project_id = "{data['project_id']}"
private_key_id = "{data['private_key_id']}"
private_key = '''{data['private_key']}'''
client_email = "{data['client_email']}"
client_id = "{data['client_id']}"
auth_uri = "{data['auth_uri']}"
token_uri = "{data['token_uri']}"
auth_provider_x509_cert_url = "{data['auth_provider_x509_cert_url']}"
client_x509_cert_url = "{data['client_x509_cert_url']}"
"""
        
        # Save to file
        with open('streamlit_secrets.toml', 'w') as file:
            file.write(secrets_content)
        
        print("✅ Conversion complete!")
        print("📄 Streamlit secrets saved to: streamlit_secrets.toml")
        print("\n📋 Copy the contents of streamlit_secrets.toml to your Streamlit Cloud app secrets")
        print("\n" + "="*60)
        print("STREAMLIT SECRETS CONTENT:")
        print("="*60)
        print(secrets_content)
        
        return secrets_content
        
    except Exception as e:
        print(f"❌ Error converting file: {e}")
        return None

# Run the converter
if __name__ == "__main__":
    # Update this path to your actual JSON file
    json_file_path = r"C:/Users/hp/Downloads/renodat-a9e531a0f160.json"
    
    print("🔄 Converting JSON to Streamlit secrets format...")
    convert_json_to_streamlit_secrets(json_file_path)