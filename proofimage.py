#!/usr/bin/python

import lldb
import fblldbbase as fb

def lldbcommands():
  return [ PrintKeyWindowLevel() ]
  
class PrintKeyWindowLevel(fb.FBCommand):
  def name(self):
    return 'proofimage'
    
  def description(self):
    return 'Display an image saved on your local hard drive as fullscreen overlay'

  def args(self):
    return [
      fb.FBCommandArgument(arg='image path', type='string', help='path to the image to be loaded from your local hard drive'),
    ]
    
  def run(self, arguments, options):
    # It's a good habit to explicitly cast the type of all return
    # values and arguments. LLDB can't always find them on its own.

    imagePath = str(arguments[0])
    imageBytes = open(imagePath, mode='rb').read()
    imageBytesLength = len(imageBytes)
    if not (imageBytes or imageBytesLength):
      print 'Could not load image.'
      return

    fb.evaluateExpression("unsigned char $rawProofImageBuffer[%i]" % imageBytesLength)
    imageBufferStartingAddress = fb.evaluateExpression('(void *)$rawProofImageBuffer')
    address = int(imageBufferStartingAddress, 16)

    process = lldb.debugger.GetSelectedTarget().GetProcess()
    error = lldb.SBError()
    numberOfWrittenBytes = process.WriteMemory(address, imageBytes, error)
    if not error.Success() or numberOfWrittenBytes != imageBytesLength:
      print('Transferring image to process memory failed!')
      return
    
    window = fb.evaluateObjectExpression('[(id)[UIApplication sharedApplication] keyWindow]')

    imageViewCommand = '(UIImageView *)[[UIImageView alloc] initWithImage:(UIImage*)[UIImage imageWithData:(NSData *)[NSData dataWithBytes:$rawProofImageBuffer length:' + str(imageBytesLength) + ']]]'
    imageViewAddress = fb.evaluateObjectExpression(imageViewCommand)
    fb.evaluateEffect('[' + imageViewAddress + ' setAlpha:0.5]')
    fb.evaluateEffect('[' + imageViewAddress + ' setContentMode:1]') # UIViewContentModeScaleAspectFit
    fb.evaluateEffect('[' + imageViewAddress + ' setFrame:(CGRect)[(id)' + window + ' bounds]]')

    fb.evaluateObjectExpression('[' + window + ' addSubview:' + imageViewAddress + ']')
    lldb.debugger.HandleCommand('caflush')

    print "UIImageView address {}".format(imageViewAddress)
