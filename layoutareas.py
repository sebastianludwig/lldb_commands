#!/usr/bin/python

import lldb
import fblldbbase as fb
import fblldbviewhelpers as viewHelpers

def lldbcommands():
  return [ 
    InsetHighlightCommand(
      name='hsafearea',
      description='Highlight the safe area insets of a given view',
      help='The view whose safe area to highlight',
      selector='safeAreaInsets',
      defaultColor='red'
    ),
    InsetUnHighlightCommand(
      name='unhsafearea',
      description='Remove the safe area inset highlight on a view',
      help='The view whose safe area highlight will be removed',
      selector='safeAreaInsets'
    ),
    InsetHighlightCommand(
      name='hlayoutmargins',
      description='Highlight the layout margins of a given view',
      help='The view whose layout margins to highlighted',
      selector='layoutMargins',
      defaultColor='blue'
    ),
    InsetUnHighlightCommand(
      name='unhlayoutmargins',
      description='Remove the layout margin highlight on a view',
      help='The view whose layout margin highlight will be removed',
      selector='layoutMargins'
    ),
  ]

def _createLayer(x, y, width, height, color, alpha, name):
  layer = fb.evaluateExpression('(id)[CALayer new]')
  rectExpr = '(CGRect){{%s, %s}, {%s, %s}}' % (str(x),
                                               str(y),
                                               str(width),
                                               str(height)
                                               )

  fb.evaluateEffect('[%s setBackgroundColor:[UIColor %sColor].CGColor]' % (layer, color))
  fb.evaluateEffect('[(CALayer *)%s setOpacity:(CGFloat)%f]' % (layer, alpha))
  fb.evaluateEffect('[%s setFrame:%s]' % (layer, rectExpr))
  fb.evaluateEffect('[(CALayer *)%s setName:"%s"]' % (layer, name))

  return layer

def _highlightInsets(view, insets, color, alpha, name):
  _unhighlightInsets(view, name)

  view_size = fb.evaluateExpressionValue('(CGSize)((CGRect)[(id)%s frame]).size' % view)
  view_width = float(view_size.GetChildMemberWithName('width').GetValue())
  view_height = float(view_size.GetChildMemberWithName('height').GetValue())

  inset_left = float(insets.GetChildMemberWithName('left').GetValue())
  inset_right = float(insets.GetChildMemberWithName('right').GetValue())
  inset_top = float(insets.GetChildMemberWithName('top').GetValue())
  inset_bottom = float(insets.GetChildMemberWithName('bottom').GetValue())

  left = _createLayer(0, 0, inset_left, view_height, color, alpha, name)
  right = _createLayer(view_width - inset_right, 0, inset_right, view_height, color, alpha, name)
  top = _createLayer(inset_left, 0, view_width - inset_left - inset_right, inset_top, color, alpha, name)
  bottom = _createLayer(inset_left, view_height - inset_bottom, view_width - inset_left - inset_right, inset_bottom, color, alpha, name)

  fb.evaluateEffect('[[%s layer] addSublayer:%s]' % (view, left))
  fb.evaluateEffect('[[%s layer] addSublayer:%s]' % (view, right))
  fb.evaluateEffect('[[%s layer] addSublayer:%s]' % (view, top))
  fb.evaluateEffect('[[%s layer] addSublayer:%s]' % (view, bottom))

  lldb.debugger.HandleCommand('caflush')

def _unhighlightInsets(view, name):
  sublayers = fb.evaluateExpression('(id)[(id)[%s layer] sublayers]' % view)
  count = int(fb.evaluateExpression('(int)[(id)%s count]' % sublayers))
  for i in reversed(range(0, count)):
    sublayer = fb.evaluateExpression('(CALayer *)[%s objectAtIndex:%i]' % (sublayers, i))
    if fb.evaluateBooleanExpression('[(NSString *)[(CALayer *)%s name] isEqual:@"%s"]' % (sublayer, name)):
      fb.evaluateEffect('(void)[%s removeFromSuperlayer]' % sublayer)

  lldb.debugger.HandleCommand('caflush')


class InsetHighlightCommand(fb.FBCommand):
  colors = [
    "black",
    "gray",
    "red",
    "green",
    "blue",
    "cyan",
    "yellow",
    "magenta",
    "orange",
    "purple",
    "brown",
  ]

  def __init__(self, name, description, help, selector, defaultColor):
    self._name = name
    self._description = description
    self._help = help
    self._selector = selector
    self._defaultColor = defaultColor

  def name(self):
    return self._name

  def description(self):
    return self._description

  def args(self):
    return [
      fb.FBCommandArgument(arg='view', type='UIView *', help=self._help)
    ]

  def options(self):
    return [
      fb.FBCommandArgument(short='-c', long='--color', arg='color', type='string', default=self._defaultColor, help='A color name such as \'red\', \'green\', \'magenta\', etc.'),
      fb.FBCommandArgument(short='-a', long='--alpha', arg='alpha', type='CGFloat', default=0.3, help='Alpha value of the highlight color'),
      fb.FBCommandArgument(short='-d', long='--depth', arg='depth', type='int', default=0, help='Number of levels of subviews highlight. Each level gets a different color beginning with the provided or default color')
    ]

  def run(self, args, options):
    color = options.color
    assert color in self.colors, "Color must be one of the following: {}".format(" ".join(self.colors))

    alpha = float(options.alpha)
    depth = int(options.depth)

    rootView = fb.evaluateInputExpression(args[0])

    prevLevel = 0
    for view, level in viewHelpers.subviewsOfView(rootView):
      if level > depth:
         break
      if prevLevel != level:
        color = self.colors[(self.colors.index(color)+1) % len(self.colors)]
        prevLevel = level
      
      insets = fb.evaluateExpressionValue('(UIEdgeInsets)[(id)%s %s]' % (view, self._selector))
      _highlightInsets(view, insets, color, alpha, '%s Highlight' % self._selector)


class InsetUnHighlightCommand(fb.FBCommand):
  def __init__(self, name, description, help, selector):
    self._name = name
    self._description = description
    self._help = help
    self._selector = selector

  def name(self):
    return self._name

  def description(self):
    return self._description

  def args(self):
    return [
      fb.FBCommandArgument(arg='view', type='UIView *', help=self._help),
    ]

  def options(self):
    return [
      fb.FBCommandArgument(short='-d', long='--depth', arg='depth', type='int', default=0, help='Number of levels of subviews where the highlight will be removed')
    ]

  def run(self, args, options):
    depth = int(options.depth)

    rootView = fb.evaluateInputExpression(args[0])

    for view, level in viewHelpers.subviewsOfView(rootView):
      _unhighlightInsets(view, '%s Highlight' % self._selector)
