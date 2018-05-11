
def TarGZ(in_folder, out_file, selectionList):
    import os, tarfile
    # Selection list is a list of strings that contain parts of
    fileList = os.listdir(in_folder)
    # Only compress files that match the selection-criteria
    tar = tarfile.open(out_file, "w:gz")
    for file in fileList:
        if any(sel in file for sel in selectionList):
            compr = in_folder + file
            tar.add(compr, arcname=file)
    tar.close()