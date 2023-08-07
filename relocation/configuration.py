import re
class Configuration:

    covered_pips_dict = {}
    def __init__(self):
        self.used_nodes_dict    = {}
        self.CUTs               = []

    def add_DLOC_CUT(self, DLOC_G):
        DLOC_nodes = []
        for node in DLOC_G:
            '''if node.startswith('INT'):
                tile = (self.get_tile(node))
                port = self.get_port(node)
            else:
                tile = f'CLB_{self.get_direction(node)}_{self.get_coordinate(node)}'
                port = self.get_port(node).split('_SITE_0_')[-1]'''
            tile = self.get_tile(node)
            port = self.get_port(node)

            if tile in self.used_nodes_dict:
                if port in self.used_nodes_dict[tile]:
                    return False      # Collision
                else:
                    DLOC_nodes.append((tile, port))
            else:
                DLOC_nodes.append((tile, port))

        for element in DLOC_nodes:
            self.extend_dict(self.used_nodes_dict, element[0], element[1], value_type='set')

        for edge in DLOC_G.edges():
            if self.is_pip(edge):
                if edge[0].startswith('INT'):
                    key = self.get_tile(edge[0])
                    value = (self.get_port(edge[0]), self.get_port(edge[1]))
                else:
                    key = self.get_tile(edge[0])
                    value = (self.get_port(edge[0]), self.get_port(edge[1]))
                    #key = f'CLB_{self.get_direction(edge[0])}_{self.get_coordinate(edge[0])}'
                    #value = (self.get_port(edge[0]).split('_SITE_0_')[-1], self.get_port(edge[1]).split('_SITE_0_')[-1])

                self.extend_dict(Configuration.covered_pips_dict, key, value, value_type='set')

        return True

    @staticmethod
    def is_pip(edge):
        if Configuration.get_tile(edge[0]) == Configuration.get_tile(edge[1]):
            return True
        else:
            return False

    @staticmethod
    def get_direction(clb_node):
        if clb_node.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir

    @staticmethod
    def get_coordinate(node):
        return re.findall('X-*\d+Y-*\d+', node)[0]

    @staticmethod
    def get_tile(wire, delimiter='/'):
        return wire.split(delimiter)[0]

    @staticmethod
    def get_port(wire, delimiter='/'):
        return wire.split(delimiter)[1]

    @staticmethod
    def extend_dict(dict_name, key, value, extend=False, value_type='list'):
        if value_type == 'set':
            if key not in dict_name:
                if isinstance(value, str) or isinstance(value, tuple):
                    dict_name[key] = {value}
                else:
                    dict_name[key] = set(value)
            else:
                if isinstance(value, str) or isinstance(value, tuple):
                    dict_name[key].add(value)
                else:
                    dict_name[key].update(value)
        else:
            if extend:
                if key not in dict_name:
                    dict_name[key] = [value]
                else:
                    dict_name[key].extend(value)
            else:
                if key not in dict_name:
                    dict_name[key] = [value]
                else:
                    dict_name[key].append(value)

        return dict_name
