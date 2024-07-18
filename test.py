def check_valid_file(filename):
    if not '.' in filename:
        return False
    else:
        fileename_ext = filename.split('.')[1]
        return fileename_ext


check_valid_file('tsf.exe')