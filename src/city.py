from hex import Hex

class City:
    def __init__(self, start_hex, grid, color=(255, 255, 255), owner_id=None):
        self.current_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.color = color
        self.owner_id = owner_id
        self.grid = grid
        self.institutes = []
        self.farms = []
        self.buildings = []
        
        # Turn the tile it is on into a white color (light element)
        for tile in grid:
            if tile.position == self.current_hex:
                tile.element = "light"
                tile.has_city = True
                tile.owner = color
                break

    def get_adjacent_hexes(self):
        q = self.current_hex.q
        r = self.current_hex.r
        return [
            Hex(q + 1, r),
            Hex(q + 1, r - 1),
            Hex(q, r - 1),
            Hex(q - 1, r),
            Hex(q - 1, r + 1),
            Hex(q, r + 1),
        ]

    def get_tile_at_hex(self, hex_coord):
        return next((tile for tile in self.grid if tile.position == hex_coord), None)

    def get_available_building_sites(self):
        sites = []
        for adj_hex in self.get_adjacent_hexes():
            tile = self.get_tile_at_hex(adj_hex)
            if tile is None:
                continue
            if tile.has_city:
                continue
            if tile.building is not None:
                continue
            sites.append(tile)
        return sites

    def add_building(self, building_type):
        available = self.get_available_building_sites()
        if not available:
            return False

        tile = available[0]
        tile.building = building_type
        tile.building_owner = self.owner_id
        tile.building_turns_left = 3
        self.buildings.append((building_type, tile.position))
        if building_type == "farm":
            self.farms.append(tile.position)
        elif building_type == "institute":
            self.institutes.append(tile.position)
        return True

    def add_farm(self):
        return self.add_building("farm")

    def add_institute(self):
        return self.add_building("institute")

    def update(self):
        pass

