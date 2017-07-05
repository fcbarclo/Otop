#!/usr/bin/python 

from OtopClass import Otop

#
#######################################################################################
################################    M A I N   #########################################
#######################################################################################
#

if __name__ == "__main__":
	
	# login information
	#LoginInfo=['oracle_user','oracle_password','oracle_server_IP_or_hostname','oracle_service']

	# screen minimum size: y=38, x=168
	myOtop = Otop(LoginInfo) 
	myOtop.Run() 	

	exit()

######################################
#################   END ##############
######################################
