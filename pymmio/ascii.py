
import csv, re

def readLines(filepath):
    lout = list()
    with open(filepath) as f:
        for ln in f.read().splitlines():
            if len(ln) == 0: continue
            lout.append(ln.strip())
    return(lout)

def readInts(filepath):
    lout = list()
    for ln in readLines(filepath):
        lout.append(int(ln))
    return(lout)        

def readFloats(fp):
    with open(fp) as f:
        return [float(x) for x in f]

def readIntFloats(fp, delim='\t'):
    with open(fp) as f:
        lines = (line.split(delim) for line in f)
        return dict((int(k), float(v)) for k, v in lines)        

def readCSV(filepath):
    with open(filepath) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        lout = list()
        for row in csv_reader:
            if line_count == 0:
                # print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                lout.append(row)
                # print(f'\t{row[0]} works in the {row[1]} department, and was born in {row[2]}.')
                line_count += 1
        # print(f'Processed {line_count} lines.')
        return(lout)

def writeLines(fp,lns):
    with open(fp, 'w') as f:
        for ln in lns:
            f.write('{}\n'.format(ln))

def splitSpaceTabLine(line):
    a = re.split('\s', line)
    return [s for s in a if len(s) > 0]