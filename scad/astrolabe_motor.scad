
// https://github.com/chrisspen/gears
// copy gears.scad to ~/.local/share/OpenSCAD/libraries 
include <gears.scad>

include <nuts.scad>
include <stepper.scad>
use <../cad/rete.scad>

bore = m3_hole_r*2;
width = 6;
teeth = 30;
pressure_angle = 20;
helix_angle = 20;
modul = 1;
opto_dx = 8; // opto offset from centre
opto_dz = 3; // thickness of opto disc
led_r = 3/4; // opto hole

// spindle 
spindle_thick = 1.5;
clear = 0.25;
shaft_join_thick = 2;

base_dz = motor_flange_dz + width + (width + opto_dz) + 1;
base_thick = 2;

function rads(idx)  =
    let (r = (bore/2) + ((idx+1)*clear) + (idx * spindle_thick))
    [ r, r+spindle_thick ];

module shaft(idx, h)
{
    sh = rads(idx);
    cylinder(h=h, r1=sh[1], r2=sh[1]);
}

module shaft_cut(idx, h)
{
    sh = rads(idx);
    translate( [ 0, 0, -0.01] )
    cylinder(h=h+0.02, r1=sh[0], r2=sh[0]);
}

module spindle(idx, h)
{
    difference()
    {
        d = modul * teeth;
        r = 0.85 * d/2;
        hh = h-(width+opto_dz);
        union()
        {
            herringbone_gear(modul=modul, tooth_number=teeth, width=width, bore=bore, pressure_angle=pressure_angle, helix_angle=helix_angle);
            translate( [ 0, 0, width+opto_dz-0.01 ] )
            shaft(idx, hh);

            cylinder(h=width+opto_dz, r1=r, r2=r);
        }
        shaft_cut(idx, h+0.02);

        translate( [ -opto_dx+(led_r/2), -r, width ] )
        rotate( [ 0, 0, 90 ] )
        cube( [ r*2, led_r, opto_dz+0.01 ] );
    }
}

module gear_shaft(idx)
{
    hs = [
        base_dz + base_thick + shaft_join_thick,
        base_dz + base_thick - width - opto_dz,
    ];
    h = hs[idx];

    // gear shafts
    d = shaft_join_thick;
    hh = h+shaft_join_thick;
    spindle(idx, hh);
    translate( [ 0, 0, hh-0.01 ] )
    shaft_top(idx, d);
}

    /*
    *
    */

module assembly(show_gear)
{
    translate( [ 0, 0, base_thick ] )
    {
        d = modul * teeth;
        // the motors
        translate( [ d, 0, 0 ] )
        {
            motor_assembly(0, 10);
            if (show_gear)
            translate([ 0, 0, motor_flange_dz ] )
            #cylinder(h=width, r1=d/2, r2=d/2);
        }
        translate( [ -d, 0, 0 ] )
        {
            rotate( [ 0, 0, 180 ] )
            motor_assembly(width+opto_dz, 10);
            if (show_gear)
            {
                translate([ 0, 0, motor_flange_dz+width+opto_dz ] )
                #cylinder(h=width, r1=d/2, r2=d/2);
            }
        }

        if (show_gear)
        {
            offs = 1; // ?????
            translate([ 0, 0, base_dz-offs ] )
            rotate( [ 0, 180, 0 ] )
            #gear_shaft(0);
            translate([ 0, 0, base_dz-offs-(width + opto_dz) ] )
            rotate( [ 0, 180, 0 ] )
            #gear_shaft(1);
        }
    }
}

module assembly_cut()
{
    rr = rads(2);
    echo(rr);
    r = rr[0];
    translate([ 0, 0, -0.01 ] )
    cylinder(h=base_thick+0.02, r1=r, r2=r);
}

function gear_points() = 
    let (offs = modul * teeth / 2)
    [
        [ -offs, -offs ],
        [ offs, offs ],
        [ offs, -offs ],
        [ -offs, offs ],
    ];

module gear_cage()
{
    support_r = m3_hole_r + 2;

    difference()
    {
        for (xy = gear_points())
        {
            translate( [ xy[0], xy[1], 0 ] )
            cylinder(h=base_dz, r1=support_r, r2=support_r);
        }
        for (xy = gear_points())
        {
            h = 20;
            translate( [ xy[0], xy[1], base_dz-h+0.01 ] )
            cylinder(h=h, r1=m3_thread_r, r2=m3_thread_r);
        }
    }

    translate( [ 0, 0, -0.01 ] )
    difference()
    {
        d = base_dz - (2 * (width + opto_dz + 0.5));
        shaft(2, d);
        shaft_cut(2, d);
    }
}

module _gear_top(thick, r)
{
    for (xy = gear_points())
    {
        translate( [ xy[0], xy[1], 0 ] )
        cylinder(h=thick, r1=r, r2=r);
    }
    cylinder(h=thick, r1=r, r2=r);
}

module gear_top(thick)
{
    support_r = m3_hole_r + 2;
    gap = 1;

    difference()
    {
        union()
        {
            hull() _gear_top(thick, support_r);
            _gear_top(thick+gap, support_r);
        }

        translate( [ 0, 0, -0.01 ] )
        _gear_top(thick+gap+0.02, bore/2);
    }
}

    /*
    *
    */

module led_tower(heights, r=5/2)
{
    led_rad = r + 0.1;
    h = max(heights) + led_rad + 2;
    sz = (2 * led_rad) + 2.5;
    pinhole_d = 2;
    step_back = 2;
    step_dz = 10;
    d = 7.5 + pinhole_d;

    difference()
    {
        union()
        {
            hull()
            {
                translate( [ 0, -sz/2, 0 ] )
                cube( [ d, sz, 1 ] );
                translate( [ step_back, -sz/2, step_dz ] )
                cube( [ d, sz, 1 ] );
            }

            translate( [ step_back, -sz/2, step_dz ] )
            cube( [ d, sz, h-step_dz ] );
        }

        translate( [ step_back, 0, 0 ] )
        for (h = heights)
        {
            translate( [ pinhole_d, 0, h] )
            rotate([ 0, 90, 0 ] )
            cylinder(h=d+0.02, r1=led_rad, r2=led_rad);
            translate( [ -0.01, 0, h] )
            rotate([ 0, 90, 0 ] )
            cylinder(h=d+0.02, r1=led_r, r2=led_r);
        }
    }
}

    /*
    *
    */

module _base(thick)
{
    d = modul * teeth;
    s = d + motor_mdx;
    translate( [ s, 0, 0 ] )
    motor_base(thick);
    translate( [ -s, 0, 0 ] )
    rotate([ 0, 0, 180 ] )
    motor_base(thick);
}

module base(thick, show_all=false)
{
    d = modul * teeth;
    s = d + motor_mdx;
    difference()
    {
        hull() _base(thick);
        assembly_cut();
    }

    // brace the base to stop it flexing
    brace_h = motor_base;
    brace_w = 3;
    translate( [ 0, 0, thick-0.01 ] )
    difference()
    {
        union()
        {
            translate( [ -s, d/2, 0 ] )
            cube( [ 2*s, brace_w, brace_h ] );
            translate( [ -s, -d/2, 0 ] )
            cube( [ 2*s, brace_w, brace_h ] );
        }
        translate( [ 0, 0, -0.01 ] )
        _base(brace_h+0.02);
    }

    // stepper mounts
    assembly(show_all);
    translate( [ 0, 0, base_thick ] )
 
    gear_cage();

    led_heights = [ 
        base_dz-width,
        base_dz-(width + opto_dz)-width,
    ];

    translate( [ opto_dx, d/2, 0 ] )
    rotate( [ 0, 0, 90 ] )
    led_tower(led_heights, 5/2);
    translate( [ opto_dx, -d/2, 0 ] )
    rotate( [ 0, 0, 270 ] )
    led_tower(led_heights, 5/2);
}
    
    /*
    *
    */

module shaft_cross(idx, thick)
{
    rr = rads(idx);
    d = rr[1];
    for (angle = [ 0, 90, 180, 270 ] )
    {
        rotate( [ 0, 0, angle ] )
        translate( [ 0, -d/4, 0 ] )
        cube( [ d, d/2, thick+0.02 ] );
    }
}

module shaft_join(idx, thick)
{
    rr = rads(idx);
    difference()
    {
        cylinder(h=thick, r1=rr[1], r2=rr[1]);
        translate( [ 0, 0, -0.01 ] )
        {
            shaft_cross(idx, thick+0.02);
            shaft_cut(idx, thick+0.02);
        }
    }
}

module shaft_top(idx, thick)
{
    intersection()
    {
        shaft(idx, thick);
        difference()
        {
            shaft_cross(idx, thick);
            shaft_cut(idx, thick);
        }
    }
}

    /*
    *
    */

module clock_face(r, thick)
{
    difference()
    {
        h = thick * 6;
        union()
        {
            cylinder(h=thick, r1=r, r2=r);

            translate( [ 0, 0, thick-0.01] )
            intersection()
            {
                cylinder(h=h, r1=r, r2=0);

                for (angle = [ 0 : 15: 360 ])
                {
                    s = 2;
                    rotate( [ 0, 0, angle ] )
                    translate( [ -r, -s/2, 0] )
                    cube([ 2*r, s, h ] );
                }

            }
        }

        rr = rads(1);
        hole_r = rr[1] +clear;
        translate( [ 0, 0, -0.01] )
        cylinder(h=h+thick+0.02, r1=hole_r, r2=hole_r);

        d = modul * teeth;
        translate( [ d+motor_mdx, 0, thick-0.01] )
        motor(h+thick);
    }
}

module make_rete()
{
    rete();
    h = 3;
    idx = 1;
    shaft_join(idx, h);
    rr = rads(idx);
    outer = rr[idx];
    echo(outer);
    difference()
    {
        cylinder(h=h+0.01, r1=outer+clear+0.1, r2=outer+clear+0.1);
        translate([ 0, 0, -0.01] )
        cylinder(h=h+0.03, r1=outer, r2=outer);
    }
}

module sun_hand()
{
    h = 3;

    translate( [ 0, 0, 0.01 - h ] )
    shaft_join(0, h+0.01);

    rr = rads(1);
    inner = rr[1];
    outer = rr[1];

    // centre plug down the shaft
    plug = bore/2;
    plug_h = h * 10;
    translate( [ 0, 0, 0.01 - (plug_h - h) ] )
    cylinder(h=plug_h, r1=plug, r2=plug);

    // tip circle radius
    tip_r = 2;
    hand_r = outer;
    big = 10 + (outer_clock_r * 2);
    difference()
    {
        hull()
        {
            // outer shape of the pointer
            translate( [ outer_clock_r, 0, 0 ] )
            cylinder(h=h, r1=tip_r, r2=tip_r);
            cylinder(h=h, r1=hand_r, r2=hand_r);
        }

        // cut off half the pointer
        translate( [ 0, 0, -0.01 ] )
        cube([ big, outer, h+1] );
        // bevel by rotatingn the 1/2 cut along the line of the pointer
        translate( [ 0, 0, 1 ] )
        rotate( [ 45, 0, 0] )
        cube([ big, outer, h+1] );
    }

    // redraw the whole centre mount (the first one has been cut in half)
    cylinder(h=h, r1=hand_r, r2=hand_r);

    // draw the Sun
    //translate( [ capricorn_dia/2, 0, 0 ] )
    //cylinder(h=h/2, r1=hand_r, r2=hand_r);
}

    /*
    *
    */

// Set true for visualisation of whole gear assembly
// false for actual generation
show_all = true;

// Set the various flags to true to generate ..

if (false) gear_top(3);

capricorn_dia = 155;
outer_clock_r = 1.2 * (capricorn_dia/2);

if (false)
{
    // Generate Sun Hand
    scale( [ 1, 1, -1] )
    sun_hand();
}

if (true)
{
    // main assembly, motor mount, face
    base(base_thick, show_all);

    clock_face(outer_clock_r, base_thick);

    if (show_all)
    translate( [ 0, 0, base_dz + base_thick + 2 + 3 ] )
    rotate( [ 180, 0, 0 ] )
    #gear_top(3);
}

if (false)
{
    // gear + shafts
    translate( [ 35, 0, 0 ] )
    gear_shaft(0);
    gear_shaft(1);
}

if (false)
difference()
{
    // drive gear mounting to stepper
    herringbone_gear(modul=modul, tooth_number=teeth, width=width, bore=3/2, pressure_angle=pressure_angle, helix_angle=-helix_angle);
    motor_spindle();
}

if (false)
{
    make_rete();
}

//  FIN
