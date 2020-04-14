
import os, struct
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
import pyproj
from pyMet import wbcode
from tqdm import tqdm

def toPOSIX(t): # this function is needed to prevent "OSError: [Errno 22] Invalid argument" when using utcfromtimestamp in Windows 10
	return (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=t)).replace(tzinfo=None)

class Met:
	v = 1
	uc = 1
	tc = 1 # 1: unix/posix; 2: vb
	wbc = wbcode.WaterBalanceDataCode()
	prcn = 8
	intvl = 0
	dtb = datetime(1980, 10, 1)
	dte = datetime(2019, 9, 30)
	lc = 0
	espg = 26917
	nloc = 0
	# dfloc = pd.DataFrame()
	# dftem = pd.DataFrame()

	def __init__(self, fp=None, printout=True, skipdata=False):
		if fp is None: return
		# print(' loading', fp)
		with open(fp, "rb") as f:
			self.v = struct.unpack('<H', f.read(2))[0] # version
			self.uc = struct.unpack('<B', f.read(1))[0] # unit code:   0 unknown units; 1 standard units (m-s-kg)
			self.tc = struct.unpack('<B', f.read(1))[0] # time code:   1: unix/posix; 2: vb
			self.wbc = wbcode.WaterBalanceDataCode(struct.unpack('<Q', f.read(8))[0]) # waterbudget code
			self.prcn = struct.unpack('<B', f.read(1))[0] # precision
			self.intvl = struct.unpack('<Q', f.read(8))[0] # interval (seconds)
			if self.intvl > 0:
				idtb = struct.unpack('<q', f.read(8))[0] # start date
				idte = struct.unpack('<q', f.read(8))[0] # end date
				self.dtb = toPOSIX(idtb) # datetime.utcfromtimestamp(idtb)
				self.dte = toPOSIX(idte) # datetime.utcfromtimestamp(idte)
				rec = 46
			else:
				self.dtb = None
				self.dte = None
				rec = 30
			self.lc = struct.unpack('<b', f.read(1))[0] # location code (see wbalcodes.xslx)
			self.espg = struct.unpack('<I', f.read(4))[0] # projection info
			self.nloc = struct.unpack('<I', f.read(4))[0] # number of locations in following location table			

			# print info
			if printout: self.Info()

			# get locations
			if self.lc > 0: rec = self.getLocations(f,rec) 

			if skipdata: return
			if os.stat(fp).st_size > 10000000000:
				self.rec = rec
				self.dti = 0
				self.f = open(fp, "rb")
				self.f.read(rec)
			else:
				# get data
				nvar = len(self.wbc.dts)
				if self.intvl > 0:
					if nvar==0: print("nvar==0 supported") # todo
					print(self.dtb.strftime('%Y-%m-%d %H:%M:%S') + " to " + self.dte.strftime('%Y-%m-%d %H:%M:%S'), end=" >> ")				
					if self.lc==0: # gridded data
						if self.prcn == 4:
							a = np.frombuffer(f.read(os.path.getsize(fp)-rec), dtype=np.single)
						elif self.prcn == 8:
							a = np.frombuffer(f.read(os.path.getsize(fp)-rec))
						else:
							print("precicion not supported") # todo
						self.dftem = np.reshape(a, (-1,self.nloc,nvar))
					elif self.lc==1:
						if self.prcn == 2:
							fmt = 'e'*nvar
						elif self.prcn == 4: 
							fmt = 'f'*nvar
						elif self.prcn == 8: 
							fmt = 'd'*nvar	
						else:
							print("precicion not supported") # todo
						cols = self.wbc.dts
						dicC = {}
						pbar = tqdm(total=int((self.dte - self.dtb).days*86400/self.intvl)+1)
						if self.nloc==1:
							for dt in self.yielddates():
								pbar.update()
								pbar.set_description(dt.strftime(' %Y-%m-%d %H:%M:%S'))
								a = struct.unpack('<' + fmt, f.read(self.prcn*nvar))
								a = np.reshape(a, (-1,nvar))
								dicC[dt] = a[0]
							pbar.close()
							self.dftem = pd.DataFrame.from_dict(dicC, orient='index', columns=cols)
						else:
							for dt in self.yielddates():
								pbar.update()
								pbar.set_description(dt.strftime(' %Y-%m-%d %H:%M:%S'))
								a = struct.unpack('<' + fmt*self.nloc, f.read(self.prcn*nvar*self.nloc))
								a = np.reshape(a, (-1,nvar))
								p = pd.DataFrame(a, columns=cols)
								dicC[dt] = p
							pbar.close()
							self.dftem = dicC
					else:
						if self.prcn == 2:
							fmt = 'e'*nvar
						elif self.prcn == 4: 
							fmt = 'f'*nvar
						elif self.prcn == 8: 
							fmt = 'd'*nvar
						else:
							print("precicion not supported") # todo					
						cols = self.wbc.dts
						dicC = {}
						if self.nloc == 1:
							for dt in self.yielddates():
								a = struct.unpack('<' + fmt, f.read((self.prcn*nvar)))
								dicC[dt] = a
							# for dt in self.yielddates(): # lc<0
							# 	nloc = struct.unpack('<I', f.read(4))[0]						
							# 	a = struct.unpack('<' + fmt*nloc, f.read((4+8*nvar)*nloc))
							# 	a = np.reshape(a, (-1,nvar+1))
							# 	p = pd.DataFrame(a, columns=cols)
							# 	p.set_index('id', inplace=True)
							# 	dicC[dt] = p
							self.dftem = pd.DataFrame.from_dict(dicC, "index", columns=cols)
						elif self.nloc > 1:
							print()
							pbar = tqdm(total=int((self.dte - self.dtb).days*86400/self.intvl)+1)
							for dt in self.yielddates():
								pbar.update()
								pbar.set_description(dt.strftime(' %Y-%m-%d %H:%M:%S'))
								a = struct.unpack('<' + fmt*self.nloc, f.read((self.prcn*nvar*self.nloc)))
								a = np.reshape(a, (-1,nvar))
								p = pd.DataFrame(a, columns=cols)
								print(p)
								dicC[dt] = p
							pbar.close()
							self.dftem = dicC
						else:
							print('met.py TODO: unsupported location code (not sure this should occur??)')
							quit()
					# print('complete')				
				elif nvar==0:
					if self.prcn != 8 and self.prcn != 4: quit() # todo				
					dicC = {}
					while True:
						f1 = f.read(4)
						if f1 == b'': break # EOF
						lid = struct.unpack('<i', f1)[0] # location id
						nval = struct.unpack('<i', f.read(4))[0] # number of values						
						if self.prcn==4:
							fmt = 'qQf'*nval
							df = pd.DataFrame(np.asarray(struct.unpack('<' + fmt, f.read(20*nval))).reshape(-1,3))
						else:
							fmt = 'qQd'*nval
							df = pd.DataFrame(np.asarray(struct.unpack('<' + fmt, f.read(24*nval))).reshape(-1,3))
						df.columns = ['Date','wbc','val'] #({0:'Date', 1:"wbc", 2:'val'}, inplace=True)
						df['Date'] = df['Date'].apply(lambda t: toPOSIX(t))
						df = df.pivot(index='Date',columns='wbc',values='val')
						df.rename(columns=wbcode.DataTypeToDict(), inplace=True)
						dicC[lid] = df							
					self.dftem = dicC
				elif self.nloc==1: # special case, 1 station met file
					if self.prcn != 8 and self.prcn != 4: quit() # todo	
					rows = []
					dts = []				
					while True:
						f1 = f.read(8)
						if f1 == b'': break # EOF
						dts.append(toPOSIX(struct.unpack('<q', f1)[0]))
						if self.prcn==4:
							fmt = 'f'*nvar
							rows.append(np.asarray(struct.unpack('<' + fmt, f.read(4*nvar))))
						else:
							fmt = 'd'*nvar
							rows.append(np.asarray(struct.unpack('<' + fmt, f.read(8*nvar))))
					self.dftem = pd.DataFrame(rows, columns=self.wbc.dts).replace(-9999.0, np.nan)
					self.dftem.insert(0, "Date", dts, True)
					self.dftem.set_index('Date', inplace=True)						
				else:				
					if self.prcn == 8:
						fmt = 'i' + str(nvar) + 'd'
						cols = ['id'] + self.wbc.dts
						dicC = {}
						while True:
							f1 = f.read(8)
							if f1 == b'': break # EOF
							dt = toPOSIX(struct.unpack('<q', f1)[0])					
							nloc = struct.unpack('<I', f.read(4))[0]
							a = struct.unpack('<' + fmt*nloc, f.read((4+8*nvar)*nloc))
							a = np.reshape(a, (-1,nvar+1))
							p = pd.DataFrame(a, columns=cols)
							p.set_index('id', inplace=True)
							dicC[dt] = p
						self.dftem = dicC
					else:
						print('met.py TODO: irregular data at known intervals')
						quit()

	def readChunk(self):
		def errmsg():
			print("readChunk error")
			quit()
		nvar = len(self.wbc.dts)
		if self.intvl > 0:
			if self.lc == 0:
				if self.prcn == 4:
					a = np.frombuffer(self.f.read(self.nloc*nvar*4), dtype=np.single)
				elif self.prcn == 8:
					a = np.frombuffer(self.f.read(self.nloc*nvar*8))
				else:
					print("precicion not supported") # todo 
				return(np.reshape(a, (self.nloc,nvar)))
			else:
				errmsg()
		else:
			errmsg()
		return(None)

	def Info(self):
		print('\n  ================= met load, version', self.v)
		print('  unit code', self.uc)
		print('  time code', self.tc)
		if len(self.wbc.dts) > 0:
			print('  waterbalance code', self.wbc.wbc)
			print('  waterbalance list')
			for u in self.wbc.dts:
				print('    '+u)
		print('  precision', self.prcn)		
		if self.intvl > 0:
			print('  interval', self.intvl)
			print('  start time', self.dtb.strftime('%Y-%m-%d %H:%M:%S'))
			print('  end time', self.dte.strftime('%Y-%m-%d %H:%M:%S'))
		print('  location code', self.lc)
		print('  ESPG code', self.espg)
		print('  nLocations', self.nloc) #, '\n')

	def Locations(self):
		if self.lc==1:
			subset = self.dfloc[['id']]
			return({x[0]:tuple(x[0]) for x in subset.values})
		elif self.lc==12:
			subset = self.dfloc[['id', 'E', 'N']]
			return({x[0]:tuple(x[1:]) for x in subset.values})

	def yielddates(self):
		if self.intvl == 86400:
			for n in range(int((self.dte - self.dtb).days)+1):
				yield self.dtb + timedelta(n)
		elif self.intvl > 0:
			f = 86400/self.intvl
			for n in range(int((self.dte - self.dtb).days*f)+1):
				yield self.dtb + timedelta(seconds=n*self.intvl)
		else:
			self.dftem.sort_index(inplace=True)
			for dt in self.dftem.index:
				yield dt

	def getDateSet(self): # def getContainedDates(self):
		s = set()
		for dt in self.yielddates():
			print(dt)
			s.add(dt)
		return s

	def getSortedDates(self): 
		s = list()
		for dt in self.yielddates():
			s.append(dt)
		return s

	def getWinters(self, wb=10, we=6):
		dts = self.getSortedDates()
		lst = list()
		lstt = list()
		blOn = False
		for dt in dts: 
			if blOn:
				if dt.month==we:
					blOn = False
					if len(lstt) > 128:
						lst += lstt
				else:
					lstt.append(dt)
			else:
				if dt.month==wb:
					blOn = True
					lstt = list()
		return lst




	def getLocations(self, br, rec):
		if self.lc == 1:
			if self.nloc==1:
				self.dfloc = struct.unpack('<i', br.read(4))[0] # id
			else:
				a = np.zeros((self.nloc,1),type=int)
				for i in range(self.nloc):
					a[i,0] = struct.unpack('<i', br.read(4))[0] # id
					rec += 4
				self.dfloc = pd.DataFrame(a, columns=['id'])
			# self.dfloc['id'] = self.dfloc['id'].astype(int)	
		elif self.lc == 2:
			a = np.zeros((self.nloc,2),dtype=int)
			for i in range(self.nloc):
				a[i,0] = struct.unpack('<i', br.read(4))[0] # row
				a[i,1] = struct.unpack('<i', br.read(4))[0] # col
				rec += 8
			self.dfloc = pd.DataFrame(a, columns=['i','j'])
			# self.dfloc['i'] = self.dfloc['i'].astype(int)				
			# self.dfloc['j'] = self.dfloc['j'].astype(int)				
		elif self.lc == 12:
			a = np.zeros((self.nloc,3))
			for i in range(self.nloc):
				a[i,0] = struct.unpack('<i', br.read(4))[0] # id
				a[i,1] = struct.unpack('<d', br.read(8))[0] # x
				a[i,2] = struct.unpack('<d', br.read(8))[0] # y
				rec += 20
			self.dfloc = pd.DataFrame(a, columns=['id','XE','YN']).replace(-9999.0, np.nan)
			self.dfloc['id'] = self.dfloc['id'].astype(int)
			if self.nloc==1: 
				a = self.dfloc.values.tolist()[0]
				print('  id '+str(int(a[0])))
				print('  E '+str(a[1]))
				print('  N '+str(a[2]))
		else:
			print('location code',self.lc,'currently not supported')
			quit()
		return rec

	def convertToUTM17(self):
		if self.espg != 26917:
			outProj = pyproj.Proj(init='epsg:26917')
			if self.espg == 3857 or self.espg == 4326: # in earlier cases, ESPG was incorrectly set to WGS84 pseudo mercator, and not WGS84 proper
				inProj = pyproj.Proj(init='epsg:4326')
				# def rule(row):
				# 	re, rn, d1, d2 = utm.from_latlon(row['YN'],row['XE'])
				# 	return pd.Series({"E": re, "N": rn})				
				# self.dfloc = self.dfloc.merge(self.dfloc.apply(rule, axis=1), left_index= True, right_index= True)			
			else:
				inProj = pyproj.Proj(init='epsg:' + str(self.espg))
			self.dfloc['E'], self.dfloc['N'] = pyproj.transform(inProj,outProj, self.dfloc['XE'].tolist(), self.dfloc['YN'].tolist())

	def WriteToFile(self, fp):		
		with open(fp, 'bw') as f:
			self.WriteHeader(f)
			# write data
			if self.wbc==0:
				print('met.py TODO: irregular data at known intervals')
				quit()
			else:
				if self.intvl > 0:
					if self.lc==0:
						print('TODO: grid-based writer')
						quit()					
					pbar = tqdm(total=int((self.dte - self.dtb).days*86400/self.intvl)+1)
					mss = set()
					for dt in self.yielddates():
						pbar.update()
						pbar.set_description(dt.strftime(' %Y-%m-%d %H:%M:%S'))
						if not dt in self.dftem:
							mss.add(dt)
						else:
							if self.wbc == 0:
								f.write(struct.pack('<I', len(self.dftem[dt]))) # number of locations with values on date 'dt'
								for k, v in self.dftem[dt].items():
									f.write(struct.pack('<i', k))
									f.write(struct.pack('<d', v)) # currently assumes only one value per station
							else:
								for _, v in self.dftem[dt].items():
									f.write(struct.pack('<d', v))
					pbar.close()
					if len(mss) > 0:
						print(' missing dates:')
						for v in mss:
							print('  ',v)
				else:
					if self.lc==0:
						print('TODO: grid-based writer')
						quit()					
					pbar = tqdm(total=len(self.dftem))
					for dt in sorted(self.dftem.index):
						pbar.update()
						pbar.set_description(dt.strftime('%Y-%m-%d'))
						f.write(struct.pack('<q', int(dt.replace(tzinfo=timezone.utc).timestamp()))) # date
						if self.wbc == 0:
							f.write(struct.pack('<I', len(self.dftem[dt].index))) # number of locations with values on date 'dt'
							r = self.dftem[dt].to_records(index=False)
							r = r.astype([('id', '<i4'), ('8', '<f8')])
							r.tofile(f)	
						else:
							a = self.dftem.loc[dt].values
							if self.prcn == 4:
								fmt = 'f'*len(a)
								f.write(struct.pack('<'+fmt, *a))
							elif self.prcn == 8:
								fmt = 'd'*len(a)
								f.write(struct.pack('<'+fmt, *a))
								pass
							else:
								print('TODO')
								quit()		
					pbar.close()

	def WriteHeader(self, bw):
		bw.write(struct.pack('<H', self.v)) # version
		bw.write(struct.pack('<B', self.uc)) # unit code
		bw.write(struct.pack('<B', self.tc)) # time code
		if self.wbc==0:
			bw.write(struct.pack('<Q', 0)) # waterbalance code given at every entry
		else:
			bw.write(struct.pack('<Q', self.wbc.wbc)) # waterbalance code
		bw.write(struct.pack('<B', self.prcn)) # data precision
		bw.write(struct.pack('<Q', self.intvl)) # data interval (sec)
		# bw.write(struct.pack('<q', int(self.dtb.timestamp())))
		# bw.write(struct.pack('<q', int(self.dte.timestamp())))
		if self.intvl > 0:
			bw.write(struct.pack('<q', int(self.dtb.replace(tzinfo=timezone.utc).timestamp())))
			bw.write(struct.pack('<q', int(self.dte.replace(tzinfo=timezone.utc).timestamp())))
		bw.write(struct.pack('<b', self.lc)) # location code
		bw.write(struct.pack('<I', self.espg)) # espg projection code
		bw.write(struct.pack('<I', self.nloc)) # number of location listed

		if self.lc > 0:
			if self.lc == 1:
				if type(self.dfloc)==list:
					bw.write(struct.pack('%si' % self.nloc, *self.dfloc))
				else:
					print('unknown dfloc type: ' + str(type(self.dfloc)))
			elif self.lc == 12:
				pbar = tqdm(total=self.nloc, desc=' writing locations')				
				for _, row in self.dfloc.iterrows():
					pbar.update()
					bw.write(struct.pack('<i', int(row['id'])))
					bw.write(struct.pack('<d', row['XE']))
					bw.write(struct.pack('<d', row['YN']))
				pbar.close()
			else:
				print('location code',self.lc,'currently not supported')

	def WriteTemDict(self, bw, dTem):
		for i in dTem: # dictionary int{list]}
			bw.write(struct.pack('<i', i))
			if self.lc == 12:
				if self.prcn == 4:
					for v in dTem(i):
						bw.write(struct.pack('<f', v))
				elif self.prcn == 8:
					for v in dTem(i):
						bw.write(struct.pack('<d', v))
			else:
				print('location code',self.lc,'currently not supported')

	def InterpretToGDEF(self,gd,dt,field,method='nearest'):
		v = self.dftem.get(dt).dropna()
		if v is None: 
			return np.zeros((gd.nrow,gd.ncol))
		m = pd.merge(v, self.dfloc, on='id', indicator=True)
		subset = m[['E', 'N', field]]
		d = {tuple(x[:2]):x[2] for x in subset.values}
		grid_x, grid_y = gd.nullMgrid()
		a = griddata(np.array(list(d.keys())), np.array(list(d.values())), (grid_x, grid_y), method=method) # 'nearest' 'linear' 'cubic'
		return(a.T)