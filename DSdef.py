### dataset definition class

class DSdef():

	def __init__(self):

                self.Vconndata_struct = []
                self.Vconndata_rows = []
		self.Vconndata_head = ""
		self.Vconndata_srows = []

                self.Vdbdata_struct = []
                self.Vdbdata_rows = []
		self.Vdbdata_head = ""
		self.Vdbdata_srows = []

                self.Vinstdata_struct = []
                self.Vinstdata_rows = []
		self.Vinstdata_row_old = []
		self.Vinstdata_head = ""
		self.Vinstdata_srows = []

		self.Vtbsdata_struct = []
		self.Vtbsdata_rows = []
		self.Vtbsdata_head = ""
		self.Vtbsdata_srows = []

                self.Vtopsql_struct = []
                self.Vtopsql_rows = []
                self.Vtopsql_head = ""
                self.Vtopsql_srows = []

                self.Vsessdata_struct = []
                self.Vsessdata_rows = []
		self.Vsessdata_head = ""
		self.Vsessdata_srows = []
		self.Vsessdata_sql_plan = []

		# init data structs 
		self.setconinfoDS()
		self.setdbDS()
		self.setinstDS()
		self.setsessDS()
		self.settbsDS()
		self.settopsqlDS()

		# make row header
		self.Vconndata_head = self.makeheadshow(self.Vconndata_struct)
		self.Vdbdata_head = self.makeheadshow(self.Vdbdata_struct)
		self.Vinstdata_head = self.makeheadshow(self.Vinstdata_struct)
		self.Vsessdata_head = self.makeheadshow(self.Vsessdata_struct)
		self.Vtbsdata_head = self.makeheadshow(self.Vtbsdata_struct)
		self.Vtopsql_head = self.makeheadshow(self.Vtopsql_struct)


	def setconinfoDS(self):
                self.Vconndata_struct = [ \
('Username','str',20,1,1), \
('InstName','str',10,1,1), \
('ConName','str',15,1,1), \
('Auth mode','str',15,1,1), \
('Server host','str',20,1,1)
]

                self.Vconndata_rows = []

	def setdbDS(self):
                self.Vdbdata_struct = [ \
('DbName','str',9,1,1), \
('LogMode','str',12,1,1), \
('FlashBack','str',9,1,1), \
('DBRole','str',16,1,1), \
('ProtectMode','str',20,1,1), \
('DGBroker','str',8,1,1), \
('RAC','str',3,1,1), \
('Instances','int',9,1,1), \
('Time','str',8,0,1) \
]
                self.Vdbdata_rows = []

	def setinstDS(self):
                self.Vinstdata_struct = [
('Inst','str',4,1,1), \
('Name','str',15,1,1), \
('Status','str',10,1,0), \
('OpenDate','str',16,1,0), \
('Sess','int',4,1,1), \
('Asess','int',5,1,1), \
('CpuB','int',4,0,0), \
('CpuI','int',4,0,0), \
('CpuBusy','int',7,1,1), \
('CpuIdle','int',7,1,1), \
('|','str',1,1,1), \
('DBT','int',4,0,0), \
('DBCpu','int',4,0,0), \
('SQLX','int',4,0,0), \
('SQLPa','int',5,0,0), \
('SQLHP','int',5,0,0), \
('PL','int',2,0,0,0), \
('DBTime%CW', 'int',9,1,1), \
('DBT_SUM','str',7,0,0), \
('DBCpu-%DBT','int',10,1,1), \
('SQL-Xela%DBT','int',12,1,1), \
('SQL-Pela%DBT','int',12,1,1), \
('SQL-HPela%DBT','int',13,1,1), \
('PLela%DBT','int',9,1,0), \
('|','str',1,1,1), \
('PgaTotB','int',6,0,0), \
('PgaXRW','int',6,0,0), \
('PgaHit','int',6,1,1), \
('CHBGETS','int',6,0,0), \
('CHCGETS','int',6,0,0), \
('CHPHR','int',6,0,0), \
('CacheHit','str',8,1,1), \
('TXS','int',8,0,0), \
('TransRate','str',9,1,1), \
('RedoW','int',5,0,0) \
]
                self.Vinstdata_rows = []


	def setsessDS(self):
                self.Vsessdata_struct = [ \
('Sid','str',9,1,1), \
('Serial#','int',7,1,1), \
('Inst','int',4,1,1), \
('Username','str',17,1,1), \
('Program','str',17,1,1), \
('Event','str',42,1,1), \
('Duration','int',8,1,0), \
('SQLID/child','str',19,1,1), \
('SQLAVela','int',10,1,1), \
('SQLRows','int',9,1,1), \
('SQLExcs','int',8,1,1), \
('FSop','str',6,1,1), \
('BLKI','str',4,0,0), \
('BLKS','str',4,0,0), \
('LOCKWAIT','str',10,0,0), \
('BLKer-I/S','str',9,1,1), \
('PWait','str',6,0,0), \
('STATUS','str',10,0,0), \
('STATE','str',10,1,0), \
('WClass','str',13,1,0), \
('QC-I/S','str',8,1,0), \
('SQLID','str',0,0,0), \
('SQLCHILD','int',0,0,0), \
('SQLTEXT','str',0,0,0), \
('PLANHASH','int',8,0,0), \
('FULLUSERNAME','str',8,0,0), \
('FULLPRGNAME','str',8,0,0), \
('MACHINENAME','str',8,0,0), \
('THISSTATEMENT','str',8,0,0) \
]
                self.Vsessdata_rows = []

	def settbsDS(self):
		self.Vtbsdata_struct = [ \
('Tablespace - online','str',30,1,1), \
('Status','str',7,0,0), \
('MaxSizeMB','int',10,1,1), \
('%Used','int',6,1,1) \
]
		self.Vtbsdata_rows = []

	def settopsqlDS(self):
		self.Vtopsql_struct = [ \
('Inst','str',4,1,1), \
('Schema','str',15,1,1), \
('SQLID','str',13,1,1), \
('PlanHash','int',10,1,1), \
('VCount','int',6,1,1), \
('SQLProfile','str',25,1,1), \
('CpuTime','int',7,1,1), \
('AvgEla','int',6,1,1), \
('AvgExecs','int',8,1,1), \
('AvgRows','int',7,1,1), \
('IOWms','str',7,1,1), \
('CLWms','str',8,1,1), \
('APWms','str',7,1,1), \
('CCWms','str',8,1,1), \
('PQuery','str',6,1,1), \
('FSop','str',7,1,1), \
('SnapId','int',7,1,1) \
]
		self.Vtopsql_rows = []


	def makeheadshow(self,data_struct):                        
		# make header 
		head=""
		if len(data_struct) > 0:
			for i in range(0,len(data_struct)):
				if data_struct[i][2] > 0 and data_struct[i][3] == 1:       # column size >0 and active
					if (data_struct[i][4] == 0 and self.ScreenFullSize) | (data_struct[i][4] == 1) : # use columnm, if not mandatory, but full screen is maxsized, or column is mandatory
        					head += data_struct[i][0].ljust(int(data_struct[i][2]))
                				if i <= len(data_struct)-1:
        						head +=  ' '
		return(head)
		

	def makelineshow(self,data_rows,data_struct, DSdescr):
		# costruisce righe da visualizzare come stringhe , con interspazi calcolati in base alla struttura
		rows=[]
		if len(data_rows) > 0:
			try:
				for i in range(0,len(data_rows)):
        				tmp_row=""
        				for j in range(0,len(data_rows[i])):
						if (data_struct[j][2] > 0) and (data_struct[j][3] == 1):  # column size >0 and active
							if (data_struct[j][4] == 0 and self.ScreenFullSize) | (data_struct[j][4] == 1) : # use column, if not mandatory, but full screen is maxsized, or column is mandatory
                						col = data_rows[i][j]
                						if data_struct[j][1] == 'int':
                       							col = str(data_rows[i][j])
	
                						tmp_row += col.ljust(data_struct[j][2])
                						if j <= len(data_rows[i])-1:
                       							tmp_row += ' '
       					rows.append(tmp_row)
			except Exception as err:
				self.WinPrintError("makelineshow error: " + str(err) )
	
		return(rows)

