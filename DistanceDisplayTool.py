from PyQt5.QtCore import QObject, QEvent,QSizeF
from PyQt5.QtGui import QTextDocument
from qgis.core import QgsTextAnnotation, QgsDistanceArea,QgsProject ,QgsGeometry, QgsWkbTypes
from qgis.gui import QgsMapCanvasAnnotationItem

class DistanceDisplayController(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.text_item = None
        self.canvas.viewport().installEventFilter(self)

        self.distance_calculator = QgsDistanceArea()
        self.distance_calculator.setEllipsoid(QgsProject.instance().ellipsoid())
        self.distance_calculator.setSourceCrs(self.canvas.mapSettings().destinationCrs(), QgsProject.instance().transformContext())

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

        layer = self.iface.activeLayer()
        surface = None

        if layer and layer.geometryType() == QgsWkbTypes.PolygonGeometry and len(pts) >= 2:
            polygon_points = pts + [mouse_point]
            polygon_points.append(polygon_points[0])

            polygon_geom = QgsGeometry.fromPolygonXY([polygon_points])
            surface = self.distance_calculator.measureArea(polygon_geom)

        self.show_measurements(distance, surface, mouse_point)

    def show_measurements(self, distance, surface, position):
        self.clear_annotation()

        annotation = QgsTextAnnotation()
        annotation.setMapPosition(position)
        
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
            Distance: <span style="color:#4CAF50;">{distance:.2f} m</span>"""

        if surface is not None:
            html_text += f"""<br/>
            Surface: <span style="color:#2196F3;">{surface:.2f} m²</span>"""

        html_text += "</div>"

        doc = QTextDocument()
        doc.setHtml(html_text)
        annotation.setDocument(doc)

        if surface is not None:
            annotation.setFrameSize(QSizeF(160, 60)) 
        else:
            annotation.setFrameSize(QSizeF(160, 35))  
        self.text_item = QgsMapCanvasAnnotationItem(annotation, self.canvas)
        self.text_item.setZValue(1000)

    def clear_annotation(self):
        if self.text_item:
            self.canvas.scene().removeItem(self.text_item)
            self.text_item = None

    def cleanup(self):
        self.clear_annotation()
        self.canvas.viewport().removeEventFilter(self)
