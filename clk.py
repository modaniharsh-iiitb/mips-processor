# an object used to emulate the clock on a processor
class clk:

    def __init__(self, cycleLength):
        # variable that keeps track of the number of cycles this 
        # clock has emulated - this will be used later in comparing
        # the performance of the pipelined and non-pipelined processor
        self.cycles = 0
        # length of cycle (differs in case of pipelined and non-pipelined 
        # processor)
        self.cycleLength = cycleLength
        self.timeTaken = 0

    def cycle(self):
        # function to execute one clock cycle. it is not a realistic function,
        # but it adds a delay of one millisecond
        self.timeTaken += self.cycleLength
        self.cycles += 1

    def noOfCycles(self):
        # returns the number of cycles this clock has emulated
        return self.cycles
    
    def getTimeTaken(self):
        # returns the time taken by the program (emulated)
        return self.timeTaken