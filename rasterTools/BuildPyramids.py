import os

def BuildPyramids(path, levels=None):
    # levels is a vector that is multiples of 2 --> e.g., 2, 4, 6, 8, ..., 64
    if levels == None:
        command = "gdaladdo.exe -r nearest -ro " + path + " 2 4 8 16 32"
        os.system(command)
    else:
        command = "gdaladdo.exe -r nearest -ro " + path + " "
        for l in levels:
            command = command + l + " "
        os.system(command)