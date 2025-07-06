import unittest
from unittest.mock import MagicMock, patch
from qgis.core import QgsPointXY, QgsProject
from PyQt5.QtCore import QPoint
from DistanceDisplayTool import DistanceDisplayController

class TestDistanceDisplayController(unittest.TestCase):

    def setUp(self):
        self.iface = MagicMock()
        self.canvas = MagicMock()
        self.iface.mapCanvas.return_value = self.canvas

        self.canvas.mapSettings.return_value.destinationCrs.return_value = QgsProject.instance().crs()
        self.canvas.mapSettings.return_value.destinationCrs = MagicMock(return_value=QgsProject.instance().crs())
        self.canvas.mapSettings.return_value.mapToPixel.return_value = None

        self.canvas.viewport.return_value.installEventFilter = MagicMock()
        self.canvas.getCoordinateTransform.return_value.toMapCoordinates = MagicMock(return_value=QgsPointXY(1, 1))

        self.controller = DistanceDisplayController(self.iface)

    @patch('DistanceDisplayTool.QgsMapCanvasAnnotationItem')
    def test_distance_calculation(self, mock_annotation_item):
        tool = MagicMock()
        tool.points.return_value = [QgsPointXY(0, 0)]
        self.canvas.mapTool.return_value = tool

        mock_event = MagicMock()
        mock_event.type.return_value = 2  
        mock_event.pos.return_value = QPoint(10, 10)

        self.controller.on_mouse_move(mock_event)

        self.assertIsNotNone(self.controller.text_item)
        mock_annotation_item.assert_called_once()


    def test_no_tool(self):
        self.canvas.mapTool.return_value = None
        mock_event = MagicMock()
        mock_event.type.return_value = 2
        self.controller.on_mouse_move(mock_event)
        self.assertIsNone(self.controller.text_item)

    def tearDown(self):
        self.controller.cleanup()

if __name__ == '__main__':
    unittest.main()
