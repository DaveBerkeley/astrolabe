
namespace panglos {
    class Stepper;
};

struct STEPPER_DEF {
    const char **pins;
    int cycle;
};

bool stepper_init(panglos::Device *dev, void *arg);

panglos::Stepper *make_stepper(int *pins, int cycle);
panglos::Stepper *make_stepper(const char **names, int cycle);

void add_stepper(const char *name);

void run_timers(void (*cb)(void *)=0, void *arg=0);

//  FIN
