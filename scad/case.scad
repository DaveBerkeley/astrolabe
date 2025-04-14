
include <nuts.scad>

face_r = (155 * 1.2) / 2;
depth = 55;
wall_thick = 2;
surround = 4;
plinth = 5;
face_thick = 2;
mount_h = 25;

$fn = 500;

module outer (thick, r)
{
    hull()
    {
        cylinder(h=thick, r1=r, r2=r);
        s = 2 * r;
        translate([ -r, r, 0 ] )
        cube( [ s, plinth, thick ] );
    }
}

if (false)
difference()
{
    outer(wall_thick, face_r+surround);
    translate([ 0, 0, -0.01 ] )
    cylinder(h=wall_thick+0.02, r1=face_r, r2=face_r);
}

module surround()
{
    difference()
    {
        h = depth;
        outer(h, face_r+surround);
        translate([ 0, 0, -0.01 ] )
        cylinder(h=h+0.02, r1=face_r, r2=face_r);
    }
}

difference()
{
sc = 1; // 0.2;
//translate([ 0, 0, sc*(-depth+4)] )
scale([ sc, sc, sc ])
{
    surround();
    // back plate
    //cylinder(h=wall_thick, r1=face_r+0.01, r2=face_r+0.01);

    

    // face support
    s = 15;
    rim = 5;
    translate([ 0, 0, depth -face_thick -s - 0.01 ] )
    difference ()
    {
        cylinder(h=s, r1=face_r+0.01, r2=face_r+0.01);
        translate([ 0, 0, -0.01 ] )
        cylinder(h=s+0.02, r1=face_r+0.01, r2=face_r-rim+0.01);

        for (angle = [ 0 : 15 : 360 ] )
        {
            d = 3;
            wx = (rim * 2);
            wy = 2;
            translate( [ face_r * sin(angle), face_r * cos(angle), 0.01 ] )
            rotate( [ 0, 0, 90-angle, ] )
            translate( [ -wx/2, -wy/2, 0 ] )
            cube( [ wx, wy, s+0.02 ] );
        }
    }


    // mounting for rear panel
    for (angle = [ 0 : 90 : 360 ] )
    {
        translate( [ face_r * sin(angle), face_r * cos(angle), 0.01 ] )
        difference()
        {
            s = m3_thread_r + wall_thick;
            cylinder(h=mount_h, r1=s, r2=s);
        }
    }
}

    // mounting for rear panel
    for (angle = [ 0 : 90 : 360 ] )
    {
        translate( [ face_r * sin(angle), face_r * cos(angle), -0.01 ] )
        difference()
        {
            #cylinder(h=mount_h, r1=m3_thread_r, r2=m3_thread_r);
        }
    }

if (false)
{
    big = 250;
    translate( [ -big/2, -big/2, -big] )
    cube([ big, big, big ] );
}

}


//  FIN
