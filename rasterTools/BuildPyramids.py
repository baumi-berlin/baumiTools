import os

def BuildPyramids(path, levels):
    # levels is a vector that is multiples of 2 --> e.g., 2, 4, 6, 8, ..., 64
    if levels == None:
        command = "gdaladdo.exe " + path + " 2 4 8 16 32 64"
        os.system(command)
    else:
        command = "gdaladdo.exe " + path + " "
        for l in levels:
            command = command + l + " "
        os.system(command)