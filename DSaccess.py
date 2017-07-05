#dataaccess class

import cx_Oracle
import time
import threading
from DSdef import DSdef

class DSaccess(DSdef):

        def __init__(self,logininfo):

		self.cpool_min = 3
		self.cpool_max = 5 
		self.cpool_incr = 1

		self.tHshowtimeconn = 0
		self.idthshowconntimer = 0
		self.ThshowconntimerSTOP = threading.Event()

		self.logininfo = logininfo

		self.startTDb = round(time.time(),0)
		initthshowconntimer = self.DBInitShowConnTimer()

		oconn = self.DBconnect()

		if initthshowconntimer:
			self.ThshowconntimerSTOP.set()  # stop thread that show connection timer, if initialized

		if oconn != -1:  # database connection  ok
			self.WinPrintError("                           " )

			self.DBversion()

			self.DBsessionOrder = 1     # sort key for session box. Range: 1-4 . Default =1 for avgela column
	
			self.reconnect = 0  # counter of reconnections to database
			self.retryconnect = 1 # num of retry connect


	########################
	### DATABASE METHODS ###
	########################

	def DBconnect(self):
		try:
        		self.Voracle_connect = cx_Oracle.SessionPool(self.logininfo[0],self.logininfo[1],self.logininfo[2]+"/"+self.logininfo[3] , self.cpool_min , self.cpool_max, self.cpool_incr,threaded = True)
   		except Exception as err:
                       	self.Voracle_connect = -1
		finally:
			pass

		return(self.Voracle_connect)

	def DBreconnect(self):
		try:
			self.startTDb = round(time.time(),0)
			if not self.idthshowconntimer.is_alive():
				initthshowconntimer = self.DBInitShowConnTimer()
			else:
				self.ThshowconntimerSTOP.clear()

			oconn = self.DBconnect()

			if self.idthshowconntimer.is_alive():
				self.ThshowconntimerSTOP.set()  # stop thread that show connection timer, if initialized

		except Exception as err:
			self.WinPrintError("DB reconnect module : "+str(err)+ "          " )
			oconn = -1

		return(oconn)


        def DBclose(self):
                if self.Voracle_connect != -1:
			try:
				self.Voracle_connect.close()
			except:
				pass

	def DBInitShowConnTimer(self):
		try:
			self.ThshowconntimerSTOP.clear()
			self.idthshowconntimer = threading.Thread(target=self.DBShowTimerConnectTH,args=(self.ThshowconntimerSTOP,) )
			self.idthshowconntimer.setDaemon(True)
			self.idthshowconntimer.start()
			result = 1
		except Exception as err:
			result = -1
			self.WinPrintError("Init Thread showconntimer KO  :"+str(err)+ "          " )

		return(result)

	def DBShowTimerConnectTH(self, stopTH_event ):
		while ( not stopTH_event.is_set() ):
			new_stop_event = stopTH_event.wait(1)
			if new_stop_event:
				self.WinPrintError("                           " )
			else:
				dbelaptryconn = str(int(round(round(time.time(),0) - self.startTDb,0) ) )
				msg = "DB Connecting.... " + dbelaptryconn + "s     "
				self.WinPrintError(msg)
			

        def DBGetCursorData(self, sql, id_th):
                result = []
                tryconn = 0
                while tryconn<2:
                        try:
				connection = self.Voracle_connect.acquire()
                                cursor = connection.cursor()

				if id_th >= 0:
					self.WinThUpdate(id_th, self.TH_SQL_RUNNING) 

                                cursor.execute(sql)
                                cursor.arraysize = 1500

				if id_th >= 0:
					self.WinThUpdate(id_th, self.TH_ROW_FETCHING) 

                                for row in cursor:  # fetch rows
				        newrow=[]

        				for i in range(0,len(row)):
                				if type(row[i]) is cx_Oracle.LOB:
                        				newrow.append(row[i].read() )   # read lob locator
                				else:
                        				newrow.append(row[i])
                                        result.append(list(newrow))

                                cursor.close()

				self.Voracle_connect.release(connection)
                                break
                        except Exception  as err:
                                result=[]
				if id_th >= 0:
					self.WinThUpdate(id_th,self.TH_REQUEST_DB_CONN) 

                                self.lockdbconn.acquire()

                                if self.DBpingconn(self.Voracle_connect) == 0:   #  global connection handle status broken
					if id_th >= 0:
						self.WinThUpdate(id_th,self.TH_DB_RECONNECTING) 

                                        oconn = self.DBreconnect()

                                        if oconn < 0:    #error on reconnecting
                                                tryconn = 2  # exit  try
                                                result=-1
                                        else:
                                                tryconn += 1
                                else:
                                        tryconn = 2 #exit try
                                        result=-1

                                self.lockdbconn.release()

                return(result)

        def DBpingconn(self,conn):
                try:
                        conn.ping()
                        connstatus=1  # conn is alive
                except:
                        connstatus=0  #conn is broken

                return(connstatus)

        def DBversion(self):
                if self.Voracle_connect != -1:
			connection = self.Voracle_connect.acquire()
			self.OracleVersion = connection.version
			self.Voracle_connect.release(connection)
			return(self.OracleVersion)
                else:
			return("0")

        def DBbanner(self):
		banner=""
                if self.Voracle_connect != -1:
			try:
				connection = self.Voracle_connect.acquire()
				orainfo = connection.cursor()
                        	orainfo.execute("SELECT PLATFORM_NAME from v$database")
				dbplatf=orainfo.fetchone()
				try:
					orainfo.execute("select count(*) from (select distinct cell_name from gv$cell_state)")
					is_exadata=orainfo.fetchone()
					ncells = is_exadata[0]
				except:
					ncells = 0
				if ncells > 0:
					exadata_msg = "- EXADATA with "+str(ncells)+" cells "
				else:
					exadata_msg = ""
				
                        	banner="Oracle Database "+self.OracleVersion+" on "+dbplatf[0]+"  " + exadata_msg + "    "
                        	orainfo.close()
				self.Voracle_connect.release(connection)
				error = 0
			except Exception as err:
				error = 1
				self.WinPrintError("DBbanner Warning : "+str(err) )

			if error: #db error
                                banner="DB ERROR"

                return(banner)

	def DBconnectioninfo(self):
			conn_info=[]
                        trycnt = 1
                        while trycnt<=self.retryconnect:   
				try:
                        		sql12c = "SELECT \
sys_context('USERENV','SESSION_USER') UNAME, \
sys_context('USERENV','INSTANCE_NAME') INSTNAME, \
sys_context('USERENV','CON_NAME') CNAME, \
sys_context('USERENV','AUTHENTICATION_METHOD') AUTH, \
sys_context('USERENV','SERVER_HOST') SHOST from dual"

                        		sql_no_12 = "SELECT \
sys_context('USERENV','SESSION_USER') UNAME, \
sys_context('USERENV','INSTANCE_NAME') INSTNAME, \
'          ' CNAME, \
'          ' AUTHM, \
sys_context('USERENV','SERVER_HOST') SHOST from dual"


					if self.OracleVersion[:2] == '12':   # select for 12c version
						conn_info = self.DBGetCursorData(sql12c, self.ID_PAD_CI)
					else:
						conn_info = self.DBGetCursorData(sql_no_12, self.ID_PAD_CI)

					if conn_info == -1:  #query error
						conn_info=[('DB ERROR',' ',' ',' ',' ')]
                                		self.Vconndata_rows = conn_info
                                		self.Vconndata_srows = self.makelineshow(conn_info,self.Vconndata_struct,'conninfo')
						trycnt=2 # exit try
					else:
						self.Vconndata_rows = conn_info
						self.Vconndata_srows = self.makelineshow(conn_info,self.Vconndata_struct,'conninfo')
						#self.WinCprint(2,1, '>'+self.Vconndata_srows[0]+'<' )
						break
				except Exception as err:
					self.WinPrintError("DBconnectioninfo exception: "+str(err) )

			return(conn_info)
	
        def DBdatainfo(self):
                	dbinfo = []
                        trycnt = 1
                        while trycnt<=self.retryconnect: 
                                try:
					sql = "SELECT name,log_mode,FLASHBACK_ON,DATABASE_ROLE,PROTECTION_MODE,DATAGUARD_BROKER, (SELECT decode(value,'TRUE','yes','no') from v$parameter where name='cluster_database') ISCLUST, \
(SELECT count(*) from gv$instance) COUNT_INST,  to_char(sysdate,'hh24:mi:ss')  FROM v$database"

   					dbinfo=self.DBGetCursorData(sql, self.ID_PAD_DB)

					if dbinfo == -1: # query error
                               			dbinfo=[('DB ERROR',' ',' ',' ',' ',' ',' ',0,' ')]
						self.Vdbdata_rows = dbinfo
						self.Vdbdata_srows = self.makelineshow(dbinfo,self.Vdbdata_struct,'dbdata')
						trycnt = 2 #exit try
					else:
						self.Vdbdata_rows = dbinfo
						self.Vdbdata_srows = self.makelineshow(dbinfo,self.Vdbdata_struct,'dbdata')
						trycnt=0
						break
				except Exception as err:
					self.WinPrintError("DBdatainfo exception: "+str(err) )

                	return(dbinfo) 

	def DBinstinfo(self):
			instinfo_new = []
			S1 = []
   			S2 = []
   			S3 = []
                        trycnt = 1
                        while trycnt<=self.retryconnect:
                                try:
   					sql1 = "SELECT to_char(instance_number),instance_name,status,to_char(STARTUP_TIME,'dd-mm-yyyy hh24:mi') from gv$instance order by instance_number"

   					sql2 = "SELECT to_char(a.inst_id),(select count(*) from gv$session where  inst_id=a.inst_id), \
(select  count(*) from gv$session  where status='ACTIVE' and inst_id=a.inst_id and username is not null) from gv$session a group by a.inst_id  order by a.inst_id "

   					sql3 = "select  to_char(inst_id), \
(select  value from gv$osstat where inst_id=b.inst_id and stat_name='BUSY_TIME') BT, \
(select  value from gv$osstat where inst_id=b.inst_id and stat_name='IDLE_TIME') IT, \
0,0, \
'|', \
(select  value from gv$sys_time_model where  b.inst_id=inst_id and stat_name='DB time') DBT, \
(select  value from gv$sys_time_model where b.inst_id=inst_id and stat_name='DB CPU') DBCPU, \
(select  value from gv$sys_time_model where b.inst_id=inst_id and stat_name='sql execute elapsed time') SELA, \
(select  value from gv$sys_time_model where b.inst_id=inst_id and stat_name='parse time elapsed') SPELA, \
(select  value from gv$sys_time_model where b.inst_id=inst_id and stat_name='hard parse elapsed time') SHPELA, \
(select  value from gv$sys_time_model where b.inst_id=inst_id and stat_name='PL/SQL execution elapsed time') PLELA, \
0,0 SUMDBT_CW,0,0,0,0,0, \
'|', \
(select value from gv$PGASTAT where NAME='bytes processed' and inst_id=b.inst_id) PGATOTB, \
(select value from gv$PGASTAT where NAME='extra bytes read/written' and inst_id=b.inst_id) PGAXRW, \
0 PGAHIT, \
(select value from GV$SYSSTAT where name='db block gets from cache' and  inst_id=b.inst_id) CHBGETS, \
(select value from GV$SYSSTAT where name='consistent gets from cache' and  inst_id=b.inst_id) CHCGETS, \
(select value from GV$SYSSTAT where name='physical reads cache' and  inst_id=b.inst_id) CHPHR, \
'0' CHR, \
(select sum(value) from GV$SYSSTAT where name in ('user commits','user rollbacks') and inst_id=b.inst_id) TXS, \
'0' TRANSEC, \
0 \
from gv$instance b \
group by inst_id  \
order by inst_id \
"
					S_error = 0

					S1 = self.DBGetCursorData(sql1, self.ID_PAD_INST)

					if S1 != -1:
						S2 = self.DBGetCursorData(sql2, self.ID_PAD_INST)
						if S2 != -1:
							S3 = self.DBGetCursorData(sql3, self.ID_PAD_INST)
							if S3 == -1:
								S_error = -1
						else:
							S_error = -1
					else:
						S_error = -1


					if S_error == -1:   #  query error
					        instinfo_new=[('DB ERROR',' ',' ',' ',0,0,0,0,0,0,'|',0,0,0,0,0,0,0,' ',0,0,0,0,0,'|',0,0,0,0,0,0,' ',0,' ',0)]
                                                self.Vinstdata_rows = instinfo_new
                                                self.Vinstdata_srows = self.makelineshow(instinfo_new,self.Vinstdata_struct,'instdata')
                                                trycnt = 2 #exit try
					else:
   						# make new list L joining S1,S2,S3 skipped first column from S2 and S3
   						for i in range(0,len(S1)):
      							a=list(S1[i])
      							for j in list(S2[i][1:]):
       								a.append(j)
      							for k in list(S3[i][1:]):
       								a.append(k)
      							instinfo_new.append(tuple(a))

						L_instinfo = []
						instinfo_old = self.Vinstdata_row_old

						dbt_sum_new = 0.0
						dbt_sum_old = 0.0
						for k in range(0,len(instinfo_new)):
							#sum DBTIME  dbt
							dbt_sum_new += instinfo_new[k][11]
							if len(self.Vinstdata_row_old) > 0:
								dbt_sum_old += self.Vinstdata_row_old[k][11]

						for j in range(0,len(instinfo_new)):
							L_row = list(instinfo_new[j])
							if len(self.Vinstdata_row_old) > 0:
								cbusy_old = instinfo_old[j][6] + .0
								cidle_old = instinfo_old[j][7] + .0
								tcpu_old = cbusy_old + cidle_old + .0
								dbt_old = instinfo_old[j][11] + .0
								dbcpu_old = instinfo_old[j][12] + .0
								sela_old = instinfo_old[j][13] + .0
								spela_old = instinfo_old[j][14] + .0
								shpela_old = instinfo_old[j][15] + .0
								plsql_old = instinfo_old[j][16] + .0
								pdbt_old = float(instinfo_old[j][17][:-1]) + .0
								pga_totb_old = instinfo_old[j][25] + .0
								pga_xrw_old = instinfo_old[j][26] + .0
								cache_hit_bgets_old = instinfo_old[j][28] + .0
								cache_hit_cgets_old = instinfo_old[j][29] + .0
								cache_hit_pr_old = instinfo_old[j][30] + .0
								txs_old = instinfo_old[j][32] + .0
							else:
								cbusy_old = 0.0
								cidle_old = 0.0
								tcpu_old = 0.0
								dbt_old = 0.0
								dbcpu_old = 0.0
								sela_old = 0.0
								spela_old = 0.0
								shpela_old = 0.0
								plsql_old = 0.0
								pdbt_old = 0.0
								pga_totb_old = 0.0
								pga_xrw_old = 0.0
								cache_hit_bgets_old = 0.0
								cache_hit_cgets_old = 0.0
								cache_hit_pr_old = 0.0
								txs_old = 0.0

							# instance cpu calc
							cbusy_new = instinfo_new[j][6] - cbusy_old 
							cidle_new = instinfo_new[j][7] - cidle_old
							tcpu_new = cbusy_new + cidle_new
							pbusy = round(cbusy_new*100/tcpu_new,2)
							pidle = round(cidle_new*100/tcpu_new,2)
							L_row[8] = pbusy
							L_row[9] = pidle

							# dbtime calculations
							dbt_new = instinfo_new[j][11] - dbt_old

							dcpu_new = instinfo_new[j][12] - dbcpu_old
							sela_new = instinfo_new[j][13] - sela_old
							spela_new = instinfo_new[j][14] -  spela_old
							shpela_new = instinfo_new[j][15] - shpela_old
							plsql_new = instinfo_new[j][16] - plsql_old

			        			pdbt_new = round(dbt_new*100/(dbt_sum_new-dbt_sum_old),2)	
							pdcpu_new = round(dcpu_new*100/dbt_new,2)
							psela_new = round(sela_new*100/dbt_new,2)
							pspela_new = round(spela_new*100/dbt_new,2)
							pshpela_new = round(shpela_new*100/dbt_new,2)
							pplsql_new = round(plsql_new*100/dbt_new,2)
		
							if pdbt_new > pdbt_old:  #compare %dbtime between old and new value, to append + or - suffix
								pdbt_new_s = str(pdbt_new)+'+'
                                			else:
								if pdbt_new < pdbt_old:
									pdbt_new_s = str(pdbt_new)+'-'
								else:
									pdbt_new_s = str(pdbt_new)+ ' '

							# pga hit calc
							pga_totb_new = instinfo_new[j][25] - pga_totb_old
							pga_xrw_new = instinfo_new[j][26] - pga_xrw_old
							pga_hit = round(100*pga_totb_new/(pga_totb_new+pga_xrw_new),2)

							# cache hit calc
							cache_hit_bgets_new = instinfo_new[j][28] - cache_hit_bgets_old
							cache_hit_cgets_new = instinfo_new[j][29] - cache_hit_cgets_old
							cache_hit_pr_new =    instinfo_new[j][30] - cache_hit_pr_old
							if cache_hit_bgets_new+cache_hit_cgets_new > 0:
								cache_hit = str(100*round(1-(cache_hit_pr_new/(cache_hit_bgets_new+cache_hit_cgets_new)),2))
							else:
							 	cache_hit = '-'

							# transaction x second calc
							txs_new = instinfo_new[j][32] - txs_old

							if txs_new > 0:
								# make transaction per second as string, using K (>1000), M(>1000000, G(>1000000000) as suffix
								txs_string = str(int(txs_new))
								if txs_new >= 1000 and txs_new<1000000:
									txs_string = str(round(txs_new/1000,1))+"K"
								if txs_new >=1000000 and txs_new<1000000000:
									txs_string = str(round(txs_new/1000000,1))+"M"
								if txs_new >=1000000000:
									txs_string = str(round(txs_new/1000000000,1))+"G"
							else:
								txs_string = "-"
								

							L_row[17] = pdbt_new_s
							L_row[18] = dbt_sum_new
							L_row[19] = pdcpu_new
							L_row[20] = psela_new
							L_row[21] = pspela_new
							L_row[22] = pshpela_new
							L_row[23] = pplsql_new

							L_row[27] = pga_hit
							L_row[31] = cache_hit
							L_row[33] = txs_string

							L_instinfo.append(L_row)

						self.Vinstdata_rows = L_instinfo
						instinfo_new = L_instinfo
						self.Vinstdata_srows = self.makelineshow(instinfo_new,self.Vinstdata_struct,'instdata')
						self.Vinstdata_row_old = self.Vinstdata_rows

						break
				except Exception as err:
					self.WinPrintError("DBinstinfo exception:      "+str(err)+"   " )
					
                	return(instinfo_new) 

	def DBsessinfo(self):
			sessinfo = []
			sql_stmt =[('void'), \
(" \
SELECT * FROM \
( \
SELECT \
to_char(a.sid), \
serial#, \
a.inst_id, \
substr(username,1,15)||'..' USERN, \
DECODE(program,null,' ',substr(program,1,15)||'..') prog, \
DECODE(EVENT,null,' ',substr(EVENT,1,40)||'..') ev, \
DECODE(LAST_CALL_ET,null,0,LAST_CALL_ET) duration, \
DECODE(a.SQL_ID,null, \
decode(a.PREV_SQL_ID,null,' ', a.PREV_SQL_ID||'/'||decode(a.PREV_CHILD_NUMBER,null,' ',a.PREV_CHILD_NUMBER)||'*'), \
a.SQL_ID||'/'||to_char(decode(a.SQL_CHILD_NUMBER,null,' ',a.SQL_CHILD_NUMBER))) SQLID_CHN, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.elapsed_time,null,' ',to_char(b.elapsed_time) ) \
ELSE decode(b.elapsed_time,null,'A',to_char(round(b.elapsed_time/b.executions/1000000,2) )) \
END) AVELA, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.ROWS_PROCESSED,null,' ',to_char(b.ROWS_PROCESSED) ) \
ELSE decode(b.ROWS_PROCESSED,null,'P',to_char(round(b.ROWS_PROCESSED/b.executions,2))) \
END) ROWSP, \
decode(b.executions,null,' ',b.executions) EXECS, \
nvl( ( \
SELECT \
(CASE  \
when length(to_char(BYTES)) <= 5 then to_char(BYTES)||'B' \
when length(to_char(BYTES)) > 5 and length(to_char(BYTES)) <= 7 then to_char(round(BYTES/1024,0))||'K' \
when length(to_char(BYTES)) > 7 then to_char(round(BYTES/1024000,0))||'M' \
END ) OPSIZE \
FROM \
( \
SELECT COST,CARDINALITY,BYTES,OPERATION, OBJECT_NAME,OPTIONS \
from gv$sql_plan \
where \
sql_id = a.sql_id \
and CHILD_NUMBER=a.SQL_CHILD_NUMBER \
and inst_id=a.inst_id \
and OPTIONS like '%FULL%' \
and bytes > 0 \
order by bytes desc,CARDINALITY desc,COST desc \
) \
where rownum<=1 \
),' ')  FSOP, \
BLOCKING_INSTANCE,BLOCKING_SESSION, \
DECODE(LOCKWAIT,null,' ',substr(LOCKWAIT,1,8)||'..') LOCKW, \
DECODE(BLOCKING_INSTANCE,null,' ',to_char(BLOCKING_INSTANCE)||'/'||to_char(decode(BLOCKING_SESSION,null,' ',BLOCKING_SESSION))) BLKIS, \
substr(to_char(WAIT_TIME),1,6) WT, \
status, \
substr(state,1,10) STATE, \
substr(wait_class,1,13) WCLASS, \
(SELECT to_char(QCINST_ID)||'/'||to_char(QCSID) FROM GV$PX_SESSION where inst_id=a.inst_id and sid=a.sid )||' ' QCISID, \
a.SQL_ID,CHILD_NUMBER,SQL_FULLTEXT, \
b.PLAN_HASH_VALUE,a.username FUNAME, \
decode(a.program,null,' ',a.program) FPRGNAME,decode(a.machine,null,' ',a.machine) FMACHINE, \
(select 'OOTOP_STATEMENT_ID' from dual) THISSTMT \
from gv$session a, gv$sql b \
where \
a.inst_id=b.inst_id(+) and a.SQL_CHILD_NUMBER=b.CHILD_NUMBER(+) and a.sql_id=b.sql_id(+) \
and a.program not like 'python%' \
and (status='ACTIVE' OR (status <> 'ACTIVE' and a.inst_id||';'||a.sid in (select BLOCKER_INSTANCE_ID||';'||BLOCKER_SID from gv$session_blockers)))  \
and username not in ('SYS','SYSTEM') \
and username is not null \
and b.sql_fulltext not like '%OOTOP_STATEMENT_ID%' \
order by AVELA desc,a.inst_id \
) WHERE ROWNUM <= 7 \
"), \
(" \
SELECT * FROM \
( \
SELECT \
LPAD(' ', (level-1)*2, ' ') ||to_char(sid),serial#,inst_id,USERN,prog,ev,duration,SQLID_CHN,AVELA,ROWSP,EXECS,FSOP, \
BLOCKING_INSTANCE,BLOCKING_SESSION, LOCKW, \
BLKIS,WT,status,STATE,WCLASS,QCISID,SQLID,SQLCH,SQLTEXT,SQLPLAN,FUNAME,FPRGNAME,FMACHINE,THISSTMT \
FROM \
( \
SELECT \
a.sid, \
serial#, \
a.inst_id, \
substr(username,1,15)||'..' USERN, \
DECODE(program,null,' ',substr(program,1,15)||'..') prog, \
DECODE(EVENT,null,' ',substr(EVENT,1,40)||'..') ev, \
DECODE(LAST_CALL_ET,null,0,LAST_CALL_ET) duration, \
DECODE(a.SQL_ID,null, \
decode(a.PREV_SQL_ID,null,' ', a.PREV_SQL_ID||'/'||decode(a.PREV_CHILD_NUMBER,null,' ',a.PREV_CHILD_NUMBER)||'*'), \
a.SQL_ID||'/'||to_char(decode(a.SQL_CHILD_NUMBER,null,' ',a.SQL_CHILD_NUMBER))) SQLID_CHN, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.elapsed_time,null,' ',to_char(b.elapsed_time) ) \
ELSE to_char(round(b.elapsed_time/b.executions/1000000,2) ) \
END) AVELA, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.ROWS_PROCESSED,null,' ',to_char(b.ROWS_PROCESSED) ) \
ELSE to_char(round(b.ROWS_PROCESSED/b.executions,2)) \
END) ROWSP, \
decode(b.executions,null,' ',b.executions) EXECS, \
nvl( ( \
SELECT \
(CASE  \
when length(to_char(BYTES)) <= 5 then to_char(BYTES)||'B' \
when length(to_char(BYTES)) > 5 and length(to_char(BYTES)) <= 7 then to_char(round(BYTES/1024,0))||'K' \
when length(to_char(BYTES)) > 7 then to_char(round(BYTES/1024000,0))||'M' \
END ) OPSIZE \
FROM \
( \
SELECT COST,CARDINALITY,BYTES,OPERATION, OBJECT_NAME,OPTIONS \
from gv$sql_plan \
where \
sql_id = a.sql_id \
and CHILD_NUMBER=a.SQL_CHILD_NUMBER \
and inst_id=a.inst_id \
and OPTIONS like '%FULL%' \
and bytes > 0 \
order by bytes desc,CARDINALITY desc,COST desc \
) \
where rownum<=1 \
),' ')  FSOP, \
BLOCKING_INSTANCE,BLOCKING_SESSION, \
DECODE(LOCKWAIT,null,' ',substr(LOCKWAIT,1,8)||'..') LOCKW, \
DECODE(BLOCKING_INSTANCE,null,' ',to_char(BLOCKING_INSTANCE)||'/'||to_char(decode(BLOCKING_SESSION,null,' ',BLOCKING_SESSION))) BLKIS, \
substr(to_char(WAIT_TIME),1,6) WT, \
status, \
substr(state,1,10) STATE, \
substr(wait_class,1,13) WCLASS, \
(SELECT to_char(QCINST_ID)||'/'||to_char(QCSID) FROM GV$PX_SESSION where inst_id=a.inst_id and sid=a.sid )||' ' QCISID, \
a.SQL_ID SQLID,CHILD_NUMBER SQLCH,SQL_FULLTEXT SQLTEXT,b.PLAN_HASH_VALUE SQLPLAN,a.username FUNAME,  \
decode(a.program,null,' ',a.program) FPRGNAME,decode(a.machine,null,' ',a.machine) FMACHINE, \
(select 'OOTOP_STATEMENT_ID' from dual) THISSTMT \
from gv$session a, gv$sql b \
where \
a.inst_id=b.inst_id(+) and a.SQL_CHILD_NUMBER=b.CHILD_NUMBER(+) and a.sql_id=b.sql_id(+) and \
(status='ACTIVE' OR (status <> 'ACTIVE' and a.inst_id||';'||a.sid in (select BLOCKER_INSTANCE_ID||';'||BLOCKER_SID from gv$session_blockers))) and \
username is not null \
and username not in ('SYS','SYSTEM') \
and program not like 'python%' \
and b.sql_fulltext not like '%OOTOP_STATEMENT_ID%' \
order by LAST_CALL_ET desc,a.inst_id \
) \
CONNECT BY PRIOR sid=BLOCKING_SESSION and inst_id=decode(BLOCKING_INSTANCE,null,inst_id,BLOCKING_INSTANCE) \
START WITH BLOCKING_SESSION IS NULL \
) WHERE ROWNUM <= 7 \
"), \
#
(" \
SELECT * FROM \
( \
SELECT \
to_char(a.sid), \
serial#, \
a.inst_id, \
substr(username,1,15)||'..' USERN, \
DECODE(program,null,' ',substr(program,1,15)||'..') prog, \
DECODE(EVENT,null,' ',substr(EVENT,1,40)||'..') ev, \
DECODE(LAST_CALL_ET,null,0,LAST_CALL_ET) duration, \
DECODE(a.SQL_ID,null, \
decode(a.PREV_SQL_ID,null,' ', a.PREV_SQL_ID||'/'||decode(a.PREV_CHILD_NUMBER,null,' ',a.PREV_CHILD_NUMBER)||'*'), \
a.SQL_ID||'/'||to_char(decode(a.SQL_CHILD_NUMBER,null,' ',a.SQL_CHILD_NUMBER))) SQLID_CHN, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.elapsed_time,null,' ',to_char(b.elapsed_time) ) \
ELSE decode(b.elapsed_time,null,'A',to_char(round(b.elapsed_time/b.executions/1000000,2) )) \
END) AVELA, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.ROWS_PROCESSED,null,' ',to_char(b.ROWS_PROCESSED) ) \
ELSE decode(b.ROWS_PROCESSED,null,'P',to_char(round(b.ROWS_PROCESSED/b.executions,2))) \
END) ROWSP, \
decode(b.executions,null,' ',b.executions) EXECS, \
nvl( ( \
SELECT \
(CASE  \
when length(to_char(BYTES)) <= 5 then to_char(BYTES)||'B' \
when length(to_char(BYTES)) > 5 and length(to_char(BYTES)) <= 7 then to_char(round(BYTES/1024,0))||'K' \
when length(to_char(BYTES)) > 7 then to_char(round(BYTES/1024000,0))||'M' \
END ) OPSIZE \
FROM \
( \
SELECT COST,CARDINALITY,BYTES,OPERATION, OBJECT_NAME,OPTIONS \
from gv$sql_plan \
where \
sql_id = a.sql_id \
and CHILD_NUMBER=a.SQL_CHILD_NUMBER \
and inst_id=a.inst_id \
and OPTIONS like '%FULL%' \
and bytes > 0 \
order by bytes desc,CARDINALITY desc,COST desc \
) \
where rownum<=1 \
),' ')  FSOP, \
BLOCKING_INSTANCE,BLOCKING_SESSION, \
DECODE(LOCKWAIT,null,' ',substr(LOCKWAIT,1,8)||'..') LOCKW, \
DECODE(BLOCKING_INSTANCE,null,' ',to_char(BLOCKING_INSTANCE)||'/'||to_char(decode(BLOCKING_SESSION,null,' ',BLOCKING_SESSION))) BLKIS, \
substr(to_char(WAIT_TIME),1,6) WT, \
status, \
substr(state,1,10) STATE, \
substr(wait_class,1,13) WCLASS, \
(SELECT to_char(QCINST_ID)||'/'||to_char(QCSID) FROM GV$PX_SESSION where inst_id=a.inst_id and sid=a.sid )||' ' QCISID, \
a.SQL_ID,CHILD_NUMBER,SQL_FULLTEXT,PLAN_HASH_VALUE,a.username FUNAME, \
decode(a.program,null,' ',a.program) FPRGNAME,decode(a.machine,null,' ',a.machine) FMACHINE, \
(select 'OOTOP_STATEMENT_ID' from dual) THISSTMT \
from gv$session a, gv$sql b \
where \
a.inst_id=b.inst_id(+) and a.SQL_CHILD_NUMBER=b.CHILD_NUMBER(+) and a.sql_id=b.sql_id(+) \
and program not like 'python%' \
and b.sql_fulltext not like '%OOTOP_STATEMENT_ID%' \
and (status='ACTIVE' OR (status <> 'ACTIVE' and a.inst_id||';'||a.sid in (select BLOCKER_INSTANCE_ID||';'||BLOCKER_SID from gv$session_blockers)))  \
and username not in ('SYS','SYSTEM') \
and username is not null \
order by EXECS desc,a.inst_id \
) WHERE ROWNUM <= 7 \
"), \
#
(" \
SELECT * FROM \
( \
SELECT \
to_char(a.sid), \
serial#, \
a.inst_id, \
substr(username,1,15)||'..' USERN, \
DECODE(program,null,' ',substr(program,1,15)||'..') prog, \
DECODE(EVENT,null,' ',substr(EVENT,1,40)||'..') ev, \
DECODE(LAST_CALL_ET,null,0,LAST_CALL_ET) duration, \
DECODE(a.SQL_ID,null, \
decode(a.PREV_SQL_ID,null,' ', a.PREV_SQL_ID||'/'||decode(a.PREV_CHILD_NUMBER,null,' ',a.PREV_CHILD_NUMBER)||'*'), \
a.SQL_ID||'/'||to_char(decode(a.SQL_CHILD_NUMBER,null,' ',a.SQL_CHILD_NUMBER))) SQLID_CHN, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.elapsed_time,null,' ',to_char(b.elapsed_time) ) \
ELSE decode(b.elapsed_time,null,'A',to_char(round(b.elapsed_time/b.executions/1000000,2) )) \
END) AVELA, \
(CASE \
when b.executions is null or b.executions = 0 then decode(b.ROWS_PROCESSED,null,' ',to_char(b.ROWS_PROCESSED) ) \
ELSE decode(b.ROWS_PROCESSED,null,'P',to_char(round(b.ROWS_PROCESSED/b.executions,2))) \
END) ROWSP, \
decode(b.executions,null,' ',b.executions) EXECS, \
nvl( ( \
SELECT \
(CASE  \
when length(to_char(BYTES)) <= 5 then to_char(BYTES)||'B' \
when length(to_char(BYTES)) > 5 and length(to_char(BYTES)) <= 7 then to_char(round(BYTES/1024,0))||'K' \
when length(to_char(BYTES)) > 7 then to_char(round(BYTES/1024000,0))||'M' \
END ) OPSIZE \
FROM \
( \
SELECT COST,CARDINALITY,BYTES,OPERATION, OBJECT_NAME,OPTIONS \
from gv$sql_plan \
where \
sql_id = a.sql_id \
and CHILD_NUMBER=a.SQL_CHILD_NUMBER \
and inst_id=a.inst_id \
and OPTIONS like '%FULL%' \
and bytes > 0 \
order by bytes desc,CARDINALITY desc,COST desc \
) \
where rownum<=1 \
),' ')  FSOP, \
BLOCKING_INSTANCE,BLOCKING_SESSION, \
DECODE(LOCKWAIT,null,' ',substr(LOCKWAIT,1,8)||'..') LOCKW, \
DECODE(BLOCKING_INSTANCE,null,' ',to_char(BLOCKING_INSTANCE)||'/'||to_char(decode(BLOCKING_SESSION,null,' ',BLOCKING_SESSION))) BLKIS, \
substr(to_char(WAIT_TIME),1,6) WT, \
status, \
substr(state,1,10) STATE, \
substr(wait_class,1,13) WCLASS, \
(SELECT to_char(QCINST_ID)||'/'||to_char(QCSID) FROM GV$PX_SESSION where inst_id=a.inst_id and sid=a.sid )||' ' QCISID, \
a.SQL_ID,CHILD_NUMBER,SQL_FULLTEXT,PLAN_HASH_VALUE,a.username FUNAME, \
decode(a.program,null,' ',a.program) FPRGNAME,decode(a.machine,null,' ',a.machine) FMACHINE, \
(select 'OOTOP_STATEMENT_ID' from dual) THISSTMT \
from gv$session a, gv$sql b \
where \
a.inst_id=b.inst_id(+) and a.SQL_CHILD_NUMBER=b.CHILD_NUMBER(+) and a.sql_id=b.sql_id(+) \
and program not like 'python%' \
and b.sql_fulltext not like '%OOTOP_STATEMENT_ID%' \
and (status='ACTIVE' OR (status <> 'ACTIVE' and a.inst_id||';'||a.sid in (select BLOCKER_INSTANCE_ID||';'||BLOCKER_SID from gv$session_blockers)))  \
and username not in ('SYS','SYSTEM') \
and username is not null \
order by ROWSP desc,a.inst_id \
) WHERE ROWNUM <= 7 \
") \
]

			trycnt = 1
		        while trycnt<=self.retryconnect: 
				try:
					self.Vsessdata_rows = []

					sessinfo = self.DBGetCursorData(sql_stmt[self.DBsessionOrder], self.ID_PAD_SESS)

					if sessinfo == -1: #query error
						sessinfo=[('DB ERROR',0,0,' ',' ',' ',0,' ',0,0,0,' ',' ',' ',' ',' ',' ',' ',' ',' ',' ', 0, ' ', 0, ' ', ' ', ' ', ' ', ' ')]
						self.Vsessdata_rows = sessinfo
						self.Vsessdata_srows = self.makelineshow(sessinfo,self.Vsessdata_struct,'sessdata')
						trycnt=2 # exit try
					else:
						self.Vsessdata_rows = sessinfo

						self.Vsessdata_srows = self.makelineshow(sessinfo,self.Vsessdata_struct,'sessdata')

						break
				except Exception as err:
					self.WinPrintError("DBsessinfo exception:  "+str(err) )

                	return(sessinfo) 

	def DBsessplan(self,inst_id,sqlid,childn,sqlplanhash):
			planinfo = []
			params=[]
			params.append("'"+sqlid+"'")
			params.append(sqlplanhash)
			trycnt = 1
                        while trycnt<=self.retryconnect:  
				try:
					if childn >=0:
						sql="select PLAN_TABLE_OUTPUT from table(dbms_xplan.DISPLAY('gv$sql_plan_statistics_all', NULL, 'ALL',' inst_id="+str(inst_id)+" and sql_id='''||'"+str(sqlid)+"'||''' and child_number="+str(childn)+"'))"
					else:
						sql="select PLAN_TABLE_OUTPUT from table(dbms_xplan.DISPLAY_AWR('"+str(sqlid)+"',"+str(sqlplanhash)+",format=>'ALL') )"

					planinfo = self.DBGetCursorData(sql, -1)

					if planinfo == -1: # query error
						self.Vsessdata_sql_plan = planinfo
						trycnt = 2 # exit try
					else:
						self.Vsessdata_sql_plan = planinfo
						break
				except Exception as err:
					self.WinPrintError("DBsessplan exception: "+str(err) )

                	return(planinfo) 

	def DBtbsinfo(self):
			tbsinfo = []
                        trycnt = 1
                        while trycnt<=self.retryconnect:
                                try:
					if self.OracleVersion[:2] == '12':   # select for 12c version
						sql = "\
SELECT TN,TST, TSZ,TUSD \
FROM ( \
SELECT a.tablespace_name TN ,b.status TST, \
round((a.tablespace_size*b.BLOCK_SIZE)/(1024*1024),0) TSZ, \
round(a.used_percent,2) TUSD  \
from dba_tablespace_usage_metrics a, dba_tablespaces b where a.tablespace_name=b.tablespace_name and b.status='ONLINE'  \
order by USED_PERCENT desc \
) WHERE ROWNUM <= 5 \
"

                        		else:  # select for other oracle version
						sql = "\
SELECT  TN,ONL,TSS,TPU \
FROM ( \
select a.tablespace_name TN, \
       'online' ONL, \
       to_char(round(a.bytes_alloc/(1024*1024),0)) TSS, \
       to_char(round((nvl(b.tot_used,0)/a.bytes_alloc)*100,3)) TPU \
from ( select tablespace_name, \
       sum(decode(autoextensible,'NO',bytes,'YES',maxbytes)) bytes_alloc \
       from dba_data_files where online_status in ('SYSTEM','ONLINE') \
       group by tablespace_name ) a, \
     ( select tablespace_name, sum(bytes) tot_used \
       from dba_segments \
       group by tablespace_name ) b \
where a.tablespace_name = b.tablespace_name (+) \
and   a.tablespace_name not in (select distinct tablespace_name from dba_temp_files) \
order by TPU desc,TSS desc \
) WHERE ROWNUM<=5 \
"
   					tbsinfo=self.DBGetCursorData(sql, self.ID_PAD_TBS)

					if tbsinfo == -1:  # db error
						tbsinfo=[('DB ERROR',' ',0,0)]
						self.Vtbsdata_rows = tbsinfo
						self.Vtbsdata_srows = self.makelineshow(tbsinfo,self.Vtbsdata_struct,'tbs')
						self.WinCprint(2,1, '> TBS err <' )
						trycnt = 2 # exit try
					else:
						self.Vtbsdata_rows = tbsinfo
						self.Vtbsdata_srows = self.makelineshow(tbsinfo,self.Vtbsdata_struct,'tbs')
						#self.WinCprint(2,1, '>' + str(len(tbsinfo)) + '< ' )
						break
				except Exception as err:
						self.WinPrintError("DBtbsinfo exception:      "+str(err) )

                	return(tbsinfo) 

	def DBtopsqlinfo(self):
                        topsqlinfo = []
                        trycnt = 1
                        while trycnt<=self.retryconnect:
                                try:
                                        sql = "\
SELECT INSTID,SCHEMA,SQLID,PLANHASH,VERSIONS,PROFILE,CPUELAX,AVGELAX,AVGEXECS,AVGROWSX, \
decode(IOWms,'0','<0.04',IOWms) IOW, \
decode(CLWms,'0','<0.04',CLWms) CLW, \
decode(APWms,'0','<0.04',APWms) APW, \
decode(CCWms,'0','<0.04',CCWms) CCW, \
PQUERY, \
FSOP, \
snap \
FROM ( \
SELECT \
to_char(a.INSTANCE_NUMBER) INSTID, \
a.PARSING_SCHEMA_NAME SCHEMA, \
a.SQL_ID SQLID, \
a.PLAN_HASH_VALUE PLANHASH, \
a.VERSION_COUNT VERSIONS, \
decode(a.SQL_PROFILE,NULL,'-',substr(a.SQL_PROFILE,1,25)) PROFILE, \
(CASE \
when a.EXECUTIONS_DELTA > 0 then round((a.CPU_TIME_DELTA/1000000)/a.EXECUTIONS_DELTA,1) \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then round(a.CPU_TIME_DELTA/1000000,1) \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then round(a.CPU_TIME_DELTA/1000000/a.PX_SERVERS_EXECS_DELTA,1) \
END ) CPUELAX, \
(CASE \
when a.EXECUTIONS_DELTA > 0 then round((a.ELAPSED_TIME_DELTA/1000000)/a.EXECUTIONS_DELTA,2) \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then round(a.ELAPSED_TIME_DELTA/1000000,2) \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then round(a.ELAPSED_TIME_DELTA/1000000/a.PX_SERVERS_EXECS_DELTA,2) \
END ) AVGELAX, \
(CASE \
when a.EXECUTIONS_DELTA > 0 then a.EXECUTIONS_DELTA \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then a.PX_SERVERS_EXECS_DELTA \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then 0 \
END ) AVGEXECS, \
(CASE \
when a.EXECUTIONS_DELTA > 0 then round(a.ROWS_PROCESSED_DELTA/a.EXECUTIONS_DELTA,1) \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then a.ROWS_PROCESSED_DELTA \
when a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then round(a.ROWS_PROCESSED_DELTA/a.PX_SERVERS_EXECS_DELTA,2) \
END ) AVGROWSX, \
(CASE \
when a.IOWAIT_DELTA = 0 then ' ' \
when a.IOWAIT_DELTA > 0 and a.EXECUTIONS_DELTA > 0 then to_char(round(a.IOWAIT_DELTA/a.EXECUTIONS_DELTA/1000,1)) \
when a.IOWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then to_char(round(a.IOWAIT_DELTA/a.PX_SERVERS_EXECS_DELTA/1000,1)) \
when a.IOWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then to_char(round(a.IOWAIT_DELTA/1000,1)) \
else ' ' \
END ) IOWms, \
(CASE \
when a.CLWAIT_DELTA = 0 then ' ' \
when a.CLWAIT_DELTA > 0 and a.EXECUTIONS_DELTA > 0 then to_char(round(a.CLWAIT_DELTA/a.EXECUTIONS_DELTA/1000,1)) \
when a.CLWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then to_char(round(a.CLWAIT_DELTA/a.PX_SERVERS_EXECS_DELTA/1000,1)) \
when a.CLWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then to_char(round(a.CLWAIT_DELTA/1000,1)) \
else ' ' \
END ) CLWms, \
(CASE \
when a.APWAIT_DELTA = 0 then ' ' \
when a.APWAIT_DELTA > 0 and a.EXECUTIONS_DELTA > 0 then to_char(round(a.APWAIT_DELTA/a.EXECUTIONS_DELTA/1000,1)) \
when a.APWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then to_char(round(a.APWAIT_DELTA/a.PX_SERVERS_EXECS_DELTA/1000,1)) \
when a.APWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then to_char(round(a.APWAIT_DELTA/1000,1)) \
else ' ' \
END ) APWms, \
(CASE \
when a.CCWAIT_DELTA = 0 then ' ' \
when a.CCWAIT_DELTA > 0 and a.EXECUTIONS_DELTA > 0 then to_char(round(a.CCWAIT_DELTA/a.EXECUTIONS_DELTA/1000,1)) \
when a.CCWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA > 0 then to_char(round(a.CCWAIT_DELTA/a.PX_SERVERS_EXECS_DELTA/1000,1)) \
when a.CCWAIT_DELTA > 0 and a.EXECUTIONS_DELTA = 0 and a.PX_SERVERS_EXECS_DELTA = 0 then to_char(round(a.CCWAIT_DELTA/1000,1)) \
else ' ' \
END ) CCWms, \
(CASE \
when a.PX_SERVERS_EXECS_DELTA > 0 then 'yes' \
ELSE ' ' \
END) PQUERY, \
nvl( ( \
SELECT \
(CASE  \
when length(to_char(BYTES)) <= 5 then to_char(BYTES)||'B' \
when length(to_char(BYTES)) > 5 and length(to_char(BYTES)) <= 7 then to_char(round(BYTES/1024,0))||'K' \
when length(to_char(BYTES)) > 7 then to_char(round(BYTES/1024000,0))||'M' \
END ) OPSIZE \
FROM \
( \
SELECT COST,CARDINALITY,BYTES,OPERATION, OBJECT_NAME,OPTIONS \
from DBA_HIST_SQL_PLAN \
where \
sql_id = a.sql_id \
and plan_hash_value = a.plan_hash_value \
and OPTIONS like '%FULL%' \
and bytes > 0 \
order by bytes desc,CARDINALITY desc,COST desc \
) \
where rownum<=1 \
),' ')  FSOP, \
b.snap_id snap \
FROM \
DBA_HIST_SQLSTAT a, DBA_HIST_SNAPSHOT b \
WHERE \
a.SNAP_ID = b.SNAP_ID \
AND a.INSTANCE_NUMBER = b.INSTANCE_NUMBER \
AND a.PARSING_SCHEMA_NAME not in ('SYS','SYSTEM') \
AND a.DBID = b.DBID AND a.DBID = (select DBID from v$database) \
AND b.END_INTERVAL_TIME =  (select max(END_INTERVAL_TIME) from DBA_HIST_SNAPSHOT) \
ORDER BY AVGELAX desc,a.INSTANCE_NUMBER \
) WHERE ROWNUM<=5 \
"

                                        topsqlinfo=self.DBGetCursorData(sql, self.ID_PAD_TOPSQL)

                                        if topsqlinfo == -1:  # db error
                                                topsqlinfo = [('DB ERROR',' ',' ',0,0,' ',0,0,0,0,0,0,0,0,' ',' ',' ')]
                                                self.Vtopsql_rows = topsqlinfo
                                                self.Vtopsql_srows = self.makelineshow(topsqlinfo,self.Vtopsql_struct,'topsql')
                                                trycnt = 2 # exit try
                                        else:
                                                self.Vtopsql_rows = topsqlinfo
                                                self.Vtopsql_srows = self.makelineshow(topsqlinfo,self.Vtopsql_struct,'topsql')
                                                break
                                except Exception as err:
                                                self.WinPrintError("DBtopsqlinfo exception:      "+str(err) )

                        return(topsqlinfo)

