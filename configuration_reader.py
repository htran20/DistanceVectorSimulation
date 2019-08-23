from configparser import ConfigParser


def read_file(filename):
    """
    read the config file and return the number of
    nodes and list of edges
    :param filename: the config file
    :return: the number of nodes and list of edges
    """
    parser = ConfigParser()
    try:
        parser.read(filename)
        num_node = parser.getint('node', 'number')
    except ConfigParser.Error:
        return None
    except ValueError:
        return None

    option = None
    try:
        option = parser.get('node', 'option')
    except ConfigParser.Error as e:
        print(e)
        pass
    except ValueError as e:
        print(e)
        pass

    list_edge = []
    if option == "Circle":
        for i in range(num_node):
            value = 1
            node_1 = str((i % num_node)+1)
            node_2 = str(((i+1) % num_node)+1)
            print((node_1, node_2, value))
            list_edge.append((node_1, node_2, value))
    elif option == "Full":
        for i in range(num_node):
            value = 1
            node_1 = str((i % num_node)+1)
            for j in range(i+1, num_node):
                node_2 = str((j % num_node)+1)
                print((node_1, node_2, value))
                list_edge.append((node_1, node_2, value))
    elif option == "None":
        try:
            edges = parser.items('edge')
            for edge in edges:
                name, value = edge
                node_1 = name.split("_")[0]
                node_2 = name.split("_")[1]
                print(type(value))
                list_edge.append((node_1, node_2, value))

        except ConfigParser.Error as e:
            print(e)
            return None

    return num_node, list_edge
