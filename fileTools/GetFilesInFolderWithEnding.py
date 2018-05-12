import os

def GetFilesInFolderWithEnding(folder, ext, fullPath):
    '''
    Function that returns all filenames in a folder that match the extension

    Parameters
	----------
	folder : string (required)
		path, through which we are searching
	ext : string (required)
		extension of the files that we want to search for
	fullPath : bool (optional)
		option to return just the file names or the entire file path
		if True, then all matched files are concatenated with 'folder'

	Returns
	-------
	outlist : list of strings
        CAUTION: if len(outlist) == 1, then outlist is a variable, will be returned with a print-statement

    '''

    outlist = []
    input_list = os.listdir(folder)
    if fullPath == True:
        for file in input_list:
            if file.endswith(ext):
	# Check if the variable folder ends with a '/', otherwise manually add to get correct path
                if folder.endswith("/"):
                    filepath = folder + file
                else:
                    filepath = folder + "/" + file
                outlist.append(filepath)
    if fullPath == False or fullPath == None:
        for file in input_list:
            if file.endswith(ext):
                outlist.append(file)
    if len(outlist) == 1:
        print("Found only one file matching the extension. Returning a variable instead of a list")
        outlist = outlist[0]
    if len(outlist) == 0:
        print("Could not find any file matching the extension. Return-value is None")
    return outlist