import streamlit as st
import tempfile
import os
from google.cloud import storage

@st.cache_data
def download_file_from_gcs(blob_name):
    """Download file from Google Cloud Storage to temporary location"""
    try:
        # Get the bucket (assuming bucket is accessible in scope)
        blob = bucket.blob(blob_name)
        
        # Check if blob exists
        if not blob.exists():
            st.error(f"File {blob_name} does not exist in GCS bucket")
            return None
        
        # Create temporary file with proper extension
        file_extension = os.path.splitext(blob_name)[1] or '.mat'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file.close()  # Close the file so it can be written to
        
        # Download to the temporary file
        blob.download_to_filename(temp_file.name)
        
        # Verify file was downloaded and has content
        if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
            st.success(f"Successfully downloaded {blob_name} ({os.path.getsize(temp_file.name)} bytes)")
            return temp_file.name
        else:
            st.error(f"Downloaded file {blob_name} is empty or doesn't exist")
            return None
            
    except Exception as e:
        st.error(f"Error downloading {blob_name}: {str(e)}")
        st.error(f"Error type: {type(e).__name__}")
        return None

# Alternative approach using direct blob download
def download_file_from_gcs_v2(blob_name, bucket):
    """Alternative download method with better error handling"""
    try:
        blob = bucket.blob(blob_name)
        
        # Check if blob exists
        if not blob.exists():
            st.error(f"Blob {blob_name} does not exist in bucket {bucket.name}")
            return None
        
        # Get blob info
        blob.reload()  # Refresh blob metadata
        st.info(f"Found blob: {blob_name}, Size: {blob.size} bytes")
        
        # Create temp directory and file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, os.path.basename(blob_name))
        
        # Download the blob
        with open(temp_file_path, 'wb') as f:
            blob.download_to_file(f)
        
        # Verify download
        if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
            st.success(f"Successfully downloaded to {temp_file_path}")
            return temp_file_path
        else:
            st.error("File download failed or file is empty")
            return None
            
    except Exception as e:
        st.error(f"Error in download_file_from_gcs_v2: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

# Updated main function section for tab2
def updated_tab2_section():
    """Updated version of your tab2 energy analysis section"""
    st.subheader("📊 Heat Consumption Analysis")
    
    # Debug: List available blobs
    with st.expander("🔍 Debug: Available files in simulation/"):
        mat_blobs_list = list(client.list_blobs(bucket, prefix="simulation/"))
        for blob in mat_blobs_list[:10]:  # Show first 10
            st.write(f"- {blob.name} ({blob.size} bytes)")
        if len(mat_blobs_list) > 10:
            st.write(f"... and {len(mat_blobs_list) - 10} more files")

    # Find the specific file for pre-renovation
    building_id = "0503100000019674"
    target_filename = f"{building_id}_result.mat"

    # Filter to find your specific file
    mat_blobs_list = list(client.list_blobs(bucket, prefix="simulation/"))
    matching_blobs = [blob for blob in mat_blobs_list if blob.name.endswith(target_filename)]

    if matching_blobs:
        file_blob = matching_blobs[0]
        st.success(f"✅ Found pre-renovation file: {file_blob.name}")
        
        # Try the improved download function
        pre_file_path = download_file_from_gcs_v2(file_blob.name, bucket)
        
        if pre_file_path and os.path.exists(pre_file_path):
            try:
                # Try to import buildingspy
                try:
                    from buildingspy.io.outputfile import Reader
                except ImportError:
                    st.error("buildingspy library not found. Install it with: pip install buildingspy")
                    return
                
                # Load .mat file
                st.info(f"Loading .mat file from: {pre_file_path}")
                r = Reader(pre_file_path, "dymola")
                
                # Get available variables first for debugging
                with st.expander("🔍 Debug: Available variables in .mat file"):
                    try:
                        # This might help debug what variables are available
                        st.write("File loaded successfully. Attempting to read heating power data...")
                    except Exception as e:
                        st.error(f"Error exploring variables: {e}")
                
                # Get heating power data
                time, heat_data = r.values('multizone.PHeater[1]')
                
                # Rest of your analysis code here...
                # [Continue with your existing plotting and analysis code]
                
            except Exception as e:
                st.error(f"Error processing energy data: {str(e)}")
                import traceback
                st.error(f"Full traceback: {traceback.format_exc()}")
            finally:
                # Clean up temporary file
                try:
                    if pre_file_path and os.path.exists(pre_file_path):
                        os.unlink(pre_file_path)
                        # Also try to remove the temporary directory
                        temp_dir = os.path.dirname(pre_file_path)
                        if temp_dir.startswith('/tmp'):
                            import shutil
                            shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as cleanup_error:
                    st.warning(f"Could not clean up temporary file: {cleanup_error}")
        else:
            st.error("❌ Failed to download pre-renovation file from GCS")
    else:
        st.warning(f"No energy data found for building {building_id}")
        available_files = [blob.name for blob in mat_blobs_list if blob.name.endswith('.mat')][:5]
        st.info(f"Available .mat files (first 5): {available_files}")