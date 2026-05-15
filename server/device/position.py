from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __repr__(self):
        return f"Point{{x={self.x}, y={self.y}}}"

@dataclass(frozen=True)
class Size:
    width: int
    height: int

    def get_max(self):
        return max(self.width, self.height)

    def rotate(self):
        return Size(self.height, self.width)

    def limit(self, max_size: int):
        if max_size == 0:
            return self
        
        portrait = self.height > self.width
        major = self.height if portrait else self.width
        if major <= max_size:
            return self
        
        minor = self.width if portrait else self.height
        new_major = max_size
        new_minor = max_size * minor // major
        
        w = new_minor if portrait else new_major
        h = new_major if portrait else new_minor
        return Size(w, h)

    def round8(self):
        if self.is_multiple_of_8():
            return self
        
        portrait = self.height > self.width
        major = self.height if portrait else self.width
        minor = self.width if portrait else self.height
        
        major &= ~7
        minor = (minor + 4) & ~7
        if minor > major:
            minor = major
            
        w = minor if portrait else major
        h = major if portrait else minor
        return Size(w, h)

    def is_multiple_of_8(self):
        return (self.width & 7) == 0 and (self.height & 7) == 0

    def __repr__(self):
        return f"{self.width}x{self.height}"

@dataclass(frozen=True)
class Position:
    point: Point
    screen_size: Size

    def rotate(self, rotation: int):
        if rotation == 1:
            return Position(Point(self.screen_size.height - self.point.y, self.point.x), self.screen_size.rotate())
        elif rotation == 2:
            return Position(Point(self.screen_size.width - self.point.x, self.screen_size.height - self.point.y), self.screen_size)
        elif rotation == 3:
            return Position(Point(self.point.y, self.screen_size.width - self.point.x), self.screen_size.rotate())
        else:
            return self

    def __repr__(self):
        return f"Position{{point={self.point}, screenSize={self.screen_size}}}"
