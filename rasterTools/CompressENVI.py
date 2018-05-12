import gzip, os

def CompressENVI(ENVIfilePath):

# do gzip compression on ENVI-file
# add in the last line of hdr file the line "file compression = 1"
    tmp_path = ENVIfilePath
    tmp_path = tmp_path.replace(".bsq", "_tmp.bsq")
    f_in = open(ENVIfilePath, 'rb')
    f_out = gzip.open(tmp_path, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    # Delete old file
    os.remove(ENVIfilePath)
    # Rename new file, delete tmpfile
    os.rename(tmp_path, ENVIfilePath)
    # Add compression-info to hdr-file
    hdrpath = ENVIfilePath
    hdrpath = hdrpath.replace(".bsq", ".hdr")
    with open(hdrpath, 'a') as file:
        file.write("file compression = 1")