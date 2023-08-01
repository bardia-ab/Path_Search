import re

class Edge:

    def __init__(self, edge):
        self.name = edge

    def __repr__(self):
        return f'{self.u} -> {self.v}'

    def __getitem__(self, item):
        return self.name[item]

    def __len__(self):
        return len(self.name)

    @property
    def u(self):
        return self.name[0]

    @property
    def u_tile(self):
        return Edge.get_tile(self.u)

    @property
    def u_port(self):
        return Edge.get_port(self.u)

    @property
    def u_coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.u_tile)[0]

    @property
    def v(self):
        return self.name[1]

    @property
    def v_tile(self):
        return Edge.get_tile(self.v)

    @property
    def v_port(self):
        return Edge.get_port(self.v)

    @property
    def v_coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.v_tile)[0]

    @property
    def type(self):
        if self.u_tile == self.v_tile:
            return 'pip'
        else:
            return 'wire'

    @staticmethod
    def get_tile(wire, delimiter='/'):
        return wire.split(delimiter)[0]

    @staticmethod
    def get_port(wire, delimiter='/'):
        return wire.split(delimiter)[1]

    @staticmethod
    def is_wire(edge):
        if Edge.get_tile(edge[0]) != Edge.get_tile(edge[1]):
            return True
        else:
            return False

    @staticmethod
    def is_pip(edge):
        if Edge.get_tile(edge[0]) == Edge.get_tile(edge[1]):
            return True
        else:
            return False