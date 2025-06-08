import os
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_photo(file, user_id):
    """
    Saves profile photo and returns the relative path for database storage
    """
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(f"user_{user_id}_{file.filename}")
        # Use the UPLOAD_FOLDER from app config
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Create profile_photos subdirectory if it doesn't exist
        profile_photos_dir = os.path.join(upload_folder, 'profile_photos')
        os.makedirs(profile_photos_dir, exist_ok=True)
        
        # Save file path will be static/uploads/profile_photos/filename
        file_path = os.path.join(profile_photos_dir, filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return f"uploads/profile_photos/{filename}"
    
    return None