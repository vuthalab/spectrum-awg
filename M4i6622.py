#
# **************************************************************************
#
# 
#
# **************************************************************************
#



from pyspcm import *
from spcm_tools import *
import math
import numpy as np
import time
from Functions.functions import *




class M4i6622:
    def __init__(self, address=b'/dev/spcm0',channelNum = 4,sampleRate=625,referenceClock=False, referenceClockFrequency = 10000000, clockOut = False):
        '''
        address: location of the card on the computer, default is /dev/spcm0
        channelNum: Number of channels used on the card, default is 4
        sampleRate: Sample Rate in Mega Samples per second (MS/s) default is 625, the maximum for an M4i.66xx card
        referenceClock: Presence of a reference clock, by default is False
        referenceClockFrequency: Frequency of the reference clock (in Hz), by default is 10 MHz.
        clockOut: If you want a clock output from the M4i. By default is False.

        Reference clock frequencies can only go from 10 MHz to 1.25GHz, but cannot be between 750 to 757 MHz and 1125 to 1145 MHz 
        '''
        
        #Connect the Card
        self.hCard = spcm_hOpen (create_string_buffer (address))
        


        self.lSetChannels = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_CHCOUNT, byref (self.lSetChannels))

        self.lBytesPerSample = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (self.lBytesPerSample))


        #Read the Card Type, it's function and Serial Number
        self.lCardType = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_PCITYP, byref (self.lCardType))
        self.lSerialNumber = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_PCISERIALNO, byref (self.lSerialNumber))
        self.lFncType = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_FNCTYPE, byref (self.lFncType))


        #Check if the card itself is valid
        Valid = self.checkCard()
        if Valid == False:
            exit()

        #Configure the reference clock (if required)
        if referenceClock == True:
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKMODE, SPC_CM_EXTREFCLOCK); # Set to reference clock mode
            spcm_dwSetParam_i32 (self.hCard, SPC_REFERENCECLOCK, referenceClockFrequency); # Reference clock that is fed in at the Clock Frequency
            if self.checkExternalClock() == True:
                print("Clock has been set\n")
            else:
                print("External Clock not found, please check connection to external clock or set referenceClock to False.\n")
                spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKMODE, SPC_CM_INTPLL) # Enables internal programmable quartz 1
        else:
            print("Using internal clock\n")



        #Set the Sample Rate
        self.SampleRate = MEGA(sampleRate)
        if ((self.lCardType.value & TYP_SERIESMASK) == TYP_M4IEXPSERIES) or ((self.lCardType.value & TYP_SERIESMASK) == TYP_M4XEXPSERIES):
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, self.SampleRate)
            print("Sample Rate has been set.\n")
        else:
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(1))
            print("ERROR: Sample Rate failed to be set. Make sure that the sample rate is under 625 Mega Samples/s and is an integer number\n")


        #Set the clock output
        if clockOut == True:
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKOUT,   1)
            print("Clock Output On.\n")
        else: 
            spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKOUT,   0)
            print("Clock Output Off.\n")

        # setup the mode
        self.qwChEnable = uint64 (1)
        self.llMemSamples = int64 (KILO_B(1024*16))
        self.llLoops = int64 (0) # loop continuously

        #putting the card in Continous mode
        spcm_dwSetParam_i32 (self.hCard, SPC_CARDMODE,    SPC_REP_STD_CONTINUOUS)

        #activating all 4 channels (changing the way the output is read)
        spcm_dwSetParam_i64 (self.hCard, SPC_CHENABLE,    CHANNEL0 | CHANNEL1 | CHANNEL2 | CHANNEL3)

        #Getting the total memory size to know how long the buffer should be
        spcm_dwSetParam_i64 (self.hCard, SPC_MEMSIZE,     self.llMemSamples)

        #Setting up the infinite loop
        spcm_dwSetParam_i64 (self.hCard, SPC_LOOPS,       self.llLoops)


        #Setting up the channels.


        self.channelNum = channelNum
        if channelNum == 3:
            self.channelNum = 4 #Cannot have 3 channels, its either 1,2 or 4
        else:
            self.channelNum = channelNum



        channelEnable = [SPC_ENABLEOUT0,SPC_ENABLEOUT1,SPC_ENABLEOUT2,SPC_ENABLEOUT3]

        lChannelList = [int32 (0), int32 (0), int32 (0), int32 (0)]
        amplitudeList = [SPC_AMP0,SPC_AMP1,SPC_AMP2,SPC_AMP3]
        filterList = [SPC_FILTER0, SPC_FILTER1, SPC_FILTER2, SPC_FILTER3]






        #Getting total number of channels recognized by the software (4 in our case) and getting the amount of bytes per sample
        self.lSetChannels = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_CHCOUNT,     byref (self.lSetChannels))
        self.lBytesPerSample = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (self.lBytesPerSample))


        # setup the trigger mode
        # (SW trigger, no output)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ORMASK,      SPC_TMASK_SOFTWARE)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ANDMASK,     0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ORMASK0,  0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ORMASK1,  0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ANDMASK0, 0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ANDMASK1, 0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIGGEROUT,       0)

        spcm_dwSetParam_i64 (self.hCard, SPC_TRIG_DELAY,       0)



        for i in range(0, self.channelNum,1):
            spcm_dwSetParam_i64 (self.hCard, channelEnable[i],  1) #Enabling the channel
            spcm_dwSetParam_i32 (self.hCard, amplitudeList[i] + lChannelList[i].value * (SPC_AMP1 - SPC_AMP0), int32 (2500)) # Setting the max amplitude
            spcm_dwSetParam_i32 (self.hCard, filterList[i], int32(1)) #Turning on the channel's filter



        

    def checkExternalClock(self):
        '''
        Checks to see if the external clock is working.
        '''

        if spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER) == ERR_CLOCKNOTLOCKED:
            print("External clock not locked. Please check connection\n")
            return False
        else:
            print("External clock locked.\n")
            return True


    def checkCard(self):
        """
        Function that checks if the card used is indeed an M4i.6622-x8 or is compatible with Analog Output.
        """

        #Check if Card is connected
        if self.hCard == None:
            print("no card found...\n")
            return False

        #Getting the card Name to check if it's supported.
        try:

            sCardName = szTypeToName (self.lCardType.value)
            if self.lFncType.value == SPCM_TYPE_AO:
                print("Found: {0} sn {1:05d}\n".format(sCardName,self.lSerialNumber.value))
                return True
            else:
                print("Code is for an M4i.6622 Card.\nCard: {0} sn {1:05d} is not supported.\n".format(sCardName,lSerialNumber.value))
                return False

        except:
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)
            print(dwError)
            print("Problem occured, mb")


    def setSoftwareBuffer(self):
        """
        Function to set up the SoftwareBuffer, no arguments required.
        """
        # setup software buffer
        print(self.llMemSamples.value, self.lBytesPerSample.value, self.lSetChannels.value)
        self.qwBufferSize = uint64 (self.llMemSamples.value * self.lBytesPerSample.value * self.lSetChannels.value) # total size of the buffer

        # we try to use continuous memory if available and big enough
        self.pvBuffer = c_void_p ()
        self.qwContBufLen = uint64 (0)



    def setupCard(self,functionList):

        self.genBuffer(functionList)
        self.transferData()
        return 0

    def getMaxDataLength(self):

        return self.llMemSamples.value
    
    def genBuffer(self,functionList):

        
        val = self.getMaxDataLength()

        Y_vect = []
        functionNum = len(functionList)


        X = np.arange(0,(int)(val/self.channelNum),1)

        for i in range(0,self.channelNum,1):
            if i > functionNum -1:
                Y_vect = Y_vect + [np.zeros(len(X)).astype(int)]
            else:
                Y_vect = Y_vect + [functionList[i](X).astype(int)]

        self.buffer = np.column_stack(Y_vect).flatten()
        return 0


    def transferData(self):

        try:
            #Calculating the amount of samples that can be added to the buffer
            qwSamplePos = 0
        
            self.pvBuffer = np.zeros(self.qwBufferSize.value,dtype="uint16")
            
            self.pvBuffer[0:self.llMemSamples.value] = self.buffer
            self.trueBuffer = self.pvBuffer.tobytes()



            #Define the buffer for transfer and start the DMA transfer
            print("Starting the DMA transfer and waiting until data is in board memory\n")
            spcm_dwDefTransfer_i64 (self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, uint32(self.qwBufferSize.value), self.trueBuffer, uint64 (0), self.qwBufferSize)
            print("Finished initial transfer")
            spcm_dwSetParam_i32 (self.hCard, SPC_DATA_AVAIL_CARD_LEN, self.qwBufferSize)
            print("Got full data size")
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
            print("... data has been transferred to board memory\n")

            
            return 0
        except KeyboardInterrupt:
            #it is also possible to stop the process before a timeout using a keyboard interrupt (Contrl+C in Windows)
            print("Broken Operation")
            return -1
            exit()

    def startCard(self):

        # We'll start and wait until the card has finished or until a timeout occurs
        try:

            spcm_dwSetParam_i32 (self.hCard, SPC_TIMEOUT, 0)
            print("\nStarting the card and waiting for ready interrupt\n(continuous and single restart will have timeout)\n")
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER )#| M2CMD_CARD_WAITREADY)
            while True:
                time.sleep(1)

          
            #if dwError == ERR_TIMEOUT:
            #    print("timeout has elapsed")

        except KeyboardInterrupt:
            print("Process finished.")
            #it is also possible to stop the process before a timeout using a keyboard interrupt (Contrl+C in Windows)
            return -1


    def stop(self):
        """
        Command to stop the Card. To use card again, need to reinitialize 
        """
        #send the stop command
        try:
            
            
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_DATA_STOPDMA)
            print(dwError)
            print("Card has been Stopped")
            spcm_vClose (self.hCard)
            return 0
        except Exception as e:
            print("Exception",str(e), " has occured")
            return -1

