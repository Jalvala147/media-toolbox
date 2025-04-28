# core/zip_files.py

import io
import zipfile, os

def rename_and_zip(files_data, new_name, extension_filter=None):
    zip_buffer = io.BytesIO()
    counter = 1

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_data in files_data:
            file_name = file_data["name"]
            file_bytes = file_data["content"]
            _, file_extension = os.path.splitext(file_name)

            if extension_filter and file_extension.lower() != extension_filter.lower():
                continue

            new_file_name = f"{new_name}_{counter:03}{file_extension}"
            zip_file.writestr(new_file_name, file_bytes)
            counter += 1

    zip_buffer.seek(0)
    return zip_buffer
