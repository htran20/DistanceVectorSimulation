import copy


class DVR:
    """
    This class handle the operation of the DVR algorithm
    """
    def __init__(self, node):
        self.node = node
        self.graph = node.graph
        self.node_list = self.graph.node_list
        self.neigbor_index = [] # List of neighbor index
        self.node_table = [] # The DV table
        self.temp_table = []
        self.is_initialized = False
        self.is_converged = False
        self.node_index = self.node.node_index
        # List that keep track which interface the cost to
        #  a node is learn from
        self.learn_table = []

    def update_neighbor_index(self):
        """
        Update the index of neighbor nodes
        :return:
        """
        self.neigbor_index.clear()
        for node in self.node.neighbor_nodes:
            node_index = node.node_index
            self.neigbor_index.append(node_index)

    def initialize_node_table(self):
        """
        Ininitalize the DV table for the node
        """
        self.node_index = self.node.node_index
        self.node_table = []
        for i, node_i in enumerate(self.node_list):
            self.node_table.append([])
            self.learn_table.append(0)
            for j, node_j in enumerate(self.node_list):
                if node_i == self.node:
                    self.node_table[i].append(node_i.get_edge_cost_between(node_j))
                else:
                    self.node_table[i].append(None)
        self.update_neighbor_index()
        self.learn_table[self.node_index] = self.node_index
        for index in self.neigbor_index:
            self.learn_table[index] = index
        self.is_initialized = True
        self.update_neighbor_index()

    def calculate_distance_vector(self):
        if not self.is_initialized:
            print("The node table must be initialized first")
            return
        self.update_neighbor_index()
        self.temp_table = copy.deepcopy(self.node_table)

        # Loop through neighbor nodes
        temp_DV = []
        temp_index_DV = []
        for i in range(len(self.node_table)):
            temp_DV.append([])
            temp_index_DV.append([])

        for node in self.node_list:
            node_index = node.node_index
            if node in self.node.neighbor_nodes:
                cost_between = self.node.get_edge_cost_between(node)
                # Get and save neighbor v’s distance vector
                DV_node = node.dvr.node_table[node_index]
                self.node_table[node_index] = DV_node

                # uses the Bellman-Ford equation to update its own distance vector
                for i in range(len(self.temp_table[self.node_index])):
                    if i is self.node_index:
                        temp_DV[i].append(0)
                        temp_index_DV[i].append(i)
                    elif DV_node[i] is None:
                        continue
                    elif node.dvr.learn_table[i] == self.node_index:
                        temp_DV[i].append(999999 + cost_between)
                        temp_index_DV[i].append(node_index)
                    else:
                        temp_DV[i].append(DV_node[i] + cost_between)
                        temp_index_DV[i].append(node_index)
            elif node != self.node:
                DV_node = [None for i in range(len(self.node_list))]
                print("AA", self.node.node_index)
                print("node", node_index)
                self.node_table[node_index] = DV_node


        for i, dv in enumerate(self.temp_table[self.node_index]):
            min_value, node_index = self.compute_min(temp_DV[i], temp_index_DV[i])
            self.temp_table[self.node_index][i] = min_value
            self.learn_table[i] = node_index
        return self.is_DV_changed()

    def compute_min(self, a_list, index_list):
        """
        Compute the min value of path's cost and the index of the interface
        :param a_list: the list holds the value
        :param index_list: the list holds the index position
        :return: the min value and the node index of the interface
        """
        try:
            min_value = min(a_list)
            index = a_list.index(min_value)
            node_index = index_list[index]
            return min_value, node_index
        except:
            return None, None


    def update_distance_vector(self):
        """
        update the distance vector
        """
        self.node_table[self.node_index] = self.temp_table[self.node_index]

    def is_DV_changed(self):
        """
        check whether the Distance Vector has changed
        """
        for i, row in enumerate(self.node_table):
            for j, entry in enumerate(self.node_table[i]):
                if entry != self.temp_table[i][j]:
                    return True
        return False
