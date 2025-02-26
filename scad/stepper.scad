
include <nuts.scad>

// 28BYJ-48 stepper motor
// for drawings see LinuxNotes_23-Dec-2024

motor_r = (28/2) + 0.25;
motor_h = 19;
motor_base = 4;
motor_dm = 34;
motor_xx = 18;
motor_yy = 17.5;
motor_mdx = 8;
motor_c = 6;
motor_flange_dz = motor_h + 3.5;

module motor_spindle()
{
    r = 5/2;
    d = 3;
    h = 6;

    intersection()
    {
        cylinder(h=h, r1=r, r2=r);
        translate( [ -r, -d/2, 0 ] )
        cube( [ 2*r, d, h] );
    }
}

module motor(h)
{
    cylinder(h=h, r1=motor_r, r2=motor_r);
    translate( [ 0, -motor_yy/2, 0 ] )
    cube( [ motor_xx, motor_yy, h ] );
}

function motor_xy() =
    [ 
        [ 0, motor_dm/2 ],
        [ 0, -motor_dm/2 ],
    ];

module motor_mount(h)
{
    plus = 1;
    for (xy = motor_xy())
    {
        translate( [ xy[0], xy[1], 0 ] )
        cylinder(h=h, r1=m4_thread_r+2, r2=m4_thread_r+2);
    }
}

module motor_cut(h)
{
    for (xy = motor_xy())
    {
        translate( [ xy[0], xy[1], motor_h-h ] )
        cylinder(h=h, r1=m4_thread_r, r2=m4_thread_r);
    }

    translate( [ motor_xx-0.01, -motor_c/2, motor_h-motor_c ] )
    cube( [ 3, motor_c, motor_c ] );
}

module motor_base(h)
{
    rim_gain = 1.1;
    scale( [ rim_gain, rim_gain, 1 ] )
    hull()
    {
        motor(h);
        motor_mount(h);
    }
}

module motor_assembly(h, d)
{
    translate( [ motor_mdx, 0, 0 ] )
    {
        motor_base(h);

        translate( [ 0, 0, h-0.01 ] )
        difference()
        {
            union()
            {
                motor_mount(motor_h);
                motor_base(motor_h/5);
            }

            translate( [ 0, 0, -0.01 ] )
            motor(motor_h+0.02);
            translate( [ 0, 0, 0.01 ] )
            motor_cut(d);
        }
    }
}

//motor_assembly(2, 10);

//  FIN
