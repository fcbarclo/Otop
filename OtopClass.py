# OtopClass

from DSdef import DSdef
from DSaccess import DSaccess
from DSwin import DSwin

#######################################################################################
#############################    O T O P   C L A S S    ###############################
#######################################################################################

class Otop(DSdef,DSaccess,DSwin):

        def __init__(self, logininfo):
                DSwin.__init__( self, logininfo)

        def Run(self):
                if self.VScrStatus < 0: # init screen error
                        self.End()
                        print self.screrrmsg
                else:
                        if self.Voracle_connect == -1: # db connect error
                                self.End()
                                print "DB connect error"
                        else:
                                self.WinOtopRun() # GO...


################################################
###############  END OTOP CLASS ################
################################################
