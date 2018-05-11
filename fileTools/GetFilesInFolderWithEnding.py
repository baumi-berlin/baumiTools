

def GetFilesInFolderWithEnding(folder, ext, fullPath):
    import os
    # Function that finds all files in a folder with the extension "ext". Returns a list of filepaths
    outlist = []
    input_list = os.listdir(folder)
    if fullPath == True:
        for file in input_list:
            if file.endswith(ext):
                if folder.endswith("/"):
                    filepath = folder + file
                else:
                    filepath = folder + "/" + file
                outlist.append(filepath)
    if fullPath == False:
        for file in input_list:
            if file.endswith(ext):
                outlist.append(file)
    if len(outlist) == 1:
        outlist = outlist[0]
    return outlist