
import os
import struct
from pymmio import files
from pyGrid.definition import gdef



class hdem:
    gd = gdef

    def __init__(self, filepath):        
        gdfp = filepath+".gdef" # files.removeExt(filepath)+".gdef"
        if not os.path.exists(gdfp):
            print('error no grid definition file available: ',gdfp,'\n')
            quit()
        if files.getExtension(filepath)!=".uhdem": 
            print("error: only .uhdem's supported ',filepath,'\n")
            quit()
            
        print("error: uhdem load to complete\n")
        quit()


        self.gd = gdef(gdfp)
        print(' loading', filepath)
        self.loadUHDEM(filepath)       

    def loadUHDEM(self,fp):
        # try:
        #     with open(fp, 'rb') as f:
        #         self.xul=float(f.readline()) # UL corner
        #         self.yul=float(f.readline()) # UL corner


        # except FileNotFoundError:
        #     print(' hdem file:',fp,'not found.')
        #     quit()
        # except Exception as err:
        #     print('error reading hdem file:',fp,'\n',err)
        #     quit()

        with open(fp, 'rb') as f:
            # read DEM data
            nl = struct.unpack('<b', f.read(1))[0]
            hd = struct.unpack('<{}c'.format(nl), f.read(nl)) # 'unstructured'
            # print(str(b''.join(hd)))
            nc = struct.unpack('<i', f.read(4))[0]


            # t.TEC = make(map[int]TEC, nc)
            # coord := make(map[int]mmaths.Point, nc)
            # uc := make([]uhdemReader, nc)
            # if err := binary.Read(buf, binary.LittleEndian, uc); err != nil {
            # 	return nil, fmt.Errorf("Fatal error: loadUHDEM uhdem read failed: %v", err)
            # }
            # for _, u := range uc {
            # 	ii := int(u.I)
            # 	coord[ii], t.TEC[ii] = u.toTEC()
            # }


	# buf := mmio.OpenBinary(fp)

	# // check file type
	# switch mmio.ReadString(buf) {
	# case "unstructured":
	# 	// do nothing
	# default:
	# 	return nil, fmt.Errorf("Fatal error: unsupported UHDEM filetype")
	# }

	# // read dem data
	# var nc int32
	# if err := binary.Read(buf, binary.LittleEndian, &nc); err != nil { // number of cells
	# 	return nil, fmt.Errorf("Fatal error: loadUHDEM uhdem read failed: %v", err)
	# }
	# t.TEC = make(map[int]TEC, nc)
	# coord := make(map[int]mmaths.Point, nc)
	# uc := make([]uhdemReader, nc)
	# if err := binary.Read(buf, binary.LittleEndian, uc); err != nil {
	# 	return nil, fmt.Errorf("Fatal error: loadUHDEM uhdem read failed: %v", err)
	# }
	# for _, u := range uc {
	# 	ii := int(u.I)
	# 	coord[ii], t.TEC[ii] = u.toTEC()
	# }

	# // read flowpaths
	# var nfp int32
	# if err := binary.Read(buf, binary.LittleEndian, &nfp); err != nil { // number of flowpaths
	# 	return nil, fmt.Errorf("Fatal error: loadUHDEM flowpath read failed: %v", err)
	# }
	# fc := make([]fpReader, nfp)
	# if err := binary.Read(buf, binary.LittleEndian, fc); err != nil {
	# 	return nil, fmt.Errorf("Fatal error: loadUHDEM flowpath read failed: %v", err)
	# }
	# for _, f := range fc {
	# 	ii := int(f.I)
	# 	var x = t.TEC[ii]
	# 	x.Ds = int(f.Ids)
	# 	t.TEC[ii] = x
	# }

	# if mmio.ReachedEOF(buf) {
	# 	return coord, nil
	# }
	# return nil, fmt.Errorf("Fatal error: UHDEM file contains extra data")