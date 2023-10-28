from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from mycanvas import *
from mymodel import *

class MyWindow(QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100,100,600,400)
        self.setWindowTitle("MyGLDrawer")
        self.canvas = MyCanvas()
        self.setCentralWidget(self.canvas)
        #create a model object and pass to canvas
        self.model = MyModel()
        self.canvas.setModel(self.model)
        #create a toolbar
        tb = self.addToolBar("File")
        tb2 = self.addToolBar("Tools")
        fit = QAction(QIcon("fit.png"), "fit", self)
        bezier = QAction(QIcon("bezier.png"), "bezier", self)
        line = QAction(QIcon("line.png"), "line", self)
        reset = QAction(QIcon("reset.png"), "reset", self)
        granularitylabel = QLabel("Granularity:")
        #toolbar primaria
        tb.addAction(fit)
        tb.addAction(reset)
        #toolbar de ferramentas
        tb2.addAction(line)
        tb2.addAction(bezier)
        tb2.addWidget(granularitylabel)
        self.granularitySpinBox = QSpinBox(self)
        self.granularitySpinBox.setValue(50)
        self.granularitySpinBox.setMaximum(100)
        tb2.addWidget(self.granularitySpinBox)
        #definindo triggers
        tb.actionTriggered[QAction].connect(self.tbpressed)
        tb2.actionTriggered[QAction].connect(self.tbpressed)
        self.granularitySpinBox.valueChanged.connect(self.setGranularity)
    
    #função que detecta e executa actions das toolbars
    def tbpressed(self, a):
        if a.text() == "fit":
            self.canvas.fitWorldToViewport()
        if a.text() == "line":
            self.canvas.mode = 0
            self.canvas.beziercount = 0
            print('mode', self.canvas.mode, sep=' ')
        if a.text() == "bezier":
            self.canvas.mode = 1
            self.canvas.linecount = 0
            print('mode', self.canvas.mode, sep=' ')
        if a.text() == "reset":
            self.canvas.resetCanvas()
            print('reset')

    #função que ajusta a granularidade de acordo com a atualização do elemento
    def setGranularity(self):
        value = self.granularitySpinBox.value()
        print("granularity: ", value, sep="")
        self.canvas.granularity = value
        