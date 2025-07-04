from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtGui import QTextDocument
from qgis.core import QgsTextAnnotation
from qgis.gui import QgsMapCanvasAnnotationItem
from PyQt5.QtCore import QSizeF
from qgis.core import QgsDistanceArea
from qgis.core import QgsProject

class DistanceDisplayController(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.text_item = None
        self.canvas.viewport().installEventFilter(self)

        self.distance_calculator = QgsDistanceArea()
        self.distance_calculator.setEllipsoid(QgsProject.instance().ellipsoid())
        print(QgsProject.instance().ellipsoid())
        self.distance_calculator.setSourceCrs(self.canvas.mapSettings().destinationCrs(),QgsProject.instance().transformContext())

    def eventFilter(self, obj, event):
        if obj == self.canvas.viewport() and event.type() == QEvent.MouseMove:
            self.on_mouse_move(event)
        return super().eventFilter(obj, event)

    def on_mouse_move(self, event):
        tool = self.canvas.mapTool()
        if not tool:
            self.clear_annotation()
            return

        if hasattr(tool, 'points') and callable(tool.points):
            pts = tool.points()
        elif hasattr(tool, 'vertexPoints') and callable(tool.vertexPoints):
            pts = tool.vertexPoints()
        else:
            self.clear_annotation()
            return

        if not pts:
            self.clear_annotation()
            return

        last_point = pts[-1]
        mouse_point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        distance = self.distance_calculator.measureLine(last_point, mouse_point)

        self.show_distance(distance, mouse_point)

    def show_distance(self, distance, position):
        self.clear_annotation()

        annotation = QgsTextAnnotation()
        annotation.setMapPosition(position)
        annotation.setFrameSize(QSizeF(140, 40))
        html_text = f"""
        <div style="
            background-color: rgba(30, 30, 30, 0.8);
            color: #fff;
            font-weight: bold;
            font-size: 14px;
            border-radius: 8px;
            padding: 6px 12px;
            box-shadow: 3px 3px 8px rgba(0,0,0,0.5);
            ">
            Distance: <span style="color:#4CAF50;">{distance:.2f} m</span>
        </div>
        """

        doc = QTextDocument()
        doc.setHtml(html_text)
        annotation.setDocument(doc)

        self.text_item = QgsMapCanvasAnnotationItem(annotation, self.canvas)
        self.text_item.setZValue(1000)

    def clear_annotation(self):
        if self.text_item:
            self.canvas.scene().removeItem(self.text_item)
            self.text_item = None

    def cleanup(self):
        self.clear_annotation()
        self.canvas.viewport().removeEventFilter(self)
