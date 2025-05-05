
#include <string.h>

#include "esp_sntp.h"
#include "esp_idf_version.h"

#include "panglos/debug.h"
#include "panglos/storage.h"
#include "panglos/mutex.h"
#include "panglos/event_queue.h"
#include "panglos/object.h"

#include "cli/src/cli.h"

#include "panglos/app/cli.h"
#include "panglos/app/cli_cmd.h"
#include "panglos/app/event.h"
#include "ntp.h"

using namespace panglos;

    /*
     *
     */

extern "C" void sntp_sync_time(struct timeval *tv)
{
    PO_DEBUG("");
    settimeofday(tv, NULL);
    sntp_set_sync_status(SNTP_SYNC_STATUS_COMPLETED);
}

class NtpTick : public EvQueue::Event
{
    ::Event::Queue *queue;
    Time::tick_t period;

    virtual void run(EvQueue *eq) override
    {
        if (when == 0)
        {
            when = Time::get();
        }

        when += period;
        eq->add(this);

        struct timeval tv;
        if (gettimeofday(& tv, 0) != 0)
        {
            PO_ERROR("gettimeofday() error");
            return;
        }

        struct tm tm;
        gmtime_r(& tv.tv_sec, & tm);

        // send DATE_TIME Event
        ::Event event;
        event.type = ::Event::DATE_TIME;
        event.payload.dt.yy = 1900 + tm.tm_year;
        event.payload.dt.mm = tm.tm_mon + 1;
        event.payload.dt.dd = tm.tm_mday;
        event.payload.dt.h = tm.tm_hour;
        event.payload.dt.m = tm.tm_min;
        event.payload.dt.s = tm.tm_sec;
        event.payload.dt.source = ::Event::payload::dt::NET;
        event.put(queue);
    }
public:
    NtpTick(::Event::Queue *q, Time::tick_t _period=1000)
    :   queue(q),
        period(_period)
    {
        ASSERT(queue);
    }
};

    /*
     *
     */

static bool on_init(void *arg, Event *, Event::Queue *q)
{
    PO_DEBUG("");
    ASSERT(arg);
    Time::tick_t period  = *(Time::tick_t *) arg;

    Storage db("ntp");

    char server[40];
    size_t s = sizeof(server);
    if (!db.get("server", server, & s))
    {
        strncpy(server, "pool.ntp.org", sizeof(server));
    }

    PO_DEBUG("Starting SNTP %s", server);
    const uint32_t period_ms = 1000 * 60 * 60 * 10;
    sntp_set_sync_interval(period_ms);

#if (ESP_IDF_VERSION_MAJOR == 5) && (ESP_IDF_VERSION_MINOR > 0)
#pragma message("" ## ESP_IDF_VERSION_MINOR)
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, strdup(server));
    esp_sntp_init();
#else
    // Old API
    sntp_setoperatingmode(SNTP_OPMODE_POLL);
    sntp_setservername(0, strdup(server));
    sntp_init();
#endif

    EvQueue *eq = (EvQueue*) Objects::objects->get("event_queue");
    ASSERT(eq);
    NtpTick *event = new NtpTick(q, period);
    eq->add(event);

    return false; // INIT handlers must return false so multiple handlers can be run
}

    /*
     *
     */

static void cli_ntp(CLI *cli, CliCommand *)
{
    struct timeval tv;
    gettimeofday(& tv, NULL);
    struct tm tm;
    gmtime_r(& tv.tv_sec, & tm);

    cli_print(cli, "%04d/%02d/%02d %02d:%02d:%02d%s",
            tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
            tm.tm_hour, tm.tm_min, tm.tm_sec,
            cli->eol);
}

static CliCommand ntp_cmd = { "ntp", cli_ntp, "show current time",  };

    /*
     *
     */

void ntp_start(Time::tick_t period)
{
    PO_DEBUG("");
    static Time::tick_t p = period;
    EventHandler::add_handler(Event::INIT, on_init, & p);
    add_cli_command(& ntp_cmd);
}

//  FIN
