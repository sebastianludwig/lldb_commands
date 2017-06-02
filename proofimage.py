#!/usr/bin/python

import lldb
import fblldbbase as fb
import random
import string

def lldbcommands():
  return [ ProofImage() ]
  
class ProofImage(fb.FBCommand):
  _imageViewVarName = None

  def name(self):
    return 'proofimage'
    
  def description(self):
    return 'Display an image saved on your local hard drive as fullscreen overlay'

  def args(self):
    return [
      fb.FBCommandArgument(arg='image path or action', type='string', help='path to the image to be loaded from your local hard drive OR `show`, `hide` or `remove`.'),
    ]
    
  def run(self, arguments, options):
    # It's a good habit to explicitly cast the type of all return
    # values and arguments. LLDB can't always find them on its own.
    argument = str(arguments[0])
    if argument == 'show':
      self._setHidden(False)
    elif argument == 'hide':
      self._setHidden(True)
    elif argument == 'remove':
      self._remove()
    else:
      self._loadImage(argument)
  
  def _setHidden(self, hidden):
    if ProofImage._imageViewVarName is None:
      print "There is no proofing image."
      return

    if hidden:
      fb.evaluateEffect('[' + ProofImage._imageViewVarName + ' setHidden:YES]')
    else:
      fb.evaluateEffect('[' + ProofImage._imageViewVarName + ' setHidden:NO]')
    lldb.debugger.HandleCommand('caflush')

  def _remove(self):
    if ProofImage._imageViewVarName is None:
      print "There is no proofing image."
      return

    fb.evaluateEffect('[' + ProofImage._imageViewVarName + ' removeFromSuperview]')
    lldb.debugger.HandleCommand('caflush')

  def _randomVarName(self):
    return '$' + ''.join(random.choice(string.ascii_uppercase) for _ in range(10))

  def _loadImage(self, imagePath):
    imageBytes = open(imagePath, mode='rb').read()
    imageBytesLength = len(imageBytes)
    if not (imageBytes or imageBytesLength):
      print 'Could not load image.'
      return

    bufferVarName = self._randomVarName()

    fb.evaluateExpression("unsigned char %s[%i]" % (bufferVarName, imageBytesLength))
    imageBufferStartingAddress = fb.evaluateExpression('(void *)' + bufferVarName)

    process = lldb.debugger.GetSelectedTarget().GetProcess()
    error = lldb.SBError()
    numberOfWrittenBytes = process.WriteMemory(int(imageBufferStartingAddress, 16), imageBytes, error)
    if not error.Success() or numberOfWrittenBytes != imageBytesLength:
      print('Transferring image to process memory failed!')
      return
    
    window = fb.evaluateObjectExpression('[(id)[UIApplication sharedApplication] keyWindow]')

    imageView = self._randomVarName()
    imageViewCommand = 'UIImageView *' + imageView + ' = (UIImageView *)[[UIImageView alloc] initWithImage:(UIImage*)[UIImage imageWithData:(NSData *)[NSData dataWithBytes:' + bufferVarName + ' length:' + str(imageBytesLength) + ']]]'
    fb.evaluateExpression(imageViewCommand)
    fb.evaluateEffect('[' + imageView + ' setAlpha:0.3]')
    fb.evaluateEffect('[' + imageView + ' setContentMode:1]') # UIViewContentModeScaleAspectFit
    fb.evaluateEffect('[' + imageView + ' setFrame:(CGRect)[(id)' + window + ' bounds]]')

    fb.evaluateObjectExpression('[' + window + ' addSubview:' + imageView + ']')
    lldb.debugger.HandleCommand('caflush')

    imageViewAddress = fb.evaluateObjectExpression(imageView)
    print "UIImageView address {}".format(imageViewAddress)
    ProofImage._imageViewVarName = imageView
