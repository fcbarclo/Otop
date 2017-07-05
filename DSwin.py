#screenshow class

import curses
import threading
import time,datetime
from DSdef import DSdef
from DSaccess import DSaccess

class DSwin(DSdef,DSaccess):

        def __init__( self, logininfo):

		# lock definition
		self.locksessth = threading.Lock()
		self.lockdbconn = threading.Lock()
		self.lockvideo = threading.Lock()

		# init id thread
		self.idthloop = 0
		self.idthconn = 0
		self.idthdb = 0
		self.idthinst = 0
		self.idthtbs = 0
		self.idthtopsql = 0
		self.idthsess = 0

		self.ScreenMinY = 39   # min screen y size - reduced info
		self.ScreenMinX = 174  # min screen x size - reduced info

		self.ScreenFullY = 39  # min screen y size for full info
		self.ScreenFullX = 226  # min screen x size for full info

		self.ScreenFullSize = 0     # full screen on (1) or off (0)

		self.VScrStatus = self.WinCinitScr()

		if self.VScrStatus < 0:  # error initializing curses
      			curses.endwin()
			self.screrrmsg="INIT SCREEN ERROR:  "
			actsize=self.scrsize
			if self.VScrStatus == -2:	# screen size error
				self.screrrmsg += "(actual size/required size) Y=("+str(actsize[0])+"/"+str(self.ScreenMinY)+")  X=("+str(actsize[1])+"/"+str(self.ScreenMinX)+") - Full size requires: ("+str(self.ScreenFullY)+","+str(self.ScreenFullX)+")"
			else: # curses error
				self.screrrmsg += "generic error"
		else:

			self.Xpos_start_menu = 85
			self.Xpos_start_submenu = 85

	  		# default box active	
			self.winConnInfoactive = 0;
			self.winDbactive = 0;
			self.winInstactive = 0;    
			self.winSessactive = 1;
			self.winTbsactive = 0;
			self.winTopSqlactive = 0

			# flag for track fsop to file
			self.trackfsop = 0
			self.trackfsopminsize = 10000   # minimum size in bytes to trigger capture FSOP
			self.lastfilenametrackfsop = ""

			self.MAX_SESS_ROWS = 50  # max number of windowd sessions

			# Otop start time
			self.startTW = round(time.time(),2)

			self.padrefreshcoord = [] #
			self.thConfig = []   # active thread list 

			# sleep info in seconds
                	self.SLEEP_CI_DATA = 30
                	self.SLEEP_DB_DATA = 30
                	self.SLEEP_INSTANCE_DATA = 2
                	self.SLEEP_SESS_DATA = 2
                	self.SLEEP_TBS_DATA = 3
                	self.SLEEP_TOPSQL_DATA = 30
                	self.SLEEP_SESS_DATA = 2
			self.ENTERING_SLEEP_TIME = .30

			# box data-structure
			conninfo_lines = 1
			conninfo_Ypos = 2
			dbdata_lines = 1
			dbdata_Ypos = conninfo_Ypos+conninfo_lines+2

			instdata_lines = 4

			tbsdata_lines = 5
			tbsdata_Ypos = dbdata_Ypos

			topsql_lines = 5
			topsql_Xpos = 1

			sessdata_lines = 7
			
			instdata_Ypos = dbdata_Ypos+tbsdata_lines+2
			topsql_Ypos = instdata_Ypos + instdata_lines + 3
			sessdata_Ypos = topsql_Ypos+topsql_lines+3

			#
			# WinOtopData = (func description,y screen position, x screen position, num of lines, thread sleep time, led descriptor)
			#
                	self.WinOtopData = [ \
('conninfo',conninfo_Ypos,1,conninfo_lines,self.SLEEP_CI_DATA,'C'), \
('dbdata',dbdata_Ypos,1,dbdata_lines,self.SLEEP_DB_DATA,'D'), \
('tbsdata',dbdata_Ypos,120,tbsdata_lines,self.SLEEP_TBS_DATA,'T'), \
('instdata',instdata_Ypos,1,instdata_lines,self.SLEEP_INSTANCE_DATA,'I'), \
('topsql',topsql_Ypos,topsql_Xpos,topsql_lines,self.SLEEP_TOPSQL_DATA,'5'), \
('sessdata',sessdata_Ypos,1,sessdata_lines,self.SLEEP_SESS_DATA,'S') \
]

			# id box 
			self.ID_PAD_CI = [i for i,elem in enumerate(self.WinOtopData) if elem[0]=='conninfo'][0]
			self.ID_PAD_DB = [i for i,elem in enumerate(self.WinOtopData) if elem[0]=='dbdata'][0]
			self.ID_PAD_INST = [i for i,elem in enumerate(self.WinOtopData) if elem[0]=='instdata'][0]
			self.ID_PAD_TBS = [i for i,elem in enumerate(self.WinOtopData) if elem[0]=='tbsdata'][0]
			self.ID_PAD_TOPSQL = [i for i,elem in enumerate(self.WinOtopData) if elem[0]=='topsql'][0]
			self.ID_PAD_SESS = [i for i,elem in enumerate(self.WinOtopData) if elem[0]=='sessdata'][0]


			# led action
			self.TH_SLEEPING = 0
			self.TH_RUNNING = 1
			self.TH_REQUEST_VIDEO_LOCK = 2
			self.TH_REQUEST_DB_CONN = 3
			self.TH_ENTERING_SLEEP = 4
			self.TH_DB_RECONNECTING = 5
			self.TH_SQL_RUNNING = 11
			self.TH_ROW_FETCHING = 12
			self.TH_SESS_REQUEST_LOCK = 13
			self.TH_SESS_TRACK_FSOP = 14

			self.PRG_EXIT = 0
			self.PRG_EXIT_SCR_SIZE = 0
			self.statusprint = 0
		
			self.lastfilenamespool=""

			# grid led position
			self.Ypos_start_sensor = 1
			self.Xpos_start_sensor = self.scrsize[1]-14
			self.winledthread = self.Winthset()

			# init other classes
			DSdef.__init__( self)
			DSaccess.__init__( self,logininfo)

	########################
	## WIN-CURSES METHODS ##
	########################

       	def WinCinitScr(self):
		# init curses
                try:
			self.VWscreen = curses.initscr()

			minY = self.ScreenMinY
			minX = self.ScreenMinX

			bestY = self.ScreenFullY
			bestX = self.ScreenFullX

			curses.noecho()
			curses.cbreak()
			curses.start_color()
			curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_CYAN)
			curses.init_pair(2,curses.COLOR_WHITE, curses.COLOR_BLUE)
			curses.init_pair(3,curses.COLOR_WHITE, curses.COLOR_RED)
			curses.init_pair(4,curses.COLOR_WHITE, curses.COLOR_MAGENTA)
			curses.init_pair(5,curses.COLOR_WHITE, curses.COLOR_YELLOW)
			curses.init_pair(6,curses.COLOR_BLACK, curses.COLOR_BLACK)
			curses.init_pair(7,curses.COLOR_BLACK, curses.COLOR_GREEN)
			curses.init_pair(8,curses.COLOR_BLACK, curses.COLOR_RED)
			curses.init_pair(9,curses.COLOR_CYAN, curses.COLOR_BLACK)
			curses.init_pair(10,curses.COLOR_RED, curses.COLOR_BLACK)
			curses.init_pair(11,curses.COLOR_BLUE, curses.COLOR_BLACK)
			curses.init_pair(12,curses.COLOR_GREEN, curses.COLOR_BLACK)
			curses.init_pair(13,curses.COLOR_YELLOW, curses.COLOR_BLACK)
			curses.init_pair(14,curses.COLOR_MAGENTA, curses.COLOR_BLACK)
			curses.init_pair(15,curses.COLOR_WHITE, curses.COLOR_BLACK)
			curses.init_pair(16,curses.COLOR_BLACK, curses.COLOR_YELLOW)
			curses.init_pair(17,curses.COLOR_YELLOW, curses.COLOR_RED)

			self.BLACKONCYAN = curses.color_pair(1)
			self.WHITEONBLUE = curses.color_pair(2)
			self.WHITEONRED = curses.color_pair(3)
			self.WHITEONMAGENTA = curses.color_pair(4)
			self.WHITEONYELLOW = curses.color_pair(5)
			self.BLACKONBLACK = curses.color_pair(6)
			self.BLACKONGREEN = curses.color_pair(7)
			self.BLACKONRED = curses.color_pair(8)
			self.CYANONBLACK = curses.color_pair(9)
			self.REDONBLACK = curses.color_pair(10)
			self.BLUEONBLACK = curses.color_pair(11)
			self.GREENONBLACK = curses.color_pair(12)
			self.YELLOWONBLACK = curses.color_pair(13)
			self.MAGENTAONBLACK = curses.color_pair(14)
			self.WHITEONBLACK = curses.color_pair(15)
			self.BLACKONYELLOW = curses.color_pair(16)
			self.YELLOWONRED = curses.color_pair(17)

			curses.curs_set( 0 )

			self.VWscreen.nodelay(1)
			self.VWscreen.keypad(1)

			self.VhighlightText = curses.color_pair( 1 )
			self.VhighlightText_menu = curses.color_pair( 2 )
			self.VnormalText = curses.A_NORMAL
			self.VWscreen.border( 0 )

			SSize=self.VWscreen.getmaxyx()
			self.scrsize = SSize

			if (SSize[0]<minY) | (SSize[1]<minX):
				scrok=-2
                        else:
				if (SSize[0]>= bestY) and (SSize[1]>=bestX):
					self.ScreenFullSize = 1
				scrok=1
				self.VWscreen.refresh()
		except:
			scrok=-1

		return(scrok)


	def WinCrestoreScr(self):
		if self.VScrStatus == 1:
                	self.VWscreen.keypad(0)

		curses.nocbreak()
		curses.echo()
      		curses.endwin()

	def End(self):
			try:
				self.DBclose()
			except:
				pass
			finally:
				self.WinCrestoreScr()
	
	def WinCprint(self,y,x,msg,color=curses.A_NORMAL):
		self.lockvideo.acquire()
		try:
			#self.VWscreen.addstr(y,x,msg[:msg.find('\n')],color)
			self.VWscreen.addstr(y,x,msg,color)
			self.VWscreen.refresh()
		except:
			pass
                self.lockvideo.release()

	def WinPrintOtopVersion(self):
		try:
			versionmsg = "Otop 0.5.5 ["+str(self.scrsize[0] )+","+str(self.scrsize[1] )+"]"
			ypos = self.scrsize[0]-2
			xpos = self.scrsize[1]-len(versionmsg)-2

			self.winotopversion = curses.newwin(1,len(versionmsg)+1,ypos,xpos)
			self.winotopversion.addstr(0,0,versionmsg,self.REDONBLACK)
			self.winotopversion.refresh()
		except:
			winotopversion = -1
			self.WinPrintError("WinPrintOtopVersion Error:"+str(err) )

	def WinCgetch(self):
		kp = -1
		while kp==-1:
			kp = self.VWscreen.getch()	
			ScrResized = curses.is_term_resized(self.scrsize[0],self.scrsize[1])
			if ScrResized:
				try:
					y,x = self.VWscreen.getmaxyx()

                       			minY = self.ScreenMinY
                       			minX = self.ScreenMinX
                       			bestY = self.ScreenFullY
                       			bestX = self.ScreenFullX

                        		if (y<minY) | (x<minX): # check resized  size
						self.VWscreen.clear()
						self.VWscreen.refresh()
						curses.resizeterm(self.scrsize[0],self.scrsize[1]) # reset to original size
						self.VWscreen.clear()
						self.VWscreen.refresh()

						curses.flash()
						self.WinPrintError("Screen size not valid.  ")
						time.sleep(1)
						self.PRG_EXIT_SCR_SIZE = 1
                				curses.ungetch(27) # push ESC key to main loop: exit from program
                        		else:   # set new size
                                		if (y>= bestY) and (x>=bestX):
                                        		self.ScreenFullSize = 1
						else:
                                        		self.ScreenFullSize = 0
					
						self.VWscreen.clear()
						curses.resizeterm(y, x)

						self.scrsize = []
						self.scrsize = (y,x)

						self.WinRefreshScr()

				except Exception as err:
					self.WinPrintError("Error resizing screen... "+str(err)+ "       " )
		return(kp)

	def WinRefreshScr(self):
		self.VWscreen.border( 0 )
		self.VWscreen.refresh()
		self.WinPrintOtopVersion()

		self.Xpos_start_sensor = self.scrsize[1]-14
		self.winledthread = self.Winthset()

		self.WinBanner()

		self.Vconndata_head = self.makeheadshow(self.Vconndata_struct)
		self.WinConnInfo()

		self.Vdbdata_head = self.makeheadshow(self.Vdbdata_struct)
		self.Windb()

		self.Vinstdata_head = self.makeheadshow(self.Vinstdata_struct)
                self.Wininst()
		
		self.Vtbsdata_head = self.makeheadshow(self.Vtbsdata_struct)
		self.Wintbs()

		self.Vtopsql_head = self.makeheadshow(self.Vtopsql_struct)
                self.Wintopsql()

		self.Vsessdata_head = self.makeheadshow(self.Vsessdata_struct)
                self.Winsess()

                self.WinShowMenu()
                self.WinShowSubMenu()

	def WinCheckThreadAlive(self, idthread):
		if idthread == 0:
			result = 0
		else:
			result = idthread.is_alive()

		return(result)

	def WinBanner(self):
		try:
			banner = self.DBbanner()
			self.winbanner = curses.newwin(1,len(banner)+1,1,2)
			self.winbanner.addstr(0,0,banner,self.REDONBLACK)
			self.winbanner.refresh()
		except Exception as err:
			winb = -1
			self.WinPrintError("WinBanner Error:"+str(err) )

	def WinKeyLoop(self):
		try:
			self.idthloop = threading.Thread(target=self._WinKeyLoopTH,name='keyloopTH')
			self.idthloop.setDaemon(True)
		except Exception as err:
			self.WinPrintError("WinKeyLoop thrd Error:"+str(err) )

	def WinConnInfo(self):
                y = self.WinOtopData[self.ID_PAD_CI][1]
                x = self.WinOtopData[self.ID_PAD_CI][2]
                nlines = self.WinOtopData[self.ID_PAD_CI][3]
                hsize = len(self.Vconndata_head)

		Ltmp=(self.ID_PAD_CI,y,x,nlines,hsize)
		self.padrefreshcoord.append(Ltmp)

		try:
                        self.connIpad = curses.newpad(y+nlines+3,x+hsize+2)
                        self.connIwinbox = curses.newwin( y+nlines+2, hsize+3, y, x)
		except Exception as err:
			self.connIpad = -1
			self.WinPrintError("WinConnInfo curses Error:"+str(err) )
		finally:
                        try:
				if not self.WinCheckThreadAlive(self.idthconn):
					self.idthconn = threading.Thread(target=self._WinconninfoshowTH,name='conninfoshowTH')
					self.idthconn.setDaemon(True)
					self.thConfig.append((self.ID_PAD_CI,1))
				else:
                                        self.lockvideo.acquire()
                                        self.connIpad.addstr(1,1,self.Vconndata_head,self.CYANONBLACK)
                                        self.connIpad.addstr(2,2,"waiting refresh... ",self.GREENONBLACK)
                                        self.connIpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        self.lockvideo.release()

                        except Exception as err:
                                self.connIpad = -10
				self.WinPrintError("WinConnInfo thrd Error:"+str(err) )

        def Windb(self):
                y = self.WinOtopData[self.ID_PAD_DB][1]
                x = self.WinOtopData[self.ID_PAD_DB][2]
                nlines = self.WinOtopData[self.ID_PAD_DB][3]
                hsize = len(self.Vdbdata_head)

		Ltmp=(self.ID_PAD_DB,y,x,nlines,hsize)
		self.padrefreshcoord.append(Ltmp)

                try:
                        self.dbpad = curses.newpad(y+nlines+3,x+hsize+2)
                        self.dbwinbox = curses.newwin( y+nlines+2, hsize+3, y, x)
                except Exception as err:
                        self.dbpad =-1
			self.WinPrintError("Windb curses Error:"+str(err) )
                finally:
                        try:
				if not self.WinCheckThreadAlive(self.idthdb):
					self.idthdb = threading.Thread(target=self._WindbshowTH,name='dbshowTH')
					self.idthdb.setDaemon(True)
					self.thConfig.append((self.ID_PAD_DB,1))
				else:
                                        self.lockvideo.acquire()
                                	self.dbpad.addstr(1,1,self.Vdbdata_head,self.CYANONBLACK)
                                        self.dbpad.addstr(2,2,"waiting refresh... ",self.GREENONBLACK)
                                        self.dbpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        self.lockvideo.release()

                        except Exception as err:
                                self.dbpad =-10
				self.WinPrintError("Windb thrd Error:"+str(err) )

 	def Wininst(self):
                y = self.WinOtopData[self.ID_PAD_INST][1]
                x = self.WinOtopData[self.ID_PAD_INST][2]
                nlines = self.WinOtopData[self.ID_PAD_INST][3]
                hsize = len(self.Vinstdata_head)
		self.instdata_head = 'Instance info'

		Ltmp=(self.ID_PAD_INST,y,x,nlines,hsize)
		self.padrefreshcoord.append(Ltmp)

                try:
                        self.instpad = curses.newpad(y+nlines+3,x+hsize+2)
                        self.instwinbox = curses.newwin( nlines+3, hsize+3, y, x)
                except Exception as err:
                        self.instpad =-1
			self.WinPrintError("Wininst curses Error:"+str(err) )
                finally:
                        try:
				if not self.WinCheckThreadAlive(self.idthinst):
					self.idthinst = threading.Thread(target=self._WininstshowTH,name='instshowTH')
					self.idthinst.setDaemon(True)
					self.thConfig.append((self.ID_PAD_INST,1))
				else:
                                        self.lockvideo.acquire()
                                	self.instpad.addstr(1,1,self.Vinstdata_head,self.CYANONBLACK)
                                        self.instpad.addstr(2,2,"waiting refresh... ",self.GREENONBLACK)
                                        self.instpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        self.lockvideo.release()
                        except Exception as err:
                                self.instpad =-10
				self.WinPrintError("Wininst thrd Error:"+str(err) )

        def Wintbs(self):
                y = self.WinOtopData[self.ID_PAD_TBS][1]
                x = self.WinOtopData[self.ID_PAD_TBS][2]
                nlines = self.WinOtopData[self.ID_PAD_TBS][3]
                hsize = len(self.Vtbsdata_head)
		self.tbs_head = 'Tablespace - max five used'

                Ltmp=(self.ID_PAD_TBS,y,x,nlines,hsize)
                self.padrefreshcoord.append(Ltmp)

                try:
                        self.tbspad = curses.newpad(y+nlines+3,x+hsize+2)
                        self.tbswinbox = curses.newwin( nlines+3, hsize+3, y, x)
                except Exception as err:
                        self.tbspad =-1
                        self.WinPrintError("Wintbs curses Error:"+str(err) )
                finally:
                        try:
                                if not self.WinCheckThreadAlive(self.idthtbs):
                                        self.idthtbs = threading.Thread(target=self._WintbsshowTH,name='tbsTH')
                                        self.idthtbs.setDaemon(True)
                                        self.thConfig.append((self.ID_PAD_TBS,1))
                                else:
                                        self.lockvideo.acquire()
                                        self.tbspad.addstr(1,1,self.Vtbsdata_head,self.CYANONBLACK)
                                        self.tbspad.addstr(2,2,"waiting refresh..." ,self.GREENONBLACK)
                                        self.tbspad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        self.lockvideo.release()

                        except Exception as err:
                                self.tbspad =-10
                                self.WinPrintError("Wintbs thrd Error:"+str(err) )


        def Winsess(self):
                y = self.WinOtopData[self.ID_PAD_SESS][1]
                x = self.WinOtopData[self.ID_PAD_SESS][2]
                nlines = self.WinOtopData[self.ID_PAD_SESS][3]
                hsize = len(self.Vsessdata_head)
		self.session_head = 'Active sessions (no sys/system)'
		virtual_v_size = nlines*self.MAX_SESS_ROWS + y + 3

                Ltmp=(self.ID_PAD_SESS,y,x,nlines,hsize)
                self.padrefreshcoord.append(Ltmp)

		try: 
			self.sesspad = curses.newpad(virtual_v_size,x+hsize+2)   
			self.sesswinbox = curses.newwin( nlines+3, hsize+3, y, x)
                except Exception as err:
			self.sesspad =-1
			self.WinPrintError("Winsess curses Error:"+str(err) )
		finally:
			try:
				if not self.WinCheckThreadAlive(self.idthsess):
					self.idthsess = threading.Thread(target=self._WinsessshowTH,name='sessshowTH')
					self.idthsess.setDaemon(True)
					self.thConfig.append((self.ID_PAD_SESS,1))
				else:
                                        self.lockvideo.acquire()
                                        self.sesspad.addstr(1,1,self.Vsessdata_head,self.CYANONBLACK)
                                        self.sesspad.addstr(2,2,"waiting refresh... ",self.GREENONBLACK)
                                        self.sesspad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        self.lockvideo.release()
					
			except Exception as err:
				self.sesspad =-10
				self.WinPrintError("Winsess thrd Error:"+str(err) )


	def Wintopsql(self):
		y = self.WinOtopData[self.ID_PAD_TOPSQL][1]
		x = self.WinOtopData[self.ID_PAD_TOPSQL][2]
		nlines = self.WinOtopData[self.ID_PAD_TOPSQL][3]
                hsize = len(self.Vtopsql_head)
		self.topsql_head = 'Top 5 sql in last awr snapshot (no sys/system)'

		Ltmp=(self.ID_PAD_TOPSQL,y,x,nlines,hsize)
		self.padrefreshcoord.append(Ltmp)
		
		try: 
			self.topsqlpad = curses.newpad(y+nlines+3,x+hsize+2)
			self.topsqlwinbox = curses.newwin( nlines+3, hsize+3, y, x)
                except Exception as err:
			self.topsqlpad =-1
			self.WinPrintError("Wintopsql curses Error:"+str(err) )
		finally:
			try:
				if not self.WinCheckThreadAlive(self.idthtopsql):
					self.idthtopsql = threading.Thread(target=self._WinTopSqlshowTH,name='topsqlTH')
					self.idthtopsql.setDaemon(True)
					self.thConfig.append((self.ID_PAD_TOPSQL,1))
				else:
					self.lockvideo.acquire()
                               		self.topsqlpad.addstr(1,1,self.Vtopsql_head,self.CYANONBLACK)
                               		self.topsqlpad.addstr(2,2,"waiting refresh..." ,self.GREENONBLACK)
                                  	self.topsqlpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        self.lockvideo.release()

			except Exception as err:
				self.tbspad =-10
				self.WinPrintError("Wintopsql thrd Error:"+str(err) )

	def _WinconninfoshowTH(self):
                while 1:
                        thS = [i for i,thLS in enumerate(self.thConfig) if thLS[0]==self.ID_PAD_CI]
                        if self.thConfig[thS[0]][1] == 1:    
                                cishow = 0
                                if (self.connIpad != -10) and (self.connIpad != -1):
                                        y = self.WinOtopData[self.ID_PAD_CI][1]
                                        x = self.WinOtopData[self.ID_PAD_CI][2]
                                        nlines = self.WinOtopData[self.ID_PAD_CI][3]
                                        hsize=len(self.Vconndata_head)


                                        self.WinThUpdate(self.ID_PAD_CI,self.TH_RUNNING)
                                        cinfo = self.DBconnectioninfo()

                                        self.WinThUpdate(self.ID_PAD_CI,self.TH_REQUEST_VIDEO_LOCK) 
                                        self.lockvideo.acquire()

                                        self.connIpad.addstr(1,1,self.Vconndata_head,self.CYANONBLACK)

                                        for j in range(0,len(cinfo)):
                                                try:
                                                        self.connIpad.addstr(1+j+1,1,self.Vconndata_srows[j],self.GREENONBLACK)
                                                except Exception as err:
                                                        cishow = -2
                                                        break
                                        if cishow == 0:
                                                if self.winConnInfoactive:
                                                        self.connIwinbox.box()
                                                        self.connIwinbox.refresh()
                                                self.connIpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        else:
                                                self.connIpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                                cishow = -1

                                        self.lockvideo.release()
                                        self.WinThUpdate(self.ID_PAD_CI,self.TH_ENTERING_SLEEP)

					#self.WinCprint(2,18,'Cishow = '+str(cishow) )

                                time.sleep(self.ENTERING_SLEEP_TIME)
                                self.WinThUpdate(self.ID_PAD_CI,self.TH_SLEEPING)
                                time.sleep(self.SLEEP_CI_DATA-self.ENTERING_SLEEP_TIME)
                        else:
                                if self.thConfig[thS[0]][1] == 0:    # thread suspended
                                        self.WinThUpdate(self.ID_PAD_CI,self.TH_SLEEPING)


	def _WindbshowTH(self):
                while 1:
			thS = [i for i,thLS in enumerate(self.thConfig) if thLS[0]==self.ID_PAD_DB]
			if self.thConfig[thS[0]][1] == 1:    
                        	dbshow = 0
                        	if (self.dbpad != -10) and (self.dbpad != -1):
                                	y = self.WinOtopData[self.ID_PAD_DB][1]
                                	x = self.WinOtopData[self.ID_PAD_DB][2]
                                	nlines = self.WinOtopData[self.ID_PAD_DB][3]
                                	hsize=len(self.Vdbdata_head)

					self.WinThUpdate(self.ID_PAD_DB,self.TH_RUNNING)
                               		dbinfo = self.DBdatainfo()

                                        self.WinThUpdate(self.ID_PAD_DB,self.TH_REQUEST_VIDEO_LOCK) 
					self.lockvideo.acquire()

                                	self.dbpad.addstr(1,1,self.Vdbdata_head,self.CYANONBLACK)

					err = 0

                                	for j in range(0,len(dbinfo)):
                                        	try:
                                               		self.dbpad.addstr(1+j+1,1,self.Vdbdata_srows[j],self.GREENONBLACK)
                                        	except Exception as err:
                                               		dbshow = -2
                                               		break
                                	if dbshow == 0:
                                        	if self.winDbactive:
                                                	self.dbwinbox.box()
                                                	self.dbwinbox.refresh()
                                        	self.dbpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                	else:
                                        	dbshow = -1
					
					self.lockvideo.release()

                               		if dbshow < 0 :
						self.WinPrintError("_WindbshowTH Error: "+str(err) )

					self.WinThUpdate(self.ID_PAD_DB,self.TH_ENTERING_SLEEP)

                       		time.sleep(self.ENTERING_SLEEP_TIME)
				self.WinThUpdate(self.ID_PAD_DB,self.TH_SLEEPING)
                       		time.sleep(self.SLEEP_DB_DATA-self.ENTERING_SLEEP_TIME)
			else:
				if self.thConfig[thS[0]][1] == 0:    # thread suspended
					self.WinThUpdate(self.ID_PAD_DB,self.TH_SLEEPING)



	def _WininstshowTH(self):
                while 1:
			thS = [i for i,thLS in enumerate(self.thConfig) if thLS[0]==self.ID_PAD_INST]
			if self.thConfig[thS[0]][1] == 1:    
                        	instshow = 0
                        	if self.instpad != -10 and self.instpad != -1:
                                	y = self.WinOtopData[self.ID_PAD_INST][1]
                                	x = self.WinOtopData[self.ID_PAD_INST][2]
                                	nlines = self.WinOtopData[self.ID_PAD_INST][3]
                                	hsize=len(self.Vinstdata_head)
					self.WinCprint(y,x+2,self.instdata_head,self.BLUEONBLACK)
	
					self.WinThUpdate(self.ID_PAD_INST,self.TH_RUNNING)
                                	instinfo = self.DBinstinfo()

                                        self.WinThUpdate(self.ID_PAD_INST,self.TH_REQUEST_VIDEO_LOCK) 
					self.lockvideo.acquire()

					self.instpad.clear()
                                	self.instpad.addstr(1,1,self.Vinstdata_head,self.CYANONBLACK)

					err = 0

                                	for j in range(0,len(instinfo)):
                                        	try:
                                                	self.instpad.addstr(1+j+1,1,self.Vinstdata_srows[j],self.GREENONBLACK)
                                        	except Exception as err:
                                                	instshow = -2
                                                	break
                                	if instshow == 0:
                                        	if self.winInstactive:
                                                	self.instwinbox.box()
                                                	self.instwinbox.refresh()
                                        	self.instpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                	else:
                                        	instshow = -1

					self.lockvideo.release()
					self.WinCprint(y,x+2,self.instdata_head,self.BLUEONBLACK)

                               		if instshow < 0 :
						self.WinPrintError("_WininstshowTH Error:   "+str(err) )

					self.WinThUpdate(self.ID_PAD_INST,self.TH_ENTERING_SLEEP)

                       		time.sleep(self.ENTERING_SLEEP_TIME)
				self.WinThUpdate(self.ID_PAD_INST,self.TH_SLEEPING)
                       		time.sleep(self.SLEEP_INSTANCE_DATA-self.ENTERING_SLEEP_TIME)
			else:
				if self.thConfig[thS[0]][1] == 0:    # thread suspended
					self.WinThUpdate(self.ID_PAD_INST,self.TH_SLEEPING)


        def _WintbsshowTH(self):
                try:
                        while 1:
                                thS = [i for i,thLS in enumerate(self.thConfig) if thLS[0]==self.ID_PAD_TBS]
                                if self.thConfig[thS[0]][1] == 1:
                                        tbsshow = 0
                                        if self.tbspad != -10 and self.tbspad != -1:
                                                y = self.WinOtopData[self.ID_PAD_TBS][1]
                                                x = self.WinOtopData[self.ID_PAD_TBS][2]
                                                nlines = self.WinOtopData[self.ID_PAD_TBS][3]
                                                hsize=len(self.Vtbsdata_head)
						self.WinCprint(y,x+2,self.tbs_head,self.BLUEONBLACK)

                                                self.WinThUpdate(self.ID_PAD_TBS,self.TH_RUNNING)
                                                tbsinfo = self.DBtbsinfo()

                                                self.WinThUpdate(self.ID_PAD_TBS,self.TH_REQUEST_VIDEO_LOCK)
                                                self.lockvideo.acquire()

                                                self.tbspad.clear()
                                                self.tbspad.addstr(1,1,self.Vtbsdata_head,self.CYANONBLACK)

                                                for j in range(0,len(tbsinfo)):
                                                        try:
                                                                self.tbspad.addstr(1+j+1,1,self.Vtbsdata_srows[j],self.GREENONBLACK)
                                                        except Exception as err:
                                                                tbsshow = -2
                                                                break
                                                if tbsshow == 0:
                                                        if self.winTbsactive:
                                                                self.tbswinbox.box()
                                                                self.tbswinbox.refresh()
                                                        self.tbspad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                                else:
                                                        tbsshow = -1

                                                self.lockvideo.release()
						self.WinCprint(y,x+2,self.tbs_head,self.BLUEONBLACK)

                                                if tbsshow == -2:
                                                        self.WinPrintError("_WintbsshowTH Error:"+str(err) )

                                                self.WinThUpdate(self.ID_PAD_TBS,self.TH_ENTERING_SLEEP)

                                        time.sleep(self.ENTERING_SLEEP_TIME)
                                        self.WinThUpdate(self.ID_PAD_TBS,self.TH_SLEEPING)
                                        time.sleep(self.SLEEP_TBS_DATA-self.ENTERING_SLEEP_TIME)
                                else:
                                        if self.thConfig[thS[0]][1] == 0:    # thread suspended
                                                self.WinThUpdate(self.ID_PAD_TBS,self.TH_SLEEPING)
                except:
                        pass

        def _WinTopSqlshowTH(self):
               	while 1:
                       	thS = [i for i,thLS in enumerate(self.thConfig) if thLS[0]==self.ID_PAD_TOPSQL]
                       	if self.thConfig[thS[0]][1] == 1:
                               	topsqlshow = 0
                               	if (self.topsqlpad != -10) and (self.topsqlpad != -1):
                                       	y = self.WinOtopData[self.ID_PAD_TOPSQL][1]
                                       	x = self.WinOtopData[self.ID_PAD_TOPSQL][2]
                                       	nlines = self.WinOtopData[self.ID_PAD_TOPSQL][3]
                                       	hsize=len(self.Vtopsql_head)
					self.WinCprint(y,x+2,self.topsql_head,self.BLUEONBLACK)

                                       	self.WinThUpdate(self.ID_PAD_TOPSQL,self.TH_SESS_REQUEST_LOCK)

                                       	self.locksessth.acquire()
                                       	topsqlinfo = self.DBtopsqlinfo()
                                       	self.locksessth.release()

                                       	self.WinThUpdate(self.ID_PAD_TOPSQL,self.TH_REQUEST_VIDEO_LOCK)
                                       	self.lockvideo.acquire()

                                       	self.topsqlpad.clear()
                                       	self.topsqlpad.addstr(1,1,self.Vtopsql_head,self.CYANONBLACK)


                                       	for j in range(0,len(topsqlinfo)):
                                               	try:
                                                       	self.topsqlpad.addstr(1+j+1,1,self.Vtopsql_srows[j],self.GREENONBLACK)
                                               	except Exception as err:
                                                       	topsqlshow = -2
                                                       	break
                                       	if topsqlshow == 0:
                                               	#if self.winTopSqlactive:
                                                #self.topsqlwinbox.box()
						self.topsqlwinbox.border(' ',' ','-','-',' ',' ',' ',' ')
                                                self.topsqlwinbox.refresh()
                                               	self.topsqlpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                       	else:
                                               	topsqlshow = -1

                                       	self.lockvideo.release()
					self.WinCprint(y,x+2,self.topsql_head,self.BLUEONBLACK)

                                       	if topsqlshow == -2:
                                               	self.WinPrintError("_WinTopSqlshowTH Error:"+str(err) )

                                       	self.WinThUpdate(self.ID_PAD_TOPSQL,self.TH_ENTERING_SLEEP)

                               	time.sleep(self.ENTERING_SLEEP_TIME)
                               	self.WinThUpdate(self.ID_PAD_TOPSQL,self.TH_SLEEPING)
                               	time.sleep(self.SLEEP_TOPSQL_DATA-self.ENTERING_SLEEP_TIME)
                       	else:
                               	if self.thConfig[thS[0]][1] == 0:    # thread suspended
                                       	self.WinThUpdate(self.ID_PAD_TOPSQL,self.TH_SLEEPING)

	def _WinsessshowTH(self):
                while 1:
                        thS = [i for i,thLS in enumerate(self.thConfig) if thLS[0]==self.ID_PAD_SESS]
                        if self.thConfig[thS[0]][1] == 1:    
                                sessshow = 0
                                if (self.sesspad != -10) and (self.sesspad != -1):
                                        y = self.WinOtopData[self.ID_PAD_SESS][1]
                                        x = self.WinOtopData[self.ID_PAD_SESS][2]
                                        nlines = self.WinOtopData[self.ID_PAD_SESS][3]
                                        hsize=len(self.Vsessdata_head)
					self.WinCprint(y,x+2,self.session_head,self.BLUEONBLACK)
					
                                        self.WinThUpdate(self.ID_PAD_SESS,self.TH_SESS_REQUEST_LOCK)  

					self.locksessth.acquire()
                                        sessinfo = self.DBsessinfo()
					if self.trackfsop and len(sessinfo)>0:  # if FSop tracking is on and there are data then: write to file sessdata
                                        	self.WinThUpdate(self.ID_PAD_SESS,self.TH_SESS_TRACK_FSOP)
						self._WinSpoolFSop()
					self.locksessth.release()

                                        self.WinThUpdate(self.ID_PAD_SESS,self.TH_REQUEST_VIDEO_LOCK) 
                                        self.lockvideo.acquire()

					self.sesspad.clear()
                                        self.sesspad.addstr(1,1,self.Vsessdata_head,self.CYANONBLACK)


                                        for j in range(0,len(sessinfo)):
                                                try:
                                                        self.sesspad.addstr(1+j+1,1,self.Vsessdata_srows[j],self.GREENONBLACK)
                                                except Exception as err:
                                                        sessshow = -2
                                                        break
                                        if sessshow == 0:
                                                if self.winSessactive:
                                                        self.sesswinbox.box()
                                                        self.sesswinbox.refresh()
                                                self.sesspad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)
                                        else:
                                                sessshow = -1

                                        self.lockvideo.release()
					self.WinCprint(y,x+2,self.session_head,self.BLUEONBLACK)

                               		if sessshow == -2:
						self.WinPrintError("_WinsessshowTH Error:"+str(err) )

                                        self.WinThUpdate(self.ID_PAD_SESS,self.TH_ENTERING_SLEEP)

                                time.sleep(self.ENTERING_SLEEP_TIME)
                                self.WinThUpdate(self.ID_PAD_SESS,self.TH_SLEEPING)
                                time.sleep(self.SLEEP_SESS_DATA-self.ENTERING_SLEEP_TIME)
                        else:
                                if self.thConfig[thS[0]][1] == 0:    # thread suspended
                                        self.WinThUpdate(self.ID_PAD_SESS,self.TH_SLEEPING)

	def WinUnsetBox(self,wbox,wpad,id_pad):
		self.lockvideo.acquire()
		wbox.border(' ',' ',' ',' ',' ',' ',' ',' ')
		wbox.refresh()
		padrefindex =[i for i,elem in enumerate(self.padrefreshcoord) if elem[0]==id_pad][0]
		y = self.padrefreshcoord[padrefindex][1]
		x = self.padrefreshcoord[padrefindex][2]
		nlines =  self.padrefreshcoord[padrefindex][3]
		hsize =  self.padrefreshcoord[padrefindex][4]
                wpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)

		self.lockvideo.release()
		

	def WinSetBox(self,wbox,wpad,id_pad):
		self.lockvideo.acquire()
		wbox.border()
		wbox.refresh()
		padrefindex =[i for i,elem in enumerate(self.padrefreshcoord) if elem[0]==id_pad][0]
		y = self.padrefreshcoord[padrefindex][1]
		x = self.padrefreshcoord[padrefindex][2]
		nlines =  self.padrefreshcoord[padrefindex][3]
		hsize =  self.padrefreshcoord[padrefindex][4]
                wpad.refresh(1,0,y+1,x+1,y+nlines+1,x+hsize)

		self.lockvideo.release()

	def Winthset(self):
		self.lockvideo.acquire()

		y = self.Ypos_start_sensor 
		x = self.Xpos_start_sensor

		head = ""
		voidhead = ""
		# make led display
                for k in range( 0, len(self.WinOtopData)):
			head += self.WinOtopData[k][5]
			voidhead += "_"
			if k<len(self.WinOtopData)-1:
				head += "|"
				voidhead += "|"
		hsize = len(head)

		try:
			winthr = curses.newwin( 4, hsize+2, y, x)
			winthr.box()
			winthr.addstr(1,1,head)
			winthr.addstr(2,1,voidhead)
		except Exception as err:
			self.winthr = -1
			self.WinPrintError("Winthset Error:"+str(err) )

		self.lockvideo.release()
		return(winthr)

	def WinThUpdate(self,id_th,th_status):
		if id_th >= 0:
			self.lockvideo.acquire()
			try:
				# calc led position
				xled_position = 2*id_th+1 # position can be : 1,3,5,7,9,11

				# status, with thrdRun=0	
				# 0 : thread paused

				# search thconfig run-status for the thread id_th
				ixthrunvalue  = [i for i,elem in enumerate(self.thConfig) if elem[0]==id_th][0]
				thrdRun = self.thConfig[ixthrunvalue][1]

				if thrdRun == 1: # thread active
					if th_status == self.TH_RUNNING:   # running
						self.winledthread.addstr(2,xled_position," ",self.WHITEONYELLOW )
                			else:
						if th_status == self.TH_SLEEPING: # sleeping
							self.winledthread.addstr(2,xled_position,"_")
		        			else:
							if th_status == self.TH_REQUEST_VIDEO_LOCK: # wait video lock
								self.winledthread.addstr(2,xled_position," ", self.BLACKONGREEN)
							else:
								if th_status == self.TH_REQUEST_DB_CONN: # dbconn lock acquired
									self.winledthread.addstr(2,xled_position," ",self.WHITEONBLUE )
								else:
									if th_status == self.TH_ENTERING_SLEEP: # entering  sleep
										self.winledthread.addstr(2,xled_position," ", self.WHITEONRED )
									else:
										if th_status == self.TH_DB_RECONNECTING: #  db reconnecting
											self.winledthread.addstr(2,xled_position," ", self.BLACKONCYAN )
										else:
											if th_status == self.TH_SQL_RUNNING: #  executing sql
												self.winledthread.addstr(2,xled_position,"E", self.BLACKONYELLOW )
											else:
												if th_status == self.TH_ROW_FETCHING: #  fetching rows 
													self.winledthread.addstr(2,xled_position,"F", self.BLACKONYELLOW )
												else:
													if th_status == self.TH_SESS_REQUEST_LOCK: # sess operation lock
														self.winledthread.addstr(2,xled_position,"X", self.BLACKONYELLOW )
													else:
														if th_status == self.TH_SESS_TRACK_FSOP: # sess track fsop to file
															self.winledthread.addstr(2,xled_position,"#", self.BLACKONYELLOW )
				else:
					if thrdRun == 0:  # thread non active = suspended
						self.winledthread.addstr(2,xled_position,"X", self.WHITEONMAGENTA )
	
				self.winledthread.refresh()
			except Exception as err:
				self.WinPrintError("WinThUpdate Error:"+str(err) )
			finally:
				self.lockvideo.release()

	def WinSetMenu(self):

		#format: menuitem,activecolor,noactivecolor,itemcoloractive = 1, first one, =0 second one
		self.generalmenuitem=[
('|',self.VnormalText,self.VnormalText,1), \
('TAB=switch box',self.WHITEONBLUE,self.BLACKONBLACK,1), \
('T=spool TopSQL',self.WHITEONBLUE,self.BLACKONBLACK,1), \
('z=track FSop',self.WHITEONBLUE,self.YELLOWONRED,1), \
('ESC=exit',self.WHITEONBLUE,self.BLACKONBLACK,1), \
#('--',self.VnormalText,self.VnormalText,1), \
]

		self.instmenuitem=[ \
]

		self.sessmenuitem=[ \
('\-->',self.VnormalText,self.VnormalText,1), \
('e=sort by ela',self.WHITEONBLUE,self.REDONBLACK,1), \
('l=show lock',self.WHITEONBLUE,self.REDONBLACK,1), \
('x=sort by exec',self.WHITEONBLUE,self.REDONBLACK,1), \
('r=sort by rows',self.WHITEONBLUE,self.REDONBLACK,1), \
('space=spool',self.WHITEONBLUE,self.VnormalText,1), \
]

	def WinSelectMenuColor(self, menu):
		if menu[3]:
			color = menu[1]
		else:
			color = menu[2]

		return(color)
		
		
	def WinShowMenu(self):
		Y = 1
		X = self.Xpos_start_menu

		h = 0
		# main menu 
		for j in range(0,len(self.generalmenuitem)):
			item_color = self.WinSelectMenuColor(self.generalmenuitem[j])
			self.WinCprint(Y,X+h,self.generalmenuitem[j][0],item_color)
			h +=len(self.generalmenuitem[j][0])+1

	def WinShowSubMenu(self):
		Y = 2
		X = self.Xpos_start_submenu
		# show menu for instance , if any
		self.WinCprint(Y,X,"                                                                        ");
		if self.winInstactive:		
			h = 0
			last_item_main_menu = 3
			for j in range(0,len(self.instmenuitem)):
				item_color_SUBM = self.WinSelectMenuColor(self.instmenuitem[j])
				self.WinCprint(Y,X+h,self.instmenuitem[j][0],item_color_SUBM)
				h +=len(self.instmenuitem[j][0])+1

		# show menu for sessions, if  any
		if self.winSessactive:	
			h = 0
			last_item_main_menu = 3
			for j in range(0,len(self.sessmenuitem)):
				if j == (self.DBsessionOrder):
					item_color_SUBM = self.sessmenuitem[j][2]
				else:
					item_color_SUBM = self.WinSelectMenuColor(self.sessmenuitem[j])
				self.WinCprint(Y,X+h,self.sessmenuitem[j][0],item_color_SUBM)
				h +=len(self.sessmenuitem[j][0])+1

		# show menu for tablespaces, if any
		if self.winTbsactive:	
			pass


	def WinPrintError(self,msg):
			ypos = self.scrsize[0]-2
			self.WinCprint(ypos,2,msg[:msg.find('\n')],self.REDONBLACK )

	def WinPrintStatus(self,msg):
			if self.statusprint:
				ypos = self.scrsize[0]-3
				self.WinCprint(ypos,2,"DB OP -> " + msg)

	def WinTxtSessSpool(self):
	        fname = 'SESS_spool_'+str(self.Vdbdata_rows[0][0])+"_"+datetime.datetime.now().strftime("%d%m%Y_%H%M")+'.txt'
		try:
                        self.WinThUpdate(self.ID_PAD_SESS,self.TH_SESS_REQUEST_LOCK)  
			self.locksessth.acquire()

			sortmsglist=['void','Sort by Avg Ela','Show by lock','Sort by Execs','Sort by rows x exec']

			fobj = open(fname,'a')

			if fname != self.lastfilenamespool: 	# file not exists. Write head info
				fobj.write("\n")
                                fobj.write("                                                                                                         Otop Session Report            " + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + "\n" )
				fobj.write("                                                                                                         " + sortmsglist[self.DBsessionOrder] + "\n" )
				fobj.write("                                                                                                         File name: " + fname + "\n\n\n" )
			else:
				# write sort info
				fobj.write("\n")
				fobj.write("     " + sortmsglist[self.DBsessionOrder] + "\n" )
				fobj.write("\n\n")

			for n in range(0,len(self.Vsessdata_rows) ):

				# 
				# call sqlplan extractor - arguments: instance, sqlid, child, plan hash
				#	
				planinfo = self.DBsessplan(self.Vsessdata_rows[n][2],self.Vsessdata_rows[n][21],self.Vsessdata_rows[n][22],self.Vsessdata_rows[n][24] )

				fobj.write("           Instance:           "+str(self.Vsessdata_rows[n][2])+"\n")
				fobj.write("           Sid:                "+str(self.Vsessdata_rows[n][0])+"\n")
				fobj.write("           Serial#:            "+str(self.Vsessdata_rows[n][1])+"\n")
				fobj.write("           Username:           "+str(self.Vsessdata_rows[n][25])+"\n")
				fobj.write("           Program name:       "+str(self.Vsessdata_rows[n][26])+"\n")
				fobj.write("           Machine name:       "+str(self.Vsessdata_rows[n][27])+"\n")
				fobj.write("           SQLID:              "+str(self.Vsessdata_rows[n][21])+"\n")
				fobj.write("           CHILD:              "+str(self.Vsessdata_rows[n][22])+"\n")
				fobj.write("           PLAN HASH:          "+str(self.Vsessdata_rows[n][24])+"\n")
				fobj.write("           Avg Elapsed x exec: "+str(self.Vsessdata_rows[n][8])+"s\n")
				fobj.write("           Executions:         "+str(self.Vsessdata_rows[n][10])+"\n")
				fobj.write("           Avg Rows x exec:    "+str(self.Vsessdata_rows[n][9])+"\n")
				fobj.write("\n")
				fobj.write("SQL Text ("+str(self.Vsessdata_rows[n][21])+"):\n" )
				fobj.write("------------------------------------------------------------------------------------\n")
				fobj.write( str( self.Vsessdata_rows[n][23] ) )
				fobj.write("\n\n")

			        if planinfo != -1:
					if len(planinfo) > 1:
						for i in range(0,len(planinfo)):
							fobj.write(str(planinfo[i][0]))
							fobj.write("\n")
					else:
						fobj.write("- NO PLAN INFO\n" )
                                else:
					if planinfo < 0:
						fobj.write("- PLAN ERROR\n" )
						fobj.write("\n")
					else:
						fobj.write("- NO PLAN INFO\n" )
				fobj.write("______________________________________________________________________________________________________________________________________\n\n")

			fobj.close()
			self.lastfilenamespool = fname
                        self.WinThUpdate(self.ID_PAD_SESS,self.TH_SLEEPING)
		except Exception as err:
			fobj = -1
			self.WinPrintError("WinTxtSessSpool Error:"+str(err) )
		finally:
			self.locksessth.release()

		return (fobj)

	def _WinSpoolTopSQL(self):
                fname = 'TOPSQL_spool_'+str(self.Vdbdata_rows[0][0])+"_"+datetime.datetime.now().strftime("%d%m%Y_%H%M")+'.txt'
                try:
                        self.WinThUpdate(self.ID_PAD_TOPSQL,self.TH_SESS_REQUEST_LOCK)
                        self.locksessth.acquire()

                        fobj = open(fname,'w')

                        fobj.write("\n")
                        fobj.write("                                                                                                         Otop Top 5 SQL            " + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + "\n" )
                        fobj.write("                                                                                                         Sort by Average Elapsed Time per execution (AvgEla)\n" )
                        fobj.write("                                                                                                         File name: " + fname + "\n\n\n" )

			
                        fobj.write("                                                         S U M M A R Y                 \n" )	
                        fobj.write("                                                         -------------                \n\n" )	

			fobj.write(self.Vtopsql_head + "\n" )

			for j in range(0,len(self.Vtopsql_rows)):
				fobj.write(self.Vtopsql_srows[j] + "\n" )
			fobj.write("\n\n\n")

                        fobj.write("                                                         D E T A I L S                 \n" )	
                        fobj.write("                                                         -------------                \n\n\n" )	

			for j in range(0,len(self.Vtopsql_rows)):
				fobj.write(self.Vtopsql_head + "\n" )
				fobj.write(self.Vtopsql_srows[j] + "\n\n" )
				# 
				# call sqlplan extractor - arguments: instance, sqlid, child, plan hash
				#	
				planinfo = self.DBsessplan( self.Vtopsql_rows[j][0],  self.Vtopsql_rows[j][2],-1, self.Vtopsql_rows[j][3] )

			        if planinfo != -1:
					if len(planinfo) > 1:
						for k in range(0,len(planinfo)):
							fobj.write(str(planinfo[k][0]))
							fobj.write("\n")
					else:
						fobj.write("\n- NO PLAN INFO\n\n\n" )
                                else:
					if planinfo < 0:
						fobj.write("\n- PLAN ERROR\n\n\n" )
						fobj.write("\n")
					else:
						fobj.write("\n- NO PLAN INFO\n\n\n" )

				fobj.write("__________________________________________________________________________________________________________________________________________________________________\n\n\n")

                        fobj.close()
                        self.WinThUpdate(self.ID_PAD_TOPSQL,self.TH_SLEEPING)
                except Exception as err:
                        fobj = -1
                        self.WinPrintError("WinSpoolTopSQL Error:"+str(err) )
                finally:
                        self.locksessth.release()

                return (fobj)

	def _WinSpoolFSop(self):
                fname = 'FSOP_spool_'+str(self.Vdbdata_rows[0][0])+"_"+datetime.datetime.now().strftime("%d%m%Y")+'.txt'
		try:
			if fname != self.lastfilenametrackfsop: 	# file not exists. Create file
                        	fobj = open(fname,'w')
                        	fobj.write("\n")
                        	fobj.write("                                                                                                         Otop Track FSop            " + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + "\n" )
				fobj.write("                                                                                                         File name: " + fname + "\n\n\n" )
			else:
                        	fobj = open(fname,'a')          # file exists, append

			for k in range(0,len(self.Vsessdata_rows) ):
				# check if exists an FSop
				fsop = self.Vsessdata_rows[k][11]
				if fsop != ' ':   
			        	# calc fsop bytes value
				   	lastch = fsop[len(fsop)-1]
				   	if lastch == 'K':
						fsop_val = float(fsop[:len(fsop)-1]) * 1000
                                    	else:
						if lastch == 'M':
							fsop_val = float(fsop[:len(fsop)-1]) * 1000000
						else:
							fsop_val = float(fsop)

					# check if fsop byte size is in range of capture
					if fsop_val >= self.trackfsopminsize:
						# write to file
						fobj.write( "Systime:  " + datetime.datetime.now().strftime("%d-%m-%Y %H:%M")+"\n" )
						fobj.write(self.Vsessdata_head + "\n" )
						fobj.write(self.Vsessdata_srows[k] + "\n\n" )
						fobj.write("\n")
						fobj.write("SQL Text ("+str(self.Vsessdata_rows[k][21])+"):\n" )
						fobj.write("------------------------------------------------------------------------------------\n")
						fobj.write( str( self.Vsessdata_rows[k][23] ) )
						fobj.write("\n\n")
						# 
						# call sqlplan extractor - arguments: instance, sqlid, child, plan hash
						#	
						planinfo = self.DBsessplan(self.Vsessdata_rows[k][2],self.Vsessdata_rows[k][21],self.Vsessdata_rows[k][22],self.Vsessdata_rows[k][24] )

	                                	if planinfo != -1:
                                        		if len(planinfo) > 1:
                                                		for y in range(0,len(planinfo)):
                                                        		fobj.write(str(planinfo[y][0]))
                                                        		fobj.write("\n")
                                        		else:
                                                		fobj.write("- NO PLAN INFO\n" )
                                		else:
                                        		if planinfo < 0:
                                                		fobj.write("- PLAN ERROR\n" )
                                                		fobj.write("\n")
                                        		else:
                                                		fobj.write("- NO PLAN INFO\n" )
                                		fobj.write("______________________________________________________________________________________________________________________________________\n\n")

                        fobj.close()
			self.lastfilenametrackfsop = fname
		except:
                        fobj = -1
                        self.WinPrintError("WinSpoolFSop Error:"+str(err) )


	def _WinCheckFocusBox(self):
		if self.winInstactive:  # sess box selected
                        y = self.WinOtopData[self.ID_PAD_INST][1]
                        x = self.WinOtopData[self.ID_PAD_INST][2]
			self.winInstactive = 0
                        self.WinUnsetBox(self.instwinbox,self.instpad,self.ID_PAD_INST)
			self.WinCprint(y,x+2,self.instdata_head,self.BLUEONBLACK)
                        self.winSessactive = 1;
                        self.WinSetBox(self.sesswinbox,self.sesspad,self.ID_PAD_SESS)
                        pos = self.ID_PAD_SESS
                        y = self.WinOtopData[self.ID_PAD_SESS][1]
                        x = self.WinOtopData[self.ID_PAD_SESS][2]
                        self.WinShowSubMenu()
			self.WinCprint(y,x+2,self.session_head,self.BLUEONBLACK)
                        self.WinProcKeySess() # process keypress in sess box
                else:
                        if self.winSessactive:  # tbs box selected
				self.winSessactive = 0;
                       		y = self.WinOtopData[self.ID_PAD_SESS][1]
                       		x = self.WinOtopData[self.ID_PAD_SESS][2]
                                self.WinUnsetBox(self.sesswinbox,self.sesspad,self.ID_PAD_SESS)
				self.WinCprint(y,x+2,self.session_head,self.BLUEONBLACK)
                                self.winTbsactive = 1
                                self.WinSetBox(self.tbswinbox,self.tbspad,self.ID_PAD_TBS)
                                pos = self.ID_PAD_TBS
                                self.WinShowSubMenu()
                       		y = self.WinOtopData[self.ID_PAD_TBS][1]
                       		x = self.WinOtopData[self.ID_PAD_TBS][2]
				self.WinCprint(y,x+2,self.tbs_head,self.BLUEONBLACK)
                        else:
				if self.winTbsactive:   # instances box selected
					self.winTbsactive = 0;
                        		y = self.WinOtopData[self.ID_PAD_TBS][1]
                        		x = self.WinOtopData[self.ID_PAD_TBS][2]
                                        self.WinUnsetBox(self.tbswinbox,self.tbspad,self.ID_PAD_TBS)
					self.WinCprint(y,x+2,self.tbs_head,self.BLUEONBLACK)
                                        self.winInstactive = 1
                                        self.WinSetBox(self.instwinbox,self.instpad,self.ID_PAD_INST)
                                        pos = self.ID_PAD_INST
                                        self.WinShowSubMenu()
                        		y = self.WinOtopData[self.ID_PAD_INST][1]
                        		x = self.WinOtopData[self.ID_PAD_INST][2]
					self.WinCprint(y,x+2,self.instdata_head,self.BLUEONBLACK)
		return(pos)

	def  _WinSwitchThreadState(self,pos):
        	try:
			ipos = self.thConfig.index((pos,1))
                        self.lockvideo.acquire()
                        self.thConfig.pop(ipos)
                        self.thConfig.append((pos,0))
                        self.lockvideo.release()
                        self.WinThUpdate(pos,0)
                except:
                        ipos = self.thConfig.index((pos,0))
                        self.lockvideo.acquire()
                        self.thConfig.pop(ipos)
                        self.thConfig.append((pos,1))
                        self.lockvideo.release()
                        self.WinThUpdate(pos,0)
                        self.WinProcKeySess() # process key in sess box

        def WinProcKeySess(self):
                kp = 0
                while (kp != 27) & (kp != 9) & (kp!=45) & (kp!=84) & (kp!=122): # while not press: esc,tab,minus,T,z
                        kp = self.WinCgetch()
                        if kp == 101: # e key
                                self.DBsessionOrder = 1
                        if kp == 108 : # l key
                                self.DBsessionOrder = 2
                        if kp == 120: # x key
                                self.DBsessionOrder = 3
                        if kp == 114: # r key
                                self.DBsessionOrder = 4
                        if kp == 32: # space key
                                if not self.WinTxtSessSpool():
                                        self.WinPrintError('Error txt spooling.')
                        if kp == 104: # h key
                                pass

                        self.WinShowSubMenu()

		if kp == 27:
			self.PRG_EXIT = 1

                curses.ungetch(kp) # push key to main loop
                return(kp)


	def _WinKeyLoopTH(self):
		kp = 0
		pos = self.ID_PAD_SESS 
		while kp != 27:  # ESC key
			if self.winSessactive:
				kp = self.WinProcKeySess()
			else:
				if self.winInstactive:
					pass
				else:
					if self.winTbsactive:
						pass

			if kp == 27:
				break
			else:
				kp = self.WinCgetch()
				if kp == 27:
					break

			if kp == 9:   # tab key : select box
				pos = self._WinCheckFocusBox()

			if kp == 45:  # minus key: suspend thread
				self._WinSwitchThreadState(pos)

			if kp == 84: # T key, spool TopSql
				self._WinSpoolTopSQL()

			if kp == 122: # z key, activate or deactivate trackFSop
				self.trackfsop = not self.trackfsop   # rotate flag value in true,false
				# repaint menu
				if self.trackfsop:
					#activate second color in self.generalmenuitem )
					tmpmenu = [(self.generalmenuitem[0])] + \
					          [(self.generalmenuitem[1])] + \
					          [(self.generalmenuitem[2])] + \
						  [(self.generalmenuitem[3][0],self.generalmenuitem[3][1],self.generalmenuitem[3][2],0)] + \
					          [(self.generalmenuitem[4])]  
				else:
					#activate first color in self.generalmenuitem )
					tmpmenu = [(self.generalmenuitem[0])] + \
					          [(self.generalmenuitem[1])] + \
					          [(self.generalmenuitem[2])] + \
						  [(self.generalmenuitem[3][0],self.generalmenuitem[3][1],self.generalmenuitem[3][2],1)] + \
					          [(self.generalmenuitem[4])]  

				self.generalmenuitem = tmpmenu
                		self.WinShowMenu()

		self.PRG_EXIT = 1

	def WinOtopRun(self):

		self.WinPrintOtopVersion()

		self.WinKeyLoop()
		self.WinConnInfo()
                self.WinBanner()
                self.Windb()
                self.Wininst()
                self.Wintbs()
		self.Wintopsql()
                self.Winsess()

                self.WinSetMenu()
                self.WinShowMenu()
                self.WinShowSubMenu()

			#start threads
		self.idthloop.start()
		self.idthtbs.start()
		self.idthconn.start()
		self.idthdb.start()
		self.idthinst.start()
		self.idthtopsql.start()
		self.idthsess.start()
		
			#join keyloop thread
		self.idthloop.join()

		try:
			while not self.PRG_EXIT:
				pass
		except Exception as err:
			self.WinPrintError("Exiting Otop.  Error:  "+str(err) )
			time.sleep(3)
		finally:
			if self.PRG_EXIT_SCR_SIZE:
				self.VWscreen.clear()
				self.VWscreen.refresh()
			self.WinPrintError("Exiting Otop                                        " )
			time.sleep(.5)
			

		self.End() # close connect and curses . restore screen settings

