#!/usr/bin/python 

from OtopClass import Otop

#
#######################################################################################
################################    M A I N   #########################################
#######################################################################################
#

if __name__ == "__main__":
	
	# login information
	# LogInfo=[user,password,host,service]
	#LoginInfo=['oracle_user','oracle_password','oracle_server','oracle_service']

	# screen minimum size: y=38, x=168
	myOtop = Otop(LoginInfo) 
	myOtop.Run() 	

	exit()

######################################
#################   END ##############
######################################
