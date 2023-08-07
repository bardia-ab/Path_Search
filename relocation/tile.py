import re
class Tile:
    def __init__(self, name):
        self.name   = name

    def __repr__(self):
        return self.name

    @property
    def exact_type(self):
        end_idx = re.search('_X-*\d+Y-*\d+', self.name).regs[0][0]
        return self.name[:end_idx]

    @property
    def type(self):
        if self.name.startswith('INT'):
            return 'INT'
        else:
            return 'CLB'

    @property
    def coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.name)[0]

    @property
    def site_type(self):
        if self.name.startswith('INT'):
            return None
        elif self.name.startswith('CLEM'):
            return 'M'
        else:
            return 'L'

    @property
    def direction(self):
        if self.name.startswith('INT'):
            dir = 'Center'
        elif self.name.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir
