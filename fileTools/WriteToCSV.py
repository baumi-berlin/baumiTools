import csv

def WriteListToCSV(outname, list, delim):
    '''
    Function to write a list of lists into a csv-file. Each entry in the list is thereby a new line
    --> the function is designed towards the standard output of may of my analyses.

    PARAMETERS
    ----------
    outname : string (required)
        Path to the output-file. make sure it ends with ".csv"

    list : list object (required)
        List with the data to write. Each sublist is an own line in the csv file. [[line 1], [line 2],...,[line n]]

    delim : string (required)
        Deliminter for the csv-File

    RETURNS
    -------
    theFile : output-file. Directly written to disc

    '''

    with open(outname, "w") as theFile:
        csv.register_dialect("custom", delimiter = delim, skipinitialspace = True, lineterminator = '\n')
        writer = csv.writer(theFile, dialect = "custom")
        for element in list:
            writer.writerow(element)