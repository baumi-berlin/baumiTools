def UnTarGZ(infile, outpath):
    import tarfile
    # Function to untar archives into a pre-created root-folder
    tar = tarfile.open(infile, "r")
    list = tar.getnames()
    for file in tar:
        tar.extract(file, outpath)
    tar.close()
    file = None