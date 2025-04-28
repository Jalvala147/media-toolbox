# core/rename.py

import os

def rename_files(folder, new_name, extension_filter=None):
    files = os.listdir(folder)
    files.sort()  # Sort files to maintain order
    counter = 1
    renamed_files = 0

    for file in files:
        file_path = os.path.join(folder, file)

        if os.path.isfile(file_path):
            _, file_extension = os.path.splitext(file)

            if extension_filter and file_extension.lower() != extension_filter.lower():
                continue

            new_file_name = f"{new_name}_{counter:03}{file_extension}"
            new_file_path = os.path.join(folder, new_file_name)

            os.rename(file_path, new_file_path)
            counter += 1
            renamed_files += 1

    return renamed_files
