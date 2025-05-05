
    /*
     *
     */

#define DEV_GPIO(name, needs, def) Device(name, needs, gpio_init, (void*) def)

extern panglos::Device *board_devs;

void board_init();

    /*
     *
     */

#if defined(ESP32_S2_MINI)
#define BOARD_NAME "ESP32_S2_MINI"
#endif

#if defined(ASTRO_CLOCK)
#define WIFI 1
#endif

#if defined(NOTHING)
#define WIFI 1
#endif

//  FIN
