#!/usr/bin/python

import sys
import math
import argparse
import subprocess

from lasercut.laser.laser import Arc, Circle, Polygon, Collection, Config, Text
from lasercut.laser.laser import radians, degrees
from lasercut.laser.render import DXF, GCODE, SCAD, PDF

#
#
#   http://solarsystem.nasa.gov/planets/earth/facts

axial_tilt = 23.4393 # degrees
eccentricity = 0.01671123
longitude_of_perihelion = 283.067 # degrees

class Twilight:
    civil = -6
    nautical = -12
    astronomical = -18

zodiac = [ 
    "Aries", "Taurus", "Gemini",
    "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius",
    "Capricorn", "Aquarius", "Pisces",
]

months = [
    ( "Jan",  31, ),
    ( "Feb",  28, ),
    ( "Mar",  31, ),
    ( "Apr",  30, ),
    ( "May",  31, ),
    ( "Jun",  30, ),
    ( "Jul",  31, ),
    ( "Aug",  31, ),
    ( "Sep",  30, ),
    ( "Oct",  31, ),
    ( "Nov",  30, ),
    ( "Dec",  31, ),
]

days = sum([ x[1] for x in months ])
assert days == 365

#
#   Equations from "The Astrolabe" by James E Morrison.

def r_eq(r_cap, e=axial_tilt):
    # radius of equator, given radius of tropic of capricorn
    return r_cap * math.tan(radians((90.0 - e) / 2.0))

def r_can(r_eq, e=axial_tilt):
    # radius of tropic of cancer, given the equator
    return r_eq * math.tan(radians((90.0 - e) / 2.0))

def almucantar(a, req, lat):
    aa, ll = radians(a), radians(lat)
    ra = req * math.cos(aa) / (math.sin(ll) + math.sin(aa))
    ya = req * math.cos(ll) / (math.sin(ll) + math.sin(aa))
    return ra, ya

def r_dec(r_eq, dec):
    # radius of declination 
    return r_eq * math.tan(radians((90.0 - dec) / 2.0))

#
#   Intersection of 2 circles.
#   
#   Assumes y==0 for both circles.

def intersect(x0, r0, x1, r1):
    y0, y1 = 0, 0
    # http://paulbourke.net/geometry/circlesphere/
    dx = x1 - x0
    dy = y1 - y0

    d = math.sqrt((dy*dy) + (dx*dx))

    if d > (r0 + r1): # seperate
        return None
    if d < abs(r0 - r1): # nested
        return None
    if (d == 0) and (r0 == r1): # co-incident
        return None

    a = ((r0*r0) - (r1*r1) + (d*d)) / (2 * d)

    x2 = x0 + (dx * (a/d))
    y2 = y0 + (dy * (a/d))

    h = math.sqrt((r0*r0) - (a*a))

    rx = -dy * (h/d)
    ry = dx * (h/d)

    xi = x2 + rx
    xii = x2 - rx
    yi = y2 + ry
    yii = y2 - ry

    return (xi, yi), (xii, yii)

#
#   Intersection of 2 circles

def intersect2(xy1, r1, xy2, r2):
    x1, y1 = xy1
    x2, y2 = xy2
    dx, dy = (x2 - x1), (y2 - y1)
    angle = math.atan2(dy, dx)
    dc = math.sqrt((dx * dx) + (dy * dy))

    c1 = Circle((x1, y1), r1)
    c2 = Circle((x2, y2), r2)
    p = Collection()
    p.add(c1)
    p.add(c2)
    # translate/rotate so circles lie on y==0 axis
    p.translate(-x1, -y1)
    p.rotate(-degrees(angle))

    inter = intersect(c1.x, c1.radius, c2.x, c2.radius)
    if inter is None: # no intersection
        return None

    (xi, yi), (xii, yii) = inter
    p = Polygon()
    p.add(xi, yi)
    p.add(xii, yii)
    # reverse the translate/rotate to restore the y axis component
    p.rotate(degrees(angle))
    p.translate(x1, y1)
    return p.points

#
#

class Circ:

    def __init__(self, x, r):
        self.x = x
        self.r = r

    def shape(self, s=1.0, **kwargs):
        return Circle((self.x * s, 0), self.r * s, **kwargs)

    def intersect(self, c):
        return intersect(self.x, self.r, c.x, c.r)

#
#

def ticks(work, xy, r1, r2, a1, a2, step, colour=None):
    x0, y0 = xy
    a = a1
    assert a1 <= a2
    while a <= a2:
        p = Polygon(colour=colour)
        x = math.sin(radians(a))
        y = math.cos(radians(a))
        p.add(x0 + (r1 * x), y0 + (r1 * y))
        p.add(x0 + (r2 * x), y0 + (r2 * y))
        work.add(p)
        a += step

#
#

def draw_almucantar(a, config, colour, work, rad_equator, outer):
    ra, ya = almucantar(a, rad_equator, config.latitude)
    circ = Circ(ya, ra)
    ii = outer.intersect(circ)
    if ii:
        (x0, y0), (x1, y1) = ii
        m = circ.x

        x = x0 - m
        y = y0

        a = degrees(math.atan2(y, x))
        x = x1 - m
        y = y1

        b = degrees(math.atan2(y, x))

        arc = Arc((m, 0), ra, a, b, colour=colour)
        work.add(arc)
    else:
        c = circ.shape(colour=colour)
        c.rotate(radians(90.0))
        work.add(c)

#
#   Plate basic shape

def cut_plate(config):
    size = config.size
    key_angle = 1.0
    key_size = size * 0.98
    work = Collection(colour=config.cut())
    a1 = 180.0 - key_angle
    a2 = 180.0 + key_angle
 
    # leave space for the locator key
    c = Arc((0, 0), size, a2, a1)
    work.add(c)
    # top of the locator key
    c = Arc((0, 0), key_size, a1, a2)
    work.add(c)

    def spoke(angle):
        angle = radians(angle)
        p = Polygon()
        p.add(size * math.cos(angle), size * math.sin(angle))
        p.add(key_size * math.cos(angle), key_size * math.sin(angle))
        work.add(p)

    spoke(a1)
    spoke(a2)

    return work


#
#   Plate detail

from lasercut.laser.ops import arc_to_poly

def circle_intersection(r1, r2, d):
    # https://mathworld.wolfram.com/Circle-CircleIntersection.html
    # assumes both on the x-axis (ie centre y is 0)
    x = ((d*d) - (r1*r1) + (r2*r2)) / (2 * d)
    y = math.sqrt((r2*r2) - (x*x))
    return x, y

class Points:

    def __init__(self, *args, **kwargs):
        self.points = []
        self.kwargs = kwargs

    def add(self, p):
        self.points.append(p)

    def draw(self, drawing, color):
        fill = self.kwargs.get("fill")
        if fill:
            drawing.polygon(points=self.points, color=fill, fill=fill)

#
#

def fill_plate(work, config):
    # background colour
    rad_capricorn = config.size
    rad_equator = r_eq(rad_capricorn)

    capricorn = Circle((0, 0), rad_capricorn)

    r, x = almucantar(0, rad_equator, config.latitude)
    horizon = Circle((x, 0), r)

    try:
        xx, yy = circle_intersection(r, rad_capricorn, x)
    except ValueError:
        # horizon is within capricorn so can paint as circles
        c = Circle((0, 0), rad_capricorn, colour=Config.draw_colour, fill=config.night_colour)
        work.add(c)
        c = Circle((x, 0), r, colour=Config.draw_colour, fill=config.day_colour)
        work.add(c)
        return

    def paint(circle, colour, fn):
        points = Points(fill=colour)
        s = arc_to_poly(circle)
        for x, y in s.points:
            if fn(x, xx):
                points.add((x, y)) 
        work.add(points)

    def fn(x, xx): return True
    paint(capricorn, config.night_colour, fn)

    def fn(x, xx): return x > xx
    paint(capricorn, config.day_colour, fn)

    def fn(x, xx): return x < xx
    paint(horizon, config.day_colour, fn)

#
#
#

def plate(config):

    work = Collection()

    # equator and tropics
    rad_capricorn = config.size
    rad_equator = r_eq(rad_capricorn)
    rad_cancer = r_can(rad_equator)

    if config.clock:
        fill_plate(work, config)

    outer = Circ(0, rad_capricorn)

    c = Circle((0, 0), rad_capricorn, colour=config.thick_colour)
    work.add(c)
    c = Circle((0, 0), rad_equator, colour=config.thick_colour)
    work.add(c)
    c = Circle((0, 0), rad_cancer, colour=config.thick_colour)
    work.add(c)

    if config.hole:
        c = Circle((0, 0), config.hole * 2, colour=config.cut_colour)
        work.add(c)

    # quarters
    def make_lines(points):
        p = Polygon(colour=config.thick_colour)
        for point in points:
            p.add(*point)
        work.add(p)

    make_lines([ (-rad_capricorn, 0), (rad_capricorn, 0), ])
    make_lines([ (0, -rad_capricorn), (0, rad_capricorn), ])

    # draw the almucantar lines
    if config.almucantar:
        for a in range(0, 90, config.almucantar):
            colour = config.thin_colour
            if (a % 10) == 0:
                colour = config.thick_colour
            draw_almucantar(a, config, colour, work, rad_equator, outer)

    # twilight arcs
    if config.twilight:
        colour = config.dotted_colour
        for twilight in config.twilight:
            draw_almucantar(twilight, config, colour, work, rad_equator, outer)

    # azimuth lines
    if config.azimuth:
        # horizon circle
        hr, hx = almucantar(0.0, rad_equator, config.latitude)
        # zenith / nadir
        yz =  rad_equator * math.tan(radians(90.0 - config.latitude) / 2.0)
        yn = -rad_equator * math.tan(radians(90.0 + config.latitude) / 2.0)
        # x centre for all circles
        yc = (yz + yn) / 2.0
        yaz = (yz - yn) / 2.0
        for angle in range(0, 90, config.azimuth):
            # calculate the azimuth circle x and radius
            xa = yaz * math.tan(radians(angle))
            ra = yaz / math.cos(radians(angle))

            def arc_angle(x, y):
                return 90.0 - degrees(math.atan2(x - yc, y - xa))

            # intersection with the horizon circle
            inter = intersect2((hx, 0), hr, (yc, xa), ra)
            assert inter, angle
            (x1, y1), (x2, y2) = inter
            # calculate the arc angles
            a1 = arc_angle(x1, y1)
            a2 = arc_angle(x2, y2)

            # intersection with the tropic of capricorn
            inter = intersect2((0, 0), rad_capricorn, (yc, xa), ra)
            if inter is None:
                # latitude is below the tropic of capricorn
                continue
            (x1, y1), (x2, y2) = inter
            # calculate the arc angle
            a3 = arc_angle(x2, y2)
            if a3 < a2:
                a2 = a3

            colour = config.thin_colour
            if (angle % 10) == 0:
                colour = config.thick_colour

            # add azimuth arc
            c = Arc((yc, xa), ra, a1, a2, colour=colour)
            work.add(c)
            # add same reflected in the x axis
            c = Arc((yc, xa), ra, a1, a2, colour=colour)
            c.reflect_h()
            work.add(c)

    # engrave the latitude number
    height = config.size/20.0
    lat = config.latitude + 0.5
    text = str(int(lat / 10)) + "  " + str(int(lat % 10))
    t = Text((0, -rad_equator*1.15), text, height=height, adjust=True, colour=config.thick_colour)
    t.rotate(270)
    t.translate(0, height*0.8)
    work.add(t)

    return work

#
#

def mater(config):
    work = Collection(colour=config.thick_colour)

    inner = config.size
    outer = config.outer
    mid = (inner + outer) / 2
    small = (mid + outer) / 2

    # draw / cut circles

    c = Circle((0, 0), outer, colour=config.cut(), fill=config.main_colour)
    work.add(c)
    c = Circle((0, 0), mid, colour=config.thick_colour)
    work.add(c)

    p = Circle((0, 0), config.size)
    work.add(p)

    # draw ticks

    tick = [
        [   inner, mid, 15, config.thick_colour, ],
        [   mid, small, 3, config.thick_colour, ],
        [   small, outer, 1, config.thin_colour, ],
    ]
    if config.clock:
        tick[0][2] = 360/24 # hours
        tick[1][2] = 360/(24*4) # quarters
        tick[2][2] = 360/(24*12) # 5 mins

    for a, b, n, colour in tick:
        ticks(work, (0, 0), a, b, 0, 360, n, colour=colour)

    hours = [ 
        "I", "II", "III", "IV", "V", "VI", 
        "VII", "VIII", "IX", "X", "XI", "XII", 
    ] 
    # label the limb
    for idx, a in enumerate(range(0, 360, 15)):
        rad = radians(a)

        if a > 270:
            label = 360 - a
        elif a > 180:
            label = a - 180
        elif a > 90:
            label = 180 - a
        else:
            label = a

        # degrees
        if not config.clock:
            height = config.size/35.0
            t = Text((0, 0), "%0.1d" % label, height=height, adjust=True)
            t.rotate(-a)
            r = small - 1
            x, y = r * math.sin(rad), r * math.cos(rad)
            t.translate(x, y)
            t.rotate(-0.3)
            work.add(t)

        # hours
        height = config.size/20.0
        t = Text((0, 0), hours[idx % 12], height=height, adjust=True)
        t.rotate(-a - 3)
        r = mid - 2
        x, y = r * math.sin(rad), r * math.cos(rad)
        t.translate(x, y)
        t.rotate(-90 - 16)
        work.add(t)

    return work

#
#

def rear_limb(config):
    work = Collection()

    inner = config.size
    outer = config.outer
    mid = (outer + inner) / 2.0
    small = (outer + mid) / 2.0

    c = Circle((0, 0), outer, colour=config.cut())
    work.add(c)

    c = Circle((0, 0), mid, colour=config.thick_colour)
    work.add(c)

    ticks(work, (0, 0), inner, mid, 0, 360, 30, colour=config.thick_colour)
    ticks(work, (0, 0), mid, small, 0, 360, 5, colour=config.thick_colour)
    ticks(work, (0, 0), small, outer, 0, 360, 1, colour=config.thin_colour)

    # degree text for zodiac
    r = ((small + mid) / 2.0) + ((small - mid) / 3.0)
    for angle in range(0, 360, 5):
        text = "%d" % (angle % 30)
        t = Text((0, 0), text, height=config.size/35.0)
        t.rotate(angle)
        rad = radians(360 - angle - (1.3 * len(text)))
        x, y = r * math.sin(rad), r * math.cos(rad)
        t.translate(x, y)
        work.add(t)

    # text for zodiac
    r = (mid + inner) / 2.0
    for idx, sign in enumerate(zodiac):
        angle = 180 + (idx * 30)
        t = Text((0, 0), sign, height=config.size/25.0)
        angle += 18
        t.rotate(angle)
        rad = radians(360 - angle)
        x, y = r * math.sin(rad), r * math.cos(rad)
        t.translate(x, y)
        work.add(t)

    return work 

#
#

def rear_plate(config):

    work = Collection()

    c = Circle((0, 0), config.size, colour=config.thick_colour)
    work.add(c)

    if 0:
        r = config.outer
        angle = longitude_of_perihelion
        x = r * math.sin(radians(angle))
        y = - r * math.cos(radians(angle))
        c = Polygon()
        c.add(x, y)
        c.add(-x, -y)
        work.add(c)

        x0, y0 = 10, 10 # TODO
        r = config.size - math.sqrt((x0 * x0) + (y0 * y0))
        for day in range(days):
            c = Polygon()
            angle = day * 360.0 / days
            x = r * math.sin(radians(angle))
            y = r * math.cos(radians(angle))
            c.add(x0 + x, y0 + y)
            c.add(0, 0)
            work.add(c)

    return work

#
#

if __name__ == "__main__":

    codes = { 
        "dxf"   : ( DXF, '.dxf' ),
        "gcode" : ( GCODE, '.ngc' ),
        "scad"  : ( SCAD, '.scad' ),
        "pdf"   : ( PDF, '.pdf' ),
    }
    parts = [ 'plate', 'mater', 'rear', 'rete' ]

    p = argparse.ArgumentParser()
    p.add_argument('part', nargs='*', default=[], help=" ".join(parts))
    p.add_argument('--code', default='dxf', help="|".join(codes.keys()))
    p.add_argument('--lat', type=float, default=50.37, help="latitude")
    p.add_argument('--qcad', action='store_true', help="call qcad to view the output")
    p.add_argument('--stdout', action='store_true')
    p.add_argument('--almucantar', type=int, default=5, help="step in degrees of almucantar lines")
    p.add_argument('--azimuth', type=int, default=15, help="step in degrees of azimuth lines")
    p.add_argument('--size', type=int, default=155, help="diameter of tropic of capricorn")
    p.add_argument('--nautical', action='store_true', help="nautical twilight")
    p.add_argument('--civil', action='store_true', help="civil twilight")
    p.add_argument('--astronomical', action='store_true', help="astronomical twilight")
    p.add_argument('--hole', type=float, help="cut central hole of size n")
    p.add_argument('--clock', action='store_true')

    args = p.parse_args()
    print(args)

    for arg in args.part:
        assert arg in parts, (args, parts)
        #print >> sys.stderr, "Generating:", arg

    try:
        dxf, ext = codes[args.code]
    except KeyError:
        raise Exception("unknown code '%s'" % args.code)

    if len(args.part) == 0:
        path = "/dev/null"
    elif len(args.part) == 1:
        path = args.part[0] + ext
    else:
        path = "output" + ext

    if args.stdout:
        path = None

    drawing = dxf.drawing(path)
    config = Config()

    config.latitude = args.lat
    config.twilight = [ ]
    if args.nautical:
        config.twilight.append(Twilight.nautical)
    if args.civil:
        config.twilight.append(Twilight.civil)
    if args.astronomical:
        config.twilight.append(Twilight.astronomical)

    # pitch of lines
    config.almucantar = args.almucantar
    config.azimuth = args.azimuth

    # radius of the edge of the plate (tropic of Capricorn)
    config.size = args.size
    config.outer = config.size * 1.2
    config.hole = args.hole
    config.clock = args.clock

    config.night_colour = (0.65, 0.65, 1)
    config.day_colour = (0.85, 0.85, 1)
    config.main_colour = (0.9, 0.9, 0.2)

    work = Collection()

    if 'rete' in args.part:
        print("Generating rete", file=sys.stderr)
        import rete
        r = rete.Rete("rete" + ext, config)
        r.draw()
        r.save()
        sys.exit()

    if 'rear' in args.part:
        print("Generating rear", file=sys.stderr)
        p = rear_plate(config)
        work.add(p)
        p = rear_limb(config)
        work.add(p)

    if 'mater' in args.part:
        print("Generating mater", file=sys.stderr)
        p = mater(config)
        work.add(p)

    if 'plate' in args.part:
        print("Generating plate", file=sys.stderr)
        p = plate(config)
        work.add(p)

    work.draw(drawing)
    print("Writing to", path, file=sys.stderr)
    drawing.save()

    # call qcad to view the output
    if args.qcad:
        cmd = "qcad %s" % path
        print("Call %s" % cmd, file=sys.stderr)
        subprocess.call(cmd, shell=True)

# FIN
