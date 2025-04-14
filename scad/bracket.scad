
include <nuts.scad>

h = 30;
h2 = 12;
w = 4;
d = 8;
d2 = 12;


$fn = 100;

difference()
{
    translate( [ 0, 0, 0 ] )
    {
        translate( [ h2, 0, 0 ] )
        cube( [ h-h2, w, d ] );

        translate( [ 0, w, 0 ] )
        cube( [ w, d2, d ] );

        translate( [ 0, w, 0 ] )
        rotate( [ 0, 0, -18 ] )
        cube( [ 13, w, d ] );
    }

    translate( [ w+0.01, d2, w ] )
    rotate( [ 0, 270, 0 ] )
    cylinder(h=w+0.02, r1=m3_hole_r, r2=m3_hole_r);
}

//  FIN
