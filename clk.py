import time

# an object used to emulate the clock on a processor. every
# cycle is 1 ms, i.e. the frequency of this processor is 1 MHz.

class clk:

    def __init__(self):
        # variable that keeps track of the number of cycles this 
        # clock has emulated - this will be used later in comparing
        # the performance of the pipelined and non-pipelined processor
        self.cycles = 0

    def cycle(self):
        # function to execute one clock cycle. it is not a realistic function,
        # but it adds a delay of one millisecond
        time.sleep(0.001)
        self.cycles += 1

    def noOfCycles(self):
        # returns the number of cycles this clock has emulated
        return self.cycles