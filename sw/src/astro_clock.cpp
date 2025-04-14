

#if defined(NOTHING)

#include "panglos/debug.h"
#include "panglos/object.h"
#include "panglos/device.h"

#include "cli/src/cli.h"

#include "panglos/app/event.h"
#include "panglos/app/cli_server.h"
#include "panglos/app/devices.h"

using namespace panglos;

Device _board_devs[] = {
    //Device("led", 0, gpio_init, (void*) & led_def),
    Device(0, 0, 0, 0, 0),
};

void board_init()
{
    PO_DEBUG("");
    
    if (Objects::objects->get("net"))
    {
        EventHandler::add_handler(Event::INIT, net_cli_init, 0);    
    }
}

Device *board_devs = _board_devs;

#endif  //  NOTHING


#if defined(ASTRO_CLOCK)

#include <driver/gpio.h>

#include "panglos/debug.h"
#include "panglos/object.h"
#include "panglos/device.h"
#include "panglos/esp32/gpio.h"
#include "panglos/drivers/motor.h"
#include "panglos/time.h"
#include "panglos/date.h"

#include "cli/src/cli.h"

#include "panglos/app/event.h"
#include "panglos/app/cli_server.h"
#include "panglos/app/devices.h"

#include "stepper.h"
#include "ntp.h"
#include "board.h"

using namespace panglos;

    /*
     *
     */

#if defined(ESP32_S2_MINI)

//  STEPPER_MOTOR board

static const GPIO_DEF led_def = { GPIO_NUM_15, ESP_GPIO::OP, false };

#define SWITCH ESP_GPIO::IP | ESP_GPIO::PU
#define LED    ESP_GPIO::OP
#define MOTOR  ESP_GPIO::OP

static const GPIO_DEF b0_def = { GPIO_NUM_14, LED, true };
static const GPIO_DEF b1_def = { GPIO_NUM_13, LED, true };
static const GPIO_DEF b2_def = { GPIO_NUM_10, SWITCH, false };
static const GPIO_DEF b3_def = { GPIO_NUM_8,  SWITCH, false };

static const GPIO_DEF m00_def = { GPIO_NUM_9, MOTOR, false };
static const GPIO_DEF m01_def = { GPIO_NUM_6, MOTOR, false };
static const GPIO_DEF m02_def = { GPIO_NUM_7, MOTOR, false };
static const GPIO_DEF m03_def = { GPIO_NUM_4, MOTOR, false };

static const GPIO_DEF m10_def = { GPIO_NUM_5, MOTOR, false };
static const GPIO_DEF m11_def = { GPIO_NUM_2, MOTOR, false };
static const GPIO_DEF m12_def = { GPIO_NUM_3, MOTOR, false };
static const GPIO_DEF m13_def = { GPIO_NUM_1, MOTOR, false };

static const char *m0_names[] = { "m00", "m01", "m02", "m03", 0 };
static const char *m1_names[] = { "m10", "m11", "m12", "m13", 0 };

const struct STEPPER_DEF s0_def = { m0_names, 4096 };
const struct STEPPER_DEF s1_def = { m1_names, 4096 };

Device _board_devs[] = {
    Device("led", 0, gpio_init, (void*) & led_def),
    // leds / opto detectors to detect the rotation of the gear wheels
    Device("led0", 0, gpio_init, (void*) & b0_def),
    Device("led1", 0, gpio_init, (void*) & b1_def),
    Device("sense0", 0, gpio_init, (void*) & b2_def),
    Device("sense1", 0, gpio_init, (void*) & b3_def),

    // Stepper motors :  4 coils per stepper
    DEV_GPIO("m00", 0, & m00_def),
    DEV_GPIO("m01", 0, & m01_def),
    DEV_GPIO("m02", 0, & m02_def),
    DEV_GPIO("m03", 0, & m03_def),

    DEV_GPIO("m10", 0, & m10_def),
    DEV_GPIO("m11", 0, & m11_def),
    DEV_GPIO("m12", 0, & m12_def),
    DEV_GPIO("m13", 0, & m13_def),

    // 2 stepper motors
    Device("step0", m0_names, stepper_init, (void*) & s0_def),
    Device("step1", m1_names, stepper_init, (void*) & s1_def),

    Device(0, 0, 0, 0, 0),
};

#endif // defined(ESP32_S2_MINI)

    /*
     *
     */

struct Clock
{
    enum State
    {
        ST_MANUAL,
        ST_AUTO, // follow date/time
        ST_CALIBRATE,
    };

    enum CalState 
    {
        CAL_NONE,
        CAL_ZERO,
        CAL_SEARCH,
        CAL_CHECK,
        CAL_MOVE,
        CAL_DONE,
    };

    struct Dial
    {
        Stepper *motor;
        GPIO *sense;
        int p1;
        int p2;    
    };

    static const int num_dials = 2;
    State state;
    Dial dials[num_dials];

    struct Cal
    {
        CalState state;
        bool gpio;
        int idx;
        State next_state;
        int centre[num_dials];
    };

    Cal cal;
};

    /*
     *
     */

static const LUT state_lut[] = {
    {   "ST_AUTO", Clock::ST_AUTO, },
    {   "ST_MANUAL", Clock::ST_MANUAL, },
    {   "ST_CALIBRATE", Clock::ST_CALIBRATE, },
    { 0, 0 },
};

static const LUT cal_lut[] = {
    {   "CAL_NONE", Clock::CAL_NONE, },
    {   "CAL_ZERO", Clock::CAL_ZERO, },
    {   "CAL_SEARCH", Clock::CAL_SEARCH, },
    {   "CAL_CHECK", Clock::CAL_CHECK, },
    {   "CAL_MOVE", Clock::CAL_MOVE, },
    {   "CAL_DONE", Clock::CAL_DONE, },
    { 0, 0 },
};

    /*
     *
     */

static void cal_start(Clock *clock, int idx)
{
    ASSERT(clock);
    ASSERT((idx >= 0) && (idx <= 1));
    if (clock->state != Clock::ST_CALIBRATE)
    {
        clock->cal.next_state = clock->state;
    }
    clock->state = Clock::ST_CALIBRATE;
    clock->cal.idx = idx;
    clock->cal.state = Clock::CAL_ZERO;
    Clock::Dial *dial = & clock->dials[idx];
    dial->p1 = dial->p2 = 0;
    dial->motor->rotate(10);
}

static void cal_irq(Clock *clock)
{
    Clock::Dial *dial = & clock->dials[clock->cal.idx];
    if (!dial->motor) return;
    if (!dial->sense) return;
    const int steps = dial->motor->get_steps();
    const int hi = steps - 10;

    switch (clock->cal.state)
    {
        case Clock::CAL_ZERO :
        {
            if (dial->motor->ready())
            {
                clock->cal.state = Clock::CAL_SEARCH;
                clock->cal.gpio = dial->sense->get();
                dial->motor->seek(hi);
            }
            break;
        }
        case Clock::CAL_SEARCH :
        {
            const bool gpio = dial->sense->get();
            const int posn = dial->motor->position();
            if (posn == hi)
            {
                clock->cal.state = Clock::CAL_CHECK;
                break;
            }
            if (gpio != clock->cal.gpio)
            {
                if (dial->p1 == 0)
                {
                    if (!gpio)
                    {
                        // earliest hi->lo transition
                        dial->p1 = posn;
                    }
                } else 
                {
                    if (gpio)
                    {
                        //  latest lo->hi transition
                        dial->p2 = posn;
                    }
                }
            }
            clock->cal.gpio = gpio;
            break;
        }
        case Clock::CAL_CHECK :
        {
            // Check that the sensor region is good
            const int near_lo = steps / 20;
            const int near_hi = steps - (steps / 20);
            const bool move = 
                    (dial->p1 < near_lo) || (dial->p1 > near_hi)
                    || (dial->p2 < near_lo) || (dial->p2 > near_hi);
            if (move)
            {
                // move the motor away from the 0000 region
                clock->cal.state = Clock::CAL_MOVE;
                dial->motor->seek(steps / 2);
                return;
            }

            clock->cal.state = Clock::CAL_DONE;
            break;            
        }
        case Clock::CAL_MOVE :
        {
            if (dial->motor->position() == (steps/2))
            {
                // re-zero the motor away from the 0000 region
                dial->motor->zero();
                cal_start(clock, clock->cal.idx);
            }
            break;
        }
        case Clock::CAL_DONE :
        {
            clock->cal.centre[clock->cal.idx] = (dial->p1 + dial->p2) / 2;
            clock->cal.idx += 1;

            if (clock->cal.idx < clock->num_dials)
            {
                cal_start(clock, clock->cal.idx);
            }
            else
            {
                clock->cal.idx = 0;
                clock->cal.state = Clock::CAL_NONE;
                clock->state = clock->cal.next_state;
            }
            break;
        }
        case Clock::CAL_NONE :
        default :
            break;
    }
}

    /*
     *
     */

static int dial_goto(Clock *clock, int idx, int mul, int div)
{
    ASSERT((idx >= 0) && (idx < clock->num_dials));
    Clock::Dial *dial = & clock->dials[idx];
    if (!dial->motor) return -1;
    const int steps = dial->motor->get_steps();
    int posn = (steps * mul) / div;
    posn += clock->cal.centre[idx];
    posn %= steps;
    dial->motor->rotate(posn);
    return posn;
}

    /*
     *
     */

static void on_date_time(Clock *clock, struct DateTime *dt)
{
    const int m = dt->m;
    const int h = dt->h;
    const int y = dt->yy % 100;

    const int day = (((h + 12) % 24) * 60) + m;
    const int day_div = 60 * 24;

    const int yd = DateTime::year_day(y, dt->mm, dt->dd);
    const int days = DateTime::days_in_year(y);

    // number of days between Winter solstice and New Year
    const int solstice = DateTime::year_day(y, 12, 21);
    const double offset = (DateTime::days_in_year(y) - solstice) / double(days);

    const double dd = day / double(day_div);
    const double yy = yd / double(days);
    int rete = (yy * 360) + (dd * 360) + (offset * 360);
    //if (rete < 0) rete += 360;

    dial_goto(clock, 0, day, day_div);
    dial_goto(clock, 1, rete, 360);

    PO_DEBUG("%04d/%02d/%02d %02d:%02d:%02d %d %d",
            dt->yy,
            dt->mm,
            dt->dd,
            dt->h,
            dt->m,
            dt->s,
            int(360 * dd), 
            int(rete)
            );
}

static bool on_date_time(void *arg, Event *event, Event::Queue *)
{
    ASSERT(arg);
    struct Clock *clock = (struct Clock *) arg;
    ASSERT(event);
    ASSERT(event->type == Event::DATE_TIME);

    if (event->payload.dt.yy < 2025)
        return false;

    if (clock->state != Clock::ST_AUTO) return true;

    struct DateTime dt = {
        .yy = event->payload.dt.yy,
        .mm = event->payload.dt.mm,
        .dd = event->payload.dt.dd,
        .h = event->payload.dt.h,
        .m = event->payload.dt.m,
        .s = event->payload.dt.s,
    };

    on_date_time(clock, & dt);
    return true;
}

    /*
     *
     */

static void astro_cmd_handler(struct CLI *cli, struct CliCommand *)
{
    Clock *clock = (Clock*) Objects::objects->get("clock");
    if (!clock)
    {
        cli_print(cli, "Clock not found%s", cli->eol);
        return;
    }
 
    const char *s = cli_get_arg(cli, 0);
    if (s)
    {
        cli_print(cli, "unknown command '%s'%s", s, cli->eol);
        return;
    }
 
    cli_print(cli, "state=%s%s", lut(state_lut, clock->state), cli->eol);

    cli_print(cli, "cal=%s idx=%d next=%s", 
            lut(cal_lut, clock->cal.state), 
            clock->cal.idx,
            lut(state_lut, clock->cal.next_state));
    for (int centre : clock->cal.centre)
    {
        cli_print(cli, " p=%d", centre);
    }
    cli_print(cli, "%s", cli->eol);

    for (Clock::Dial & dial : clock->dials)
    {
        if (!dial.motor)
        {
            cli_print(cli, "no motor%s", cli->eol);
            continue;
        }
        cli_print(cli, "posn=%d t=%d p1=%d p2=%d %s", 
            dial.motor->position(), 
            dial.motor->get_target(), 
            dial.p1,
            dial.p2,
            cli->eol);
    }
}

static void state_cmd(struct CLI *cli, struct CliCommand *cmd)
{
    Clock *clock = (Clock*) Objects::objects->get("clock");
    if (!clock)
    {
        cli_print(cli, "Clock not found%s", cli->eol);
        return;
    }
 
    static const LUT state_lut[] = {
        {   "auto", Clock::ST_AUTO, },
        {   "man", Clock::ST_MANUAL, },
        {   "cal", Clock::ST_CALIBRATE, },
        { 0, 0 },
    };
 
    Clock::State state = (Clock::State) rlut(state_lut, cmd->cmd);

    if (state == Clock::ST_CALIBRATE)
    {
        cal_start(clock, 0);
    }

    clock->state = state;
    cli_print(cli, "enter %s mode%s", lut(state_lut, state), cli->eol);
}

static void goto_cmd_handler(struct CLI *cli, struct CliCommand *cmd)
{
    Clock *clock = (Clock*) Objects::objects->get("clock");
    if (!clock)
    {
        cli_print(cli, "Clock not found%s", cli->eol);
        return;
    }

    const char *s = cli_get_arg(cli, 0);
    if (!s)
    {
        cli_print(cli, "yyyymmddThhmmss expected%s", cli->eol);
        return;
    }

    struct DateTime dt;
    if (!dt.parse_datetime(s))
    {
        cli_print(cli, "error parsing '%s'%s", s, cli->eol);
        return;
    }

    clock->state = Clock::ST_MANUAL;
    on_date_time(clock, & dt);

    cli_print(cli, "goto %04d/%02d/%02d %02d:%02d:%02d%s", 
            dt.yy, dt.mm, dt.dd, 
            dt.h, dt.m, dt.s, 
            cli->eol);
}
 
    /*
     *
     */

static CliCommand goto_cmd   = { 
    .cmd="goto", 
    .handler=goto_cmd_handler, 
    .help="goto yyyymmddThhmmss", 
    .next=0
};
static CliCommand cal_cmd   = { 
    .cmd="cal", 
    .handler=state_cmd, 
    .help="calibrate position", 
    .next=& goto_cmd,
};
static CliCommand man_cmd   = { 
    .cmd="man", 
    .handler=state_cmd, 
    .help="manual mode : don't control motor", 
    .next=& cal_cmd  
};
static CliCommand auto_cmd  = { 
    .cmd="auto", 
    .handler=state_cmd, 
    .help="track date/time", 
    .next=& man_cmd
};
static CliCommand astro_cmd = { 
    .cmd="astro", 
    .handler=astro_cmd_handler, 
    .help="display state", 
    .subcommand=& auto_cmd 
};

    /*
     *
     */

bool astro_cli_init(void *, Event *, Event::Queue *)
{
    CLI *cli = (CLI*) Objects::objects->get("cli");
    if (cli)
    {
        cli_append(cli, & astro_cmd);
    }
    return false; // INIT handlers must return false so multiple handlers can be run
}

static void step_cb(void *arg)
{
    // called in timer interrupt
    ASSERT(arg);
    Clock *clock = (Clock*) arg;

    if (clock->state == Clock::ST_CALIBRATE)
    {
        cal_irq(clock);
    }
}

void board_init()
{
    PO_DEBUG("");

    EventHandler::add_handler(Event::INIT, astro_cli_init, 0);
 
    static struct Clock clock;

    clock.dials[0].motor = (Stepper*) Objects::objects->get("step0");
    clock.dials[0].sense = (GPIO*) Objects::objects->get("sense0");

    clock.dials[1].motor = (Stepper*) Objects::objects->get("step1");
    clock.dials[1].sense = (GPIO*) Objects::objects->get("sense1");

    Objects::objects->add("clock", & clock);
 
    clock.state = Clock::ST_AUTO;
    cal_start(& clock, 0);
    run_timers(step_cb, & clock);

    if (Objects::objects->get("net"))
    {
        Time::tick_t period = 100 * 10;
        ntp_start(period);
        EventHandler::add_handler(Event::INIT, net_cli_init, 0);    
        EventHandler::add_handler(Event::DATE_TIME, on_date_time, & clock);
    }
}

Device *board_devs = _board_devs;

#endif  //   ASTRO_CLOCK

//  FIN
