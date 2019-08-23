import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from DVR_module import *
import os
from configuration_reader import read_file


class Edge(QGraphicsItem):
    """
    Class Edge for the edge object
    """
    Pi = math.pi
    TwoPi = 2.0 * Pi

    Type = QGraphicsItem.UserType + 2

    def __init__(self, source_node, dest_node):
        super(Edge, self).__init__()

        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.sourcePoint = QPointF()
        self.destPoint = QPointF()

        self.cost = 1
        self.is_active = True

        self.penColor = Qt.black
        self.selectionPolygon = QPolygonF()
        self.line = QLineF(self.sourcePoint, self.destPoint)

        self.source = source_node
        self.dest = dest_node
        self.source.add_edge(self)
        self.dest.add_edge(self)
        self.name = "Edge {} - {}".format(source_node.name, dest_node.name)
        self.adjust()

    def set_cost(self, cost):
        self.cost = cost

    def type(self):
        return Edge.Type

    def source_node(self):
        return self.source

    def set_source_node(self, node):
        self.source = node
        self.adjust()

    def dest_node(self):
        return self.dest

    def set_dest_node(self, node):
        self.dest = node
        self.adjust()

    def set_pen_color(self, color):
        self.penColor = color
        self.update()

    def adjust(self):
        if not self.source or not self.dest:
            return

        self.line = QLineF(self.mapFromItem(self.source, 0, 0),
                           self.mapFromItem(self.dest, 0, 0))

        self.prepareGeometryChange()

        self.sourcePoint = self.line.p1()
        self.destPoint = self.line.p2()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if self.isSelected():
                self.set_pen_color(Qt.red)
                print("selected", self.name)
            else:
                self.set_pen_color(Qt.black)
                print("not selected", self.name)

        return super(Edge, self).itemChange(change, value)

    @staticmethod
    def createSelectionPolygon(line):
        radAngle = line.angle() * math.pi / 180
        selectionOffset = 2
        dx = selectionOffset * math.sin(radAngle)
        dy = selectionOffset * math.cos(radAngle)
        offset1 = QPointF(dx, dy)
        offset2 = QPointF(-dx, -dy)
        vector = [line.p1() + offset1, line.p1() + offset2,
                  line.p2() + offset2, line.p2() + offset1]
        nPolygon = QPolygonF(vector)
        return nPolygon

    def boundingRect(self):
        if not self.source or not self.dest:
            return QRectF()

        extra = 1.0

        return QRectF(self.sourcePoint,
                      QSizeF(self.destPoint.x() - self.sourcePoint.x(),
                             self.destPoint.y() - self.sourcePoint.y())).normalized().adjusted(-extra, -extra, extra,
                                                                                               extra)

    def shape(self):
        ret = QPainterPath()
        self.selectionPolygon = self.createSelectionPolygon(self.line)
        ret.addPolygon(self.selectionPolygon)
        return ret

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        if self.line.length() == 0.0:
            return

        pen = QPen(Qt.black, 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen.setColor(self.penColor)
        painter.setPen(pen)
        painter.drawLine(self.line)

    def mousePressEvent(self, event):
        self.update()
        super(Edge, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super(Edge, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.source.graph.handle_double_click(self)
        print("double click edge")
        self.update()
        super(Edge, self).mouseDoubleClickEvent(event)


class Node(QGraphicsItem):
    """
    Class for Node object
    """
    Type = QGraphicsItem.UserType + 1

    def __init__(self, graph_widget, name="1"):
        super(Node, self).__init__()

        self.name = str(name)
        self.node_index = None
        self.graph = graph_widget
        self.newPos = QPointF()
        self.brush = QBrush(Qt.red)
        self.edge_list = []
        self.neighbor_nodes = []

        # The DVR object
        self.dvr = DVR(self)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)

    def get_node_attached(self, edge):
        """
        return the node attached to other end of the edge.
        :param edge: the Edge object
        :return: a Node object
        """
        if edge.source == self:
            return edge.dest
        return edge.source

    def type(self):
        return Node.Type

    def add_edge(self, edge):
        self.edge_list.append(edge)
        edge.adjust()
        attached_node = self.get_node_attached(edge)
        self.neighbor_nodes.append(attached_node)

    def remove_edge(self, edge):
        attached_node = self.get_node_attached(edge)
        self.edge_list.remove(edge)
        self.neighbor_nodes.remove(attached_node)

    def get_all_edges(self):
        return self.edge_list

    def get_edge_cost_between(self, node):
        """
        Get the cost of the edge between itself and the node
        :param node: the Node object
        :return: int value of the edge cost
        """
        if node == self:
            return 0
        try:
            index = self.neighbor_nodes.index(node)
            return self.edge_list[index].cost
        except:
            return None

    def advance(self):
        if self.newPos == self.pos():
            return False

        self.setPos(self.newPos)
        return True

    def boundingRect(self):
        adjust = 0.5
        return QRectF(-10 - adjust, -10 - adjust, 23 + adjust, 23 + adjust)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(-10, -10, 20, 20)
        return path

    def set_brush(self, brush):
        self.brush = brush
        self.update()

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(QPen(Qt.black, 0))
        painter.drawEllipse(-10, -10, 20, 20)
        painter.setPen(QPen(Qt.blue, 0))
        painter.drawText(QPointF(-5, 5), str(self.name))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edge_list:
                edge.adjust()
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if self.isSelected():
                self.set_brush(QBrush(Qt.black))
                print("selected", self.name)
            else:
                self.set_brush(QBrush(Qt.red))
                print("not selected", self.name)

        return super(Node, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super(Node, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super(Node, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.graph.handle_double_click(self)
        print("double click")
        print(self.node_index, self.dvr.node_table)
        self.update()
        super(Node, self).mouseDoubleClickEvent(event)


class GraphWidget(QGraphicsView):
    """
    The customized class to draw Node and Edge object on.
    """
    def __init__(self):
        super(GraphWidget, self).__init__()

        scene = QGraphicsScene(self)
        # scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-200, -200, 400, 400)
        self.setScene(scene)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self.double_selected_item = None
        self.num_nodes = 0
        self.num_edges = 0
        self.node_list = []
        self.edge_list = []
        self.network_graph = []

        node1 = Node(self, 1)
        node2 = Node(self, 2)
        node3 = Node(self, 3)
        node4 = Node(self, 4)
        self.centerNode = Node(self, 5)
        node6 = Node(self, 6)
        node7 = Node(self, 7)
        node8 = Node(self, 8)
        node9 = Node(self, 9)
        self.add_item(node1)
        self.add_item(node2)
        self.add_item(node3)
        # self.add_item(node4)
        # self.add_item(self.centerNode)
        # self.add_item(node6)
        # self.add_item(node7)
        # self.add_item(node8)
        # self.add_item(node9)
        self.add_item(Edge(node1, node3))
        self.add_item(Edge(node1, node2))
        self.add_item(Edge(node2, node3))
        # self.add_item(Edge(node2, self.centerNode))
        # self.add_item(Edge(node3, node6))
        # self.add_item(Edge(node4, node1))
        # self.add_item(Edge(node4, self.centerNode))
        # self.add_item(Edge(self.centerNode, node6))
        # self.add_item(Edge(self.centerNode, node8))
        # self.add_item(Edge(node6, node9))
        # self.add_item(Edge(node7, node4))
        # self.add_item(Edge(node8, node7))
        # self.add_item(Edge(node9, node8))

        node1.setPos(-50, -50)
        node2.setPos(0, -50)
        node3.setPos(50, -50)
        node4.setPos(-50, 0)
        self.centerNode.setPos(0, 0)
        node6.setPos(50, 0)
        node7.setPos(-50, 50)
        node8.setPos(0, 50)
        node9.setPos(50, 50)

        self.scale(0.8, 0.8)
        self.setMinimumSize(400, 400)
        self.setWindowTitle("Network")

    def add_item(self, item):
        """
        Add Node or Edge object to the GraphWidget
        :param item: Node or Edge object
        """
        scene = self.scene()
        if scene:
            if type(item) is Node:
                item.node_index = self.num_nodes
                self.num_nodes += 1
                item.name = str(self.num_nodes)
                self.node_list.append(item)
            elif type(item) is Edge:
                self.num_edges += 1
                self.edge_list.append(item)
            scene.addItem(item)

    def reset(self):
        """
        Clear all the item and setting
        """
        self.double_selected_item = None
        self.num_nodes = 0
        self.num_edges = 0
        self.node_list.clear()
        self.edge_list.clear()
        self.network_graph.clear()
        self.scene().clear()

    def get_node(self, name):
        """
        Return the Node object given the name
        :param name: name of Node object
        :return: The Node object
        """
        for node in self.node_list:
            if node.name == name:
                return node
        return None

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Up:
            self.centerNode.moveBy(0, -20)
        elif key == Qt.Key_Down:
            self.centerNode.moveBy(0, 20)
        elif key == Qt.Key_Left:
            self.centerNode.moveBy(-20, 0)
        elif key == Qt.Key_Right:
            self.centerNode.moveBy(20, 0)
        elif key == Qt.Key_Plus:
            self.scale_view(1.2)
        elif key == Qt.Key_Minus:
            self.scale_view(1 / 1.2)
        elif key == Qt.Key_Space or key == Qt.Key_Enter:
            for item in self.scene().items():
                if isinstance(item, Node):
                    item.setPos(-240 + qrand() % 480, -240 + qrand() % 480)
        else:
            super(GraphWidget, self).keyPressEvent(event)

    def wheelEvent(self, event):
        self.scale_view(math.pow(2.0, -event.angleDelta().y() / 240.0))

    def scale_view(self, scale_factor):
        factor = self.transform().scale(scale_factor, scale_factor).mapRect(QRectF(0, 0, 1, 1)).width()

        if factor < 0.07 or factor > 100:
            return

        self.scale(scale_factor, scale_factor)

    def handle_double_click(self, item):
        self.double_selected_item = item
        simulator_object = self.parentWidget().parentWidget()
        if type(item) == Edge:
            simulator_object.display(0)
        elif type(item) == Node:
            simulator_object.update_table_UI_with_node_table(item)
            simulator_object.display(1)
        simulator_object.update()


class NetworkSimulator(QWidget):
    """
    The class handles the interface for the software
    """
    WIDTH = 1200
    HEIGHT = 600

    def __init__(self, graph_widget):
        super().__init__()

        self.block_edit = False

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(self.WIDTH)
        self.setFixedHeight(self.HEIGHT)
        self.graph_widget = graph_widget
        self.scene = self.graph_widget.scene()
        self.double_selected_item = self.graph_widget.double_selected_item
        self.count = 0
        self.createButtons()
        # self.layout.addWidget(self.graph_widget)
        self.createSceneWindow()
        self.create_item_window()

    def create_item_window(self):
        """
        Method to create File window (right pannel)
        """
        self.file_frame = QGroupBox(self)

        self.stack_node = QWidget()
        self.stack_edge = QWidget()
        self.Stack = QStackedWidget()
        self.Stack.addWidget(self.stack_edge)
        self.Stack.addWidget(self.stack_node)

        self.stack_node_UI()
        self.stack_edge_UI()

        layout_file = QVBoxLayout()
        layout_file.addWidget(self.Stack)
        self.file_frame.setLayout(layout_file)
        self.layout.addWidget(self.file_frame, 0, 2)

    def display(self, i):
        self.Stack.setCurrentIndex(i)

    def stack_node_UI(self):
        """
        Method to create node properties view (right most pannel)
        """
        layout_node = QVBoxLayout()
        # --------------------------------------------
        #               Item name
        # --------------------------------------------
        self.item_name_frame = QFrame(self)
        layout_node_name = QHBoxLayout()
        self.item_name_frame.setLayout(layout_node_name)
        name_label = QLabel(self.item_name_frame)
        name_label.setText("Node Name: ")
        layout_node_name.addWidget(name_label)
        self.name_node_widget = QLineEdit(self.item_name_frame)
        layout_node_name.addWidget(self.name_node_widget)
        # --------------------------------------------
        #               Forwarding table
        # --------------------------------------------
        self.file_table = QTableWidget(30, 30)
        self.file_table.setSortingEnabled(False)
        self.file_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_table.resizeColumnsToContents()
        self.file_table.setColumnWidth(5, 0)
        self.file_table.resizeRowsToContents()

        layout_node.addWidget(self.item_name_frame)
        layout_node.addWidget(self.file_table)
        self.stack_node.setLayout(layout_node)

    def stack_edge_UI(self):
        """
        Method to create edge properties view (right most pannel)
        """
        layout_edge = QGridLayout()
        name_label = QLabel()
        name_label.setText("Edge Name: ")
        self.name_edge_widget = QLineEdit()
        active_label = QLabel()
        active_label.setText("Is Active: ")
        self.active_box = QCheckBox()
        self.active_box.stateChanged.connect(self.update_edge_active_status)
        cost_label = QLabel()
        cost_label.setText("Link Cost: ")
        # self.cost_edge_widget = QLineEdit()
        self.cost_edge_widget = QSpinBox()
        self.cost_edge_widget.setRange(0, 100)
        self.cost_edge_widget.valueChanged.connect(self.update_edge_cost)
        layout_edge.addWidget(name_label, 0, 0)
        layout_edge.addWidget(self.name_edge_widget, 0, 1)
        layout_edge.addWidget(active_label)
        layout_edge.addWidget(self.active_box, 1, 1)
        layout_edge.addWidget(cost_label, 2, 0)
        layout_edge.addWidget(self.cost_edge_widget, 2, 1)

        self.stack_edge.setLayout(layout_edge)

    def update_table_UI_with_node_table(self, node):
        node_table = node.dvr.node_table
        if node_table is []:
            return
        self.file_table.setRowCount(len(node_table))
        self.file_table.setColumnCount(len(node_table))
        for i in range(len(node_table)):
            for j, dv in enumerate(node_table[i]):
                self.file_table.setItem(i, j, QTableWidgetItem("{}".format(dv)))

    def update_edge_cost(self):
        if type(self.double_selected_item) is Edge:
            self.double_selected_item.set_cost(self.cost_edge_widget.value())
            # source_node = self.double_selected_item.source
            # dest_node = self.double_selected_item.dest

    def update_edge_active_status(self):
        if type(self.double_selected_item) is Edge:
            self.double_selected_item.is_active = self.active_box.isChecked()

    def update(self):
        self.double_selected_item = self.graph_widget.double_selected_item
        if type(self.double_selected_item) is Node:
            self.name_node_widget.setText(self.double_selected_item.name)
        elif type(self.double_selected_item) is Edge:
            self.name_edge_widget.setText(self.double_selected_item.name)
            self.cost_edge_widget.setValue(self.double_selected_item.cost)
            self.active_box.setChecked(self.double_selected_item.is_active)
        self.iter_widget.setText(str(self.count))
        super(NetworkSimulator, self).update()

    def reset(self):
        self.graph_widget.reset()
        self.count = 0
        self.update()

    def config_file(self, filename):
        """
        Handle reding config file
        :param filename: the path to config file
        """
        self.reset()
        num_node, list_edge = read_file(filename)
        for i in range(num_node):
            self.add_node()
        for edge in list_edge:
            value = edge[2]
            node1 = self.graph_widget.get_node(edge[0])
            node2 = self.graph_widget.get_node(edge[1])
            my_edge = Edge(node1, node2)
            my_edge.set_cost(int(value))
            self.graph_widget.add_item(my_edge)

    def read_input_file(self):
        """
        Open directory for user to pick a file
        """
        path = pickAFile()
        path = path[0]
        if path.endswith(".ini"):
            self.config_file(path)

    def add_node(self):
        self.graph_widget.add_item(Node(self.graph_widget, 20))

    def delete_selected_node(self):
        selected_lists = self.scene.selectedItems()
        for item in selected_lists:
            if type(item) == Node:
                print(len(item.edge_list))
                for edge in item.edge_list:
                    print("edge: ", edge)
                    if edge.source != item:
                        edge.source.remove_edge(edge)
                    else:
                        edge.dest.remove_edge(edge)
                    self.scene.removeItem(edge)
                self.scene.removeItem(item)

    def delete_selected_edge(self):
        selected_lists = self.scene.selectedItems()
        for item in selected_lists:
            if type(item) == Edge:
                item.source.remove_edge(item)
                item.dest.remove_edge(item)
                self.scene.removeItem(item)

    def add_edge(self):
        selectedLists = self.scene.selectedItems()

        # Currently support for selecting at most two items
        if len(selectedLists) >= 2:
            self.graph_widget.add_item(Edge(selectedLists[0], selectedLists[1]))
        else:
            pass

    def set_name(self, item, name):
        # TODO: get the cuttent item, get the name in the box, change it
        pass

    def generate_graph(self):
        """
        Initialize the DV table for each node.
        """
        dvList = []
        for i, node_i in enumerate(self.graph_widget.node_list):
            dvList.append([])
            for j, node_j in enumerate(self.graph_widget.node_list):
                dvList[i].append(node_i.get_edge_cost_between(node_j))
        self.graph_widget.network_graph = dvList
        for node in self.graph_widget.node_list:
            node.dvr.initialize_node_table()

    def step(self):
        """
        Run one iteration
        """
        for node in self.graph_widget.node_list:
            if not node.dvr.is_initialized:
                print("The dv table of each node must be initialized first")
                return

        is_converged = True
        for node in self.graph_widget.node_list:
            if node.dvr.calculate_distance_vector():
                is_converged = False

        for node in self.graph_widget.node_list:
            node.dvr.update_distance_vector()
            # print(node.dvr.node_table)
        print(is_converged)
        return is_converged

    def run_simulation(self):
        """
        Run the simulation
        """
        for node in self.graph_widget.node_list:
            if not node.dvr.is_initialized:
                print("The dv table of each node must be initialized first")
                return
        is_converged = False
        while (self.count < 100 and not is_converged):
            is_converged = self.step()
            self.count += 1
        self.update()
        print("number of iteration: ", self.count)

    def createSceneWindow(self):
        """
        Method to create middle view (middle pannel)
        """
        self.sceneFrame = QGroupBox(self)
        layoutScene = QVBoxLayout()
        self.sceneFrame.setLayout(layoutScene)

        # Add Tool Button
        self.tool_frame = QFrame(self)
        layout_tool = QHBoxLayout()
        self.tool_frame.setLayout(layout_tool)

        self.generate_network_graph = QPushButton("Generate Network", self.buttonFrame)
        self.generate_network_graph.clicked.connect(self.generate_graph)
        self.start_simu_button = QPushButton("Run Simulation", self.tool_frame)
        self.start_simu_button.clicked.connect(self.run_simulation)
        self.step_simu_button = QPushButton("Step", self.tool_frame)
        self.step_simu_button.clicked.connect(self.step)
        layout_tool.addWidget(self.generate_network_graph)
        layout_tool.addWidget(self.start_simu_button)
        layout_tool.addWidget(self.step_simu_button)

        # Add iteration label
        self.iter_frame = QFrame(self)
        layout_iter = QHBoxLayout()
        self.iter_frame.setLayout(layout_iter)

        iter_label = QLabel(self.iter_frame)
        iter_label.setText("number of iterations: ")
        self.iter_widget = QLineEdit(self.iter_frame)
        self.iter_widget.setText(str(self.count))
        layout_iter.addWidget(iter_label)
        layout_iter.addWidget(self.iter_widget)

        # Add Scene
        layoutScene.addWidget(self.tool_frame)
        layoutScene.addWidget(self.iter_frame)
        layoutScene.addWidget(self.graph_widget)
        self.layout.addWidget(self.sceneFrame, 0, 1)

    def createButtons(self):
        """
        Create Button layouts (left pannel)
        """
        self.buttonFrame = QGroupBox(self)
        # self.buttonFrame.setFixedSize(200, 4)
        layoutButton = QVBoxLayout()
        self.buttonFrame.setLayout(layoutButton)
        self.add_edge_button = QPushButton("Add Edge", self.buttonFrame)
        self.add_edge_button.clicked.connect(self.add_edge)
        self.add_node_button = QPushButton("Add Node", self.buttonFrame)
        self.add_node_button.clicked.connect(self.add_node)
        self.deletet_node_button = QPushButton("Delete Selected Node", self.buttonFrame)
        self.deletet_node_button.clicked.connect(self.delete_selected_node)
        self.delete_edge_button = QPushButton("Delete Selected Edge", self.buttonFrame)
        self.delete_edge_button.clicked.connect(self.delete_selected_edge)
        self.input_button = QPushButton("Input File", self.buttonFrame)
        self.input_button.clicked.connect(self.read_input_file)
        self.reset_button = QPushButton("Reset", self.buttonFrame)
        self.reset_button.clicked.connect(self.reset)
        # Add button in layout
        layoutButton.addWidget(self.input_button)
        layoutButton.addWidget(self.reset_button)
        layoutButton.addWidget(self.add_edge_button)
        layoutButton.addWidget(self.add_node_button)
        layoutButton.addWidget(self.deletet_node_button)
        layoutButton.addWidget(self.delete_edge_button)
        self.layout.addWidget(self.buttonFrame, 0, 0)


def pickAFile(sdir=None):
    """
        Opens a file chooser to let the user pick a file and returns the
        complete path name as a string.

        :param sdir: the directory that holds the file (optional)
        :return: the string path to the file chosen in the dialog box
    """

    if sdir is not None:
        our_dir = sdir
    else:
        our_dir = os.getcwd()
    ret = QFileDialog.getOpenFileName(directory=our_dir)
    if ret == '':
        ret = None

    return ret


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    qsrand(QTime(0, 0, 0).secsTo(QTime.currentTime()))

    widget = GraphWidget()

    a = NetworkSimulator(widget)
    a.show()

    sys.exit(app.exec_())
