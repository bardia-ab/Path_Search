import re
from resources.node import Node

class Edge:
    __slots__ = ('_name', 'idx')
    def __init__(self, edge: (str|Node, )):
        self.name = edge

    def __repr__(self):
        return f'{self.u} -> {self.v}'

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __hash__(self):
        return hash((self.name, ))

    def __getitem__(self, item):
        return self.name[item]

    def __len__(self):
        return len(self.name)

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if self.idx >= len(self):
            raise StopIteration
        else:
            self.idx += 1
            return self[self.idx - 1]

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, edge:(str|Node, )):
        if type(edge[0]) == str:
            edge = (Node(edge[0]), Node(edge[1]))

        self._name = edge

    @property
    def u(self):
        return self.name[0].name

    @property
    def u_tile(self):
        return self.name[0].tile

    @property
    def u_port(self):
        return self.name[0].port

    @property
    def u_coordinate(self):
        return self.name[0].coordinate

    @property
    def v(self):
        return self.name[1].name

    @property
    def v_tile(self):
        return self.name[1].tile

    @property
    def v_port(self):
        return self.name[1].port

    @property
    def v_coordinate(self):
        return self.name[1].coordinate

    @property
    def type(self):
        if self.u_tile == self.v_tile:
            return 'pip'
        else:
            return 'wire'