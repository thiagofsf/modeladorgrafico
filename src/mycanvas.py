from PyQt5 import QtOpenGL
from PyQt5.QtWidgets import *
from OpenGL.GL import *
from PyQt5 import QtCore

from hetool.include.hetool import HeController
from hetool.include.hetool import HeModel
from hetool.geometry.segments.polyline import Polyline
from geometry.point import Point
from hetool.compgeom.tesselation import Tesselation

class MyCanvas(QtOpenGL.QGLWidget):

    def __init__(self):
        super(MyCanvas, self).__init__()
        self.m_model = None
        self.m_hmodel = HeModel()
        self.m_controller = HeController(self.m_hmodel)
        self.m_w = 0 #width: GL canvas horizontal size
        self.m_h = 0 #height: GL canvas vertical size
        self.m_L = -1000.0
        self.m_R = 1000.0
        self.m_B = -1000.0
        self.m_T = 1000.0
        self.list = None
        self.m_buttonPressed = False
        self.m_pt0 = QtCore.QPointF(0.0,0.0)
        self.m_pt1 = QtCore.QPointF(0.0,0.0)
        self.m_pt2 = QtCore.QPointF(0.0,0.0)

        self.mode = 0    #0 para nenhuma ferramenta, 1 para linha, 2 para bezier
        self.granularity = 50
        #variaveis que controlam coleta de pontos
        self.pointcount = 0

        #Controla se houve movimento para iniciar tracking do desenho
        self.moved =  False

        #self.cont = 0    #variavel usada para contar quantas vezes paintGL foi executado (usada para resolver um bug que deixava varias linhas desenhadas ao redimensionar a janela)

        #vamos rastrear o mouse independente de haver clique (press event)
        self.setMouseTracking(True)
    
    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_LINE_SMOOTH)
        self.list = glGenLists(1)
    
    def resizeGL(self, _width, _height):
        #store GL canvas sizes in object properties
        self.m_w = _width
        self.m_h = _height
        
        if(self.m_hmodel == None) or (self.m_hmodel.isEmpty()): self.scaleWorldWindow(1.0)
        else:
            self.m_L, self.m_R, self.m_B, self.m_T = self.m_hmodel.getBoundBox()
            self.scaleWorldWindow(1.1)

        #setup the viewport to canvas dimensions
        glViewport(0, 0, self.m_w, self.m_h)
        #reset the cordinate system
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        #Establish the clipping colume by setting up an orthographic projection
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        #setup display in model cordinates
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def paintGL(self):
        
        #limpando buffer para evitar bug de linhas antigas no redimensionamento
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        #Desenhando previsualização das ferramentas
        glCallList(self.list)
        glDeleteLists(self.list, 1)
        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)
        glColor3f(1.0, 0.0, 0.0)
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0x00FF)
        glBegin(GL_LINE_STRIP)
        #Gerando visualização da ferramenta line
        #checamos se o primeiro ponto foi coletado (pointcount==1), caso sim, atualizamos conforme movimento do mouse para desenhar
        if(self.mode == 1 and self.pointcount == 1):
            pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
            pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
            glVertex2f(pt0_U.x(), pt0_U.y())
            glVertex2f(pt1_U.x(), pt1_U.y())
        #Gerando Visualização da ferramenta Bézier
        #Checamos se há primeiro ponto coletado, se sim, desenhar linhas entre pontos de controle pt0 e pt1
        elif(self.mode == 2 and self.pointcount == 1):
            pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
            pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
            glVertex2f(pt0_U.x(), pt0_U.y())
            glVertex2f(pt1_U.x(), pt1_U.y())
        #caso estejamos coletando o pt2, desenhar entre pt0, pt1 e pt2
        elif(self.mode == 2 and self.pointcount == 2):
            pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
            pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
            pt2_U = self.convertPtCoordsToUniverse(self.m_pt2)
            glVertex2f(pt0_U.x(), pt0_U.y())
            glVertex2f(pt1_U.x(), pt1_U.y())
            glVertex2f(pt2_U.x(), pt2_U.y())
        glEnd()
        glDisable(GL_LINE_STIPPLE)
        glEndList()
        
        #gerando visualização das linhas coletadas e preenchimento
        if not(self.m_hmodel.isEmpty()):
            patches = self.m_hmodel.getPatches()
            for pat in patches:
                pts = pat.getPoints()
                triangs = Tesselation.tessellate(pts)
                for j in range(0, len(triangs)):
                    #print("ponto [", j, "] [0]: ", triangs[j][0].getX(), sep="")
                    glColor3f(1.0, 0.0, 1.0)
                    glBegin(GL_TRIANGLES)
                    glVertex2d(triangs[j][0].getX(), triangs[j][0].getY())
                    glVertex2d(triangs[j][1].getX(), triangs[j][1].getY())
                    glVertex2d(triangs[j][2].getX(), triangs[j][2].getY())
                    '''
                    glVertex2d(pts[triangs[j][0]].getX(), pts[triangs[j][0]].getY())
                    glVertex2d(pts[triangs[j][1]].getX(), pts[triangs[j][1]].getY())
                    glVertex2d(pts[triangs[j][2]].getX(), pts[triangs[j][2]].getY())
                    '''
                    glEnd()
            segments = self.m_hmodel.getSegments()
            for curv in segments:
                ptc = curv.getPointsToDraw()
                glColor3f(0.0,0.0,0.0)
                glBegin(GL_LINE_STRIP)
                for point in ptc:
                    glVertex2f(point.getX(), point.getY())
                glEnd()
    
    def setModel(self, _model):
        self.m_model = _model
    
    def fitWorldToViewport(self):
        #print("fitWorldToViewport")
        if self.m_hmodel == None:
            return
        self.m_L, self.m_R, self.m_B, self.m_T = self.m_hmodel.getBoundBox()
        self.scaleWorldWindow(1.10)
        self.update()
        self.repaint()
    
    def scaleWorldWindow(self, _scaleFac):
        #compute canvas viewport distortion ratio.
        vpr = self.m_h / self.m_w
        #get current window center
        cx = (self.m_L + self.m_R) / 2.0
        cy = (self.m_B + self.m_T) / 2.0
        #set new window sizes based on scaling factor
        sizex = (self.m_R - self.m_L) * _scaleFac
        sizey = (self.m_T - self.m_B) * _scaleFac
        #Adjust window to keep the same aspect ratio of the viewport
        if sizey > (vpr*sizex):
            sizex = sizey / vpr
        else:
            sizey = sizex * vpr
        self.m_L = cx - (sizex * 0.5)
        self.m_R = cx + (sizex * 0.5)
        self.m_B = cy - (sizey * 0.5)
        self.m_T = cy + (sizey * 0.5)
        #Establish the clipping volume by setting up an
        #orthographic projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
    
    def panWorldWindow(self, _panFacX, _panFacY):
        #compute pan distances in horizontal and vertical directions
        panX = (self.m_R - self.m_L) * _panFacX
        panY = (self.m_T - self.m_B) * _panFacY
        #shift current window
        self.m_L += panX
        self.m_R += panX
        self.m_B += panY
        self.m_T += panY
        #Establish the clipping volume by setting up an
        #orthographic projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
    
    def convertPtCoordsToUniverse(self, _pt):
        dX = self.m_R - self.m_L
        dY = self.m_T - self.m_B
        mX = _pt.x() * dX / self.m_w
        mY = (self.m_h - _pt.y()) * dY / self.m_h
        x = self.m_L + mX
        y = self.m_B + mY
        return QtCore.QPointF(x,y)

    #a forma de coleta da linha foi alterado para coletagem on release, assim, apenas setamos como true que o botão foi pressionado
    def mousePressEvent(self, event):
        self.m_buttonPressed = True

    #na inicialização definimos para sempre rastrear o mouse, assim, conseguimos definir os pontos para linha guia interativamente
    def mouseMoveEvent(self, event):
        #coletando retas se mode == 0
        if(self.mode == 1):
            if(self.pointcount == 1):
                self.m_pt1 = event.pos()
                self.update()
        #coletando retas se mode ==1
        elif(self.mode == 2):
            #se o contador da bezier está em 1 o primeiro ponto foi coletado
            #atualizar posição do ponto 2 pra previa
            if(self.pointcount == 1):
                self.m_pt1 = event.pos()
                self.update()
            if(self.pointcount == 2):
                self.m_pt2 = event.pos()
                self.update()

    #toda a coleta se dará no evento (mouserelease)
    def mouseReleaseEvent(self, event):
        
        #coletando retas (modo 1)
        if(self.mode == 1):
            #checamos se algum ponto foi coletado, se não coletamos o primeiro ponto e atualizamos o atributo
            if(self.pointcount == 0):
                self.m_pt0 = event.pos()
                self.m_pt1 = event.pos() #definimos o ponto 1 provisoriamente como o mesmo para tracking dinamico da linha guia, evita aparecerem linhas com pontos antigos
                self.pointcount+=1
                
            #se o primeiro ponto foi coletado, coletamos o segundo ponto e adicionamos o segmento ao model
            elif(self.pointcount == 1):
                self.m_pt1 = event.pos()
                #fim da coleta, adicionar segmento
                self.pointcount=0 #resetando contagem de pontos para proxima coleta
                pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
                pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
                segment = Polyline()
                segment.addPoint(pt0_U.x(), pt0_U.y())
                segment.addPoint(pt1_U.x(), pt1_U.y())
                #tratamento de exceção para o erro divisão por zero da biblioteca ao inserir
                try:
                    self.m_controller.addSegment(segment, 0)
                    print("Segmento Adicionado")
                    print("[p1: ", pt0_U.x(), ", ", pt0_U.y()," ] [p2: ",pt1_U.x(),", ", pt1_U.y()," ]", sep="")
                except:
                    print("Erro ao inserir segmento")
                    print("[p1: ", pt0_U.x(), ", ", pt0_U.y()," ] [p2: ",pt1_U.x(),", ", pt1_U.y()," ]", sep="")
                #self.update()
                #self.repaint()
                #resetando pontos no fim
                self.m_pt0 = QtCore.QPointF(0.0,0.0)
                self.m_pt1 = QtCore.QPointF(0.0,0.0)
                self.m_pt2 = QtCore.QPointF(0.0,0.0)
            #botão foi solto (release)
            self.m_buttonPressed = False

        #coletando as curvas bezier quadráticas (modo 2)    
        elif(self.mode == 2):
            #checamos se algum ponto foi coletado, se não coletamos o primeiro ponto e atualizamos o atributo
            if(self.pointcount == 0):
                self.m_pt0 = event.pos()
                self.m_pt1 = event.pos() #definindo ponto para linhas guias interativas
                self.pointcount+=1
                #self.update()
                #self.repaint()
            #Se um ponto foi coletado, vamos coletar o segundo ponto e atualizar o atributo
            elif(self.pointcount == 1):
                self.m_pt1 = event.pos()
                self.m_pt2 = event.pos() #definindo ponto para linhas guias interativas
                self.pointcount+=1
                #self.update()
                #self.repaint()
            #se o segundo ponto foi coletado, vamos coletar o terceiro e ultimo ponto, adicionar segmento no model e resetar o atributo beziercount
            elif(self.pointcount == 2):
                self.m_pt2 = event.pos()
                #fim da coleta, adicionar segmento
                self.pointcount = 0 #resetando atributo
                #convertendo pontos
                pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
                pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
                pt2_U = self.convertPtCoordsToUniverse(self.m_pt2)
                #criando o segmento
                segment = Polyline()
                #adicionando primeiro ponto do segmento
                segment.addPoint(pt0_U.x(), pt0_U.y())
                #loop para encontrar as coordenadas x e y usando a formula para calculos de bezier quadratica com paretro t
                #B(t) = (1-t)²P0 + 2t(1-t)P1 + t²P2
                #a variável self.granularity controla a granularidade do loop
                print("coletando bezier com granularidade ", self.granularity, sep="")
                for t in range(0, self.granularity):
                    t = t/self.granularity
                    x = (1-t)**2*pt0_U.x() + 2*t*(1-t)*pt1_U.x() + t**2*pt2_U.x()
                    y = (1-t)**2*pt0_U.y() + 2*t*(1-t)*pt1_U.y() + t**2*pt2_U.y()
                    #para cada novo ponto calculado, adicionar ao segmento
                    segment.addPoint(x,y)
                #após o fim do calculo dos pontos inserimos o segmento na lista
                #tratamento de exceção para o erro divisão por zero da biblioteca ao inserir
                try:
                    self.m_controller.addSegment(segment, 0)
                    print("Segmento Adicionado")
                    print("[p1: ", pt0_U.x(), ", ", pt0_U.y()," ] [p2: ",pt1_U.x(),", ", pt1_U.y()," ] [p3: ",pt2_U.x(),", ", pt2_U.y()," ]", sep="")
                except:
                    print("erro ao inserir segmento")
                    print("[p1: ", pt0_U.x(), ", ", pt0_U.y()," ] [p2: ",pt1_U.x(),", ", pt1_U.y()," ] [p3: ",pt2_U.x(),", ", pt2_U.y()," ]", sep="")
                #self.update()
                #self.repaint()
                #resetando pontos no fim
                self.m_pt0 = QtCore.QPointF(0.0,0.0)
                self.m_pt1 = QtCore.QPointF(0.0,0.0)
                self.m_pt2 = QtCore.QPointF(0.0,0.0)
            #botão foi solto (release)
            self.m_buttonPressed = False
        self.update()
        self.repaint()
        
    #função que limpa o canvas removendo todos os segmentos da tela
    def resetCanvas(self):
        self.m_hmodel.clearAll()
        self.update()
        self.repaint()
                
            
        