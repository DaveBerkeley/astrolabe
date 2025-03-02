#!/usr/bin/env python3

import sys
import os
import cmath
import math

import ephem # pyephem
import ephem.stars as stars

from lasercut.laser.render import Difference, Union, Intersection, Hull, SCAD
from lasercut.laser.laser import radians, degrees

outer_disc_w = 8
ecliptic_w = 10
disc_thick = 1.5
chamfer = 3
centre_surround = 4
text_h = 0.5

zodiac = [ 
    "Aries", "Taurus", "Gemini",
    "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius",
    "Capricorn", "Aquarius", "Pisces",
]

def zodiac_path(idx):
    return os.path.join('/tmp', zodiac[idx] + '.png')    

def create_zodiac():
    zodiac_signs = [
        "♈︎︎", "♉︎︎", "♊︎︎",
        "♋︎︎", "♌︎︎", "♍︎︎",
        "♎︎︎", "♏︎︎", "♐︎︎",
        "♑︎︎", "♒︎︎", "♓︎︎",
    ];
    #zodiac_signs = zodiac

    from PIL import ImageFont, ImageDraw, Image

    font = ImageFont.truetype("Symbola_hint.ttf", 60)
    for idx, c in enumerate(zodiac_signs):
        path = zodiac_path(idx)
        if os.path.exists(path):
            continue
        # find the size of the endered char
        im = Image.new("L", (800, 100), (255,))
        draw = ImageDraw.Draw(im)
        width, height = draw.textsize(c, font=font)
        # create an image just big enough to hold the char
        im = Image.new("L", (width, height), (0,))
        draw = ImageDraw.Draw(im)
        draw.text((0, 0), c, font=font, fill=(1,), stroke_width=2)
        print("creating", path, file=sys.stderr)
        im.save(path)

class Rete(SCAD):
 
    def __init__(self, filename, config):
        super().__init__(filename)
        self.config = config

        create_zodiac()

        from astrolabe import r_eq, r_can, r_dec
        self.rad_capricorn = config.size/2
        self.rad_equator = r_eq(self.rad_capricorn)
        self.rad_cancer = r_can(self.rad_equator)
        print(self.rad_capricorn, self.rad_equator, self.rad_cancer, file=sys.stderr)

        print("$fn = 100;", file=self.f)
        self.r_dec = r_dec
        self.star_w = self.rad_equator / 6

    def circle(self, r=None):
        self.function("circle", r=r)

    def ticks(self, h, x, r, length, step, size, minus=0):
        #print("#", end='', file=self.f)
        with Intersection(self):
            self.xform("translate", v=[ x, 0, h+0.01, ])
            with Difference(self):
                # ecliptic disc
                self.cylinder(h=disc_thick+0.01, r1=r+0.01, r2=r+0.01)
                self.cylinder(h=disc_thick, r1=r-minus-0.01, r2=r-minus-0.01)
 
            with Union(self):
                for angle in range(0, 360, step):
                    self.xform("rotate", a=[ 0, 270, angle, ])
                    self.function("cube", size=[ disc_thick*3, size, r*2 ])

    def ecliptic(self):
        # Ecliptic
        x0 = self.rad_capricorn
        x1 = -self.rad_cancer
        x = (x0 + x1) / 2.0
        r = (x0 - x1) / 2.0
        with Difference(self):
            self.xform("translate", v=[ x, 0, 0, ])
            with Union(self):
                with Difference(self):
                    with Union(self):
                        self.cylinder(h=disc_thick, r1=r)
                        self.xform("translate", v=[ 0, 0, disc_thick-0.01, ])
                        self.cylinder(h=disc_thick, r1=r, r2=r-chamfer)
                    self.xform("translate", v=[ 0, 0, -0.01, ])
                    self.cylinder(h=(disc_thick*2)+0.02, r1=r-ecliptic_w)
        
            self.ticks(disc_thick, x, r, chamfer*2, 30, 0.75, ecliptic_w)
            self.ticks(disc_thick, x, r, chamfer*2, 5, 0.5, chamfer)

        # label ecliptic with Zodiac
        self.comment("label ecliptic with Zodiac")
        for idx in range(0, 12):
            path = zodiac_path(idx)
            scale = 1/12
            angle = 90 + (idx * 30) + 15 + 5
            rangle = radians(angle)

            rr = r - ecliptic_w + 0.5
            # solve intersection with eliptic for angle from origin
            a = x * math.cos(rangle)
            c = x * math.sin(rangle)
            b = math.sqrt((rr*rr) - (c * c))
            z = cmath.rect(a + b, rangle)
            self.xform("translate", v= [ z.real, z.imag, disc_thick*2 ])
            zz = complex(x, 0)
            zzz = z - zz
            beta = cmath.phase(zzz)
            self.xform("rotate", a= [ 0, 0, degrees(beta) -90 - 5 ])
            self.xform("scale", v= [ scale*1.5, scale, text_h*3 ])
            self.function("surface", file=f'"{path}"')

    def ecliptic_cut(self):
        self.comment("ecliptic_cut")

        x0 = self.rad_capricorn
        x1 = -self.rad_cancer
        x = (x0 + x1) / 2.0
        r = (x0 - x1) / 2.0
        self.xform("translate", v=[ x, 0, -0.01, ])
        self.cylinder(h=(disc_thick*2)+0.02, r1=r-ecliptic_w)
 
    def star_mount(self, name, d, angle):
        w = self.star_w

        self.xform("rotate", a=angle)
        with Hull(self):
            self.xform("translate", v=[ w, -w/2, 0, ])
            self.function("cube", size=[ d-w, w, disc_thick*2 ] )
            points = [
                [ 0, 0, ],
                [ w, w/2 ],
                [ w, -w/2 ],
            ]
            self.xform("linear_extrude", height=1)
            self.function("polygon", points=points)

    stars_skip = [
        "Polaris",
        "Dubhe",
        "Sirius",
        "Mirzam",
        "Castor",
        "Pollux",
        "Elnath",
        "Alcaid",
        "Alnilam",
        "Alnitak",
        "Regulus", 
    ]

    star_info = {
        "Altair" : (0, None, 0.5),
        "Procyon" : (0, None, 0.5),
        "Vega" : (180, "Vga", 0.5),
        "Deneb" : (180, "Db", 0.35),
        "Mirfak" : (250, "Mrk", 0.2),
        "Aldebaran" : (180, " ", 0.2),
        "Alhena" : (180, " ", 0.2),
        "Alioth" : (290, "Al", 0.2),
        "Alkaid" : (290, None, 0.35),
        "Betelgeuse" : (20, "Betelgeus", 0.6),
        "Bellatrix" : (25, None, 0.55),
        "Menkalinan" : (150, "Menkl", 0.4),
        "Capella" : (180, "Cp", 0.3),
        "Alphard" : (0, "Alp.", 0.25),
        "Rigel" : (0, "Rigl", 0.25),
        "Spica" : (300, "Spica", 0.4),
        "Arcturus" : (0, "Arctrs", 0.42),
    }

    def star(self, name, star):

        if name in self.stars_skip:
            return

        setting = self.star_info.get(name) or (0, name, 0.2)

        #print(name, float(star.a_ra), float(star.a_dec), star.mag, file=sys.stderr)
        r = self.r_dec(self.rad_equator, degrees(star.a_dec))
        if r > self.rad_capricorn:
            return

        a = float(star.a_ra) + radians(90)
        #print(name, r, a, star.mag)
        z = cmath.rect(r, a)
        self.xform("translate", v= [ z.real, z.imag, 0 ])
        text_height = 3.8;
        with Union(self):
            rot = setting[0] + degrees(a)

            # offset from star tip to main body
            z = cmath.rect(self.star_w, radians(rot))
            # move the text down 1/2 a line to centre in the star pointer
            z += cmath.rect(text_height/2, radians(rot) + radians(270))

            self.star_mount(name, self.rad_equator * setting[2], rot)

            self.xform("translate", v= [ z.real, z.imag, (disc_thick*2) - 0.01 ])
            self.text(text=setting[1] or name, height=text_height, rotation=rot, depth=text_h)
 
    def stars(self):
        for name in stars.stars.keys():
            try:
                star = stars.star(name)
            except KeyError:
                raise Exception(name, stars.stars.keys())
            star.compute()
            if star.mag > 2.0:
                continue # too dim
            self.star(name, star)

    def draw(self):

        outer_cut_angle = 26
        a = radians(outer_cut_angle)
        radius = self.rad_capricorn
        d = radius / math.tan(a)

        with Difference(self):
            with Union(self):
                with Difference(self):
                    with Union(self):
                        # outer disc
                        self.comment("outer disc")
                        self.xform("linear_extrude", height=disc_thick*2)
                        with Difference(self):
                            # outer disc
                            self.circle(r=radius)
                            self.circle(r=radius-outer_disc_w)
                            points = [
                                [ 0, 0 ],
                                [ radius, -d ],
                                [ radius, d ],
                            ]
                            self.function("polygon", points=points)

                        # connecting bar to ecliptic
                        self.comment("connecting bar to ecliptic")
                        w = outer_disc_w
                        d = self.rad_capricorn
                        for a in [ outer_cut_angle+180, -outer_cut_angle ]:
                            self.xform("rotate", a=a )
                            self.xform("translate", v = [ 0, d/2, 0 ] )
                            self.xform("linear_extrude", height=disc_thick*2)
                            self.function("square", size=[w, d], center=True)

                    #self.xform("#translate", v = [ 0, 0, 0 ] )
                    self.ecliptic_cut()

                # connecting outer ring, centre, ecliptic
                self.xform("translate", v = [ -w/2, 0, 0 ] )
                self.xform("linear_extrude", height=disc_thick*2)
                self.function("square", size=[w, d*2 - 1], center=True)

                self.ecliptic()
                self.stars()

                # centre mount
                self.xform("linear_extrude", height=disc_thick*2)
                self.circle(r=centre_surround + self.config.hole)

            # centre hole
            self.xform("translate", v = [ 0, 0, -0.01 ] )
            self.xform("linear_extrude", height=disc_thick*2 + 0.02)
            self.circle(r=self.config.hole)


if __name__ == "__main__":
    rete = Rete()
    rete.draw()

#   FIN
