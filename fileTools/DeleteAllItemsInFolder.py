
def DeleteAllItemsInFolder(path):
    import os, shutil
    # test if last item is "/", otherwise add it
    if not path.endswith("/"):
        path = path + "/"
    else:
        path = path
    # Now loop through items in folder, and delete them one by one
    itemList = os.listdir(path)
    for item in itemList:
        inname = path + item + "/"
        outname = path + "1/"
        os.rename(inname, outname)
        shutil.rmtree(outname)