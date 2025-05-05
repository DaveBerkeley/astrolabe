
#include <string.h>

#include "panglos/debug.h"

#include "panglos/list.h"
#include "panglos/object.h"
#include "panglos/time.h"
#include "panglos/device.h"

#include "panglos/drivers/timer.h"
#include "panglos/drivers/motor.h"
#include "panglos/esp32/gpio.h"

#include "cli/src/cli.h"

#include "panglos/app/cli.h"

#include "stepper.h"

using namespace panglos;

Stepper *make_stepper(int *pins, int cycle)
{
    GPIO *gpios[4];

    for (int i = 0; i < 4; i++)
    {
        ESP_GPIO *gpio = new ESP_GPIO(pins[i], ESP_GPIO::OP, false, false, 0);
        gpios[i] = gpio;
    }

    MotorIo_4 *motor = new MotorIo_4(gpios[0], gpios[1], gpios[2], gpios[3]);
    Stepper *stepper = new Stepper(cycle, motor);
    return stepper;
}

Stepper *make_stepper(const char **names, int cycle)
{
    GPIO *gpios[4];

    for (int i = 0; i < 4; i++)
    {
        const char *name = names[i];
        ASSERT(name);
        GPIO *gpio = (GPIO*) Objects::objects->get(name);
        ASSERT(gpio);
        gpios[i] = gpio;
    }

    MotorIo_4 *motor = new MotorIo_4(gpios[0], gpios[1], gpios[2], gpios[3]);
    Stepper *stepper = new Stepper(cycle, motor);
    return stepper;
}

    /*
     *
     */

struct StepperItem {
    Stepper *stepper;
    struct StepperItem *next;
    static struct StepperItem **get_next(struct StepperItem *item) { return & item->next; }
};

static List<struct StepperItem*> steppers(StepperItem::get_next);

    /*
     *
     */

static void cmd_motor(CLI *cli, CliCommand *cmd)
{
    const char *name = (const char *) cmd->ctx;
    ASSERT(name);
    Stepper *stepper = (Stepper*) Objects::objects->get(name);
    ASSERT(stepper);

    int idx = 0;
    const char *s = cli_get_arg(cli, idx++);
    if (!s)
    {
        cli_print(cli, "command expected%s", cli->eol);
        return;
    }

    if (!strcmp("zero", s))
    {
        cli_print(cli, "zero the position%s", cli->eol);
        stepper->zero(stepper->position());
        return;
    }

    if (!strcmp("get", s))
    {
        const int i = stepper->position();
        cli_print(cli, "%d%s", i, cli->eol);
        return;
    }

    int value = 0;
    if (!cli_parse_int(s, & value, 0))
    {
        cli_print(cli, "number expected%s", cli->eol);
        return;
    }

    stepper->seek(value);
}

static CliCommand cli_cmd_motor = { "motor", cli_nowt, "", 0, };

    /*
     *
     */

static void (*timer_cb)(void*) = 0;
static void *timer_arg = 0;

static void on_timer(Timer *timer, void *arg)
{
    IGNORE(arg);
    for (StepperItem *item = steppers.head; item; item = item->next)
    {
        ASSERT(item->stepper);
        item->stepper->poll();
    }
    if (timer_cb) timer_cb(timer_arg);
}

void run_timers(void (*cb)(void *), void *arg)
{
    PO_DEBUG("");
    timer_arg = arg;
    timer_cb = cb;

    if (!steppers.head)
    {
        PO_INFO("No Stepper. No Timer tests!");
        return;
    }

    static Timer *timer = 0;

    if (timer)
    {
        PO_DEBUG("Timer already running");
    }

    timer = Timer::create();
    timer->set_period(5000); // in us
    timer->set_handler(on_timer, 0);
    timer->start(true);
}

    /*
     *
     */

void add_stepper(const char *name)
{
    Stepper *stepper = (Stepper*) Objects::objects->get(name);
    ASSERT(stepper);

    StepperItem *si = new StepperItem;
    si->stepper = stepper;
    si->next = 0;
    steppers.push(si, 0);

    if (!cli_cmd_motor.subcommand)
    {
        add_cli_command( & cli_cmd_motor);
    }

    CliCommand *cmd = new CliCommand;
    memset(cmd, 0, sizeof(*cmd));
    cmd->cmd = name;
    cmd->handler = cmd_motor;
    cmd->help = "zero|<value>|get";
    cmd->ctx = (void*) name;
    cmd->next = cli_cmd_motor.subcommand;
    cli_cmd_motor.subcommand = cmd;
}

    /*
     *
     */

bool stepper_init(Device *dev, void *arg)
{
    ASSERT(arg);
    struct STEPPER_DEF *def = (struct STEPPER_DEF *) arg;
    ASSERT(def->pins);

    Stepper *stepper = make_stepper(def->pins, def->cycle);

    Objects::objects->add(dev->name, stepper);
    add_stepper(dev->name);

    return stepper;
}

//  FIN
