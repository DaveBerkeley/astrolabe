#!/usr/bin/env python3

import os

def make_link(src, dst, path):
    s = src + path
    d = dst + path
    d_dir = os.path.dirname(d)
    s_dir = os.path.dirname(s)
    _, name = os.path.split(path)

    d_path = os.path.join(dst, path)
    r, _ = os.path.split(d_path)
    rel = '../' * len(r.split('/'))
    s_path = os.path.join(rel, s_dir, name)

    #raise Exception((s_dir, name, s_path, path, d, rel))

    if not os.path.exists(d_dir):
        print('create dir', d_dir)
        os.makedirs(d_dir)

    if not os.path.lexists(d):
        print('create link', d)
        os.symlink(s_path, d)

#
#

files = [
    'time.cpp',
    'object.cpp',
    'list.cpp',
    'io.cpp',
    'logger.cpp',
    'device.cpp',
    'thread.cpp',
    'json.cpp',
    'event_queue.cpp',
    'verbose.cpp',
    'socket.cpp',
    'cli_net.cpp',
    'tx_net.cpp',
    'watchdog.cpp',
    'batch.cpp',
    'network.cpp',

    'panglos/deque.h',
    'panglos/buffer.h',
    'panglos/event.h',
    'panglos/debug.h',
    'panglos/timer.h',
    'panglos/mutex.h',
    'panglos/semaphore.h',
    'panglos/time.h',
    'panglos/object.h',
    'panglos/list.h',
    'panglos/io.h',
    'panglos/logger.h',
    'panglos/thread.h',
    'panglos/queue.h',
    'panglos/device.h',
    'panglos/mqtt.h',
    'panglos/storage.h',
    'panglos/json.h',
    'panglos/event_queue.h',
    'panglos/verbose.h',
    'panglos/socket.h',
    'panglos/cli_net.h',
    'panglos/tx_net.h',
    'panglos/watchdog.h',
    'panglos/batch.h',
    'panglos/network.h',
    'panglos/ring_buffer.h',

    'drivers/i2c_bitbang.cpp',
    'drivers/mcp23s17.cpp',
    'drivers/keyboard.cpp',
    'drivers/motor.cpp',
    'drivers/pwm.cpp',
    'drivers/7-segment.cpp',
    'drivers/aht25.cpp',
    'drivers/pzem004t.cpp',
    'drivers/nmea.cpp',
    'drivers/spi_bitbang.cpp',
    'drivers/ds3231.cpp',
    'drivers/oled_GC9A01A.cpp',
    'drivers/mcp6s91.cpp',
    'drivers/spi.cpp',
    'drivers/mhz19b.cpp',
    'drivers/2_wire_bitbang.cpp',
    'drivers/tm1637.cpp',
    'drivers/bmp280.cpp',
    'drivers/mcp3002.cpp',
    'drivers/amg88xx.cpp',
    'drivers/led_strip.cpp',
    'drivers/max7219.cpp',

    'panglos/drivers/gpio.h',
    'panglos/drivers/mcp23s17.h',
    'panglos/drivers/spi.h',
    'panglos/drivers/i2c.h',
    'panglos/drivers/i2c_bitbang.h',
    'panglos/dispatch.h',
    'panglos/drivers/uart.h',
    'panglos/drivers/keyboard.h',
    'panglos/drivers/timer.h',
    'panglos/drivers/motor.h',
    'panglos/drivers/pwm.h',
    'panglos/drivers/7-segment.h',
    'panglos/drivers/aht25.h',
    'panglos/drivers/pzem004t.h',
    'panglos/drivers/nmea.h',
    'panglos/drivers/spi_bitbang.h',
    'panglos/drivers/rtc.h',
    'panglos/drivers/ds3231.h',
    'panglos/drivers/oled.h',
    'panglos/drivers/mcp6s91.h',
    'panglos/drivers/mcp3002.h',
    'panglos/drivers/mhz19b.h',
    'panglos/drivers/2_wire_bitbang.h',
    'panglos/drivers/tm1637.h',
    'panglos/drivers/bmp280.h',
    'panglos/drivers/adc.h',
    'panglos/drivers/amg88xx.h',
    'panglos/drivers/led_strip.h',
    'panglos/drivers/max7219.h',

    'panglos/hal.h',
    'panglos/esp32/hal.h',
    'panglos/esp32/adc.h',
    'panglos/esp32/timer.h',
    'panglos/stm32/hal.h',

    'panglos/arch.h',
    'panglos/riscv32/arch.h',
    'panglos/xtensa/arch.h',
    'panglos/stm32/arch.h',
    'riscv32/arch.cpp',
    'xtensa/arch.cpp',
    'stm32/arch.cpp',

    'esp32/hal.cpp',
    'esp32/gpio.cpp',
    'esp32/i2c.cpp',
    'esp32/timer.cpp',
    'esp32/mqtt.cpp',
    'esp32/pwm.cpp',
    'esp32/storage.cpp',
    'esp32/spi.cpp',
    'esp32/uart.cpp',
    'esp32/adc.cpp',
    'esp32/rmt_strip.cpp',
    'esp32/network.cpp',

    'panglos/esp32/gpio.h',
    'panglos/esp32/i2c.h',
    'panglos/esp32/spi.h',
    'panglos/esp32/uart.h',
    'panglos/esp32/hal.h',
    'panglos/esp32/rmt_strip.h',
 
    'freertos/yield.h',
    'freertos/time.cpp',
    'freertos/mutex.cpp',
    'freertos/semaphore.cpp',
    'freertos/thread.cpp',
    'freertos/queue.cpp',
    'panglos/freertos/queue.h',

]

for path in files:
    make_link('panglos/src/', 'lib/panglos/src/', path)

#
#   Put the google test simulation in its own lib

#files = [
#    'gtest/gtest.h',
#    'gtest.cpp',
#]
#
#for path in files:
#    make_link('../panglos/', 'lib/gtest/src/', path)

print("built library links ...")


# FIN
