
def UnzipToFolder(inZip):
    import zipfile, os
    # Create folder with exactly the same name as the zip-file
    outPath = inZip
    outPath = outPath.replace(".zip", "/")
    os.makedirs(outPath)
    # Now extract the zipFile
    zip_ref = zipfile.ZipFile(inZip, 'r')
    zip_ref.extractall(outPath)
    zip_ref.close()
    return outPath