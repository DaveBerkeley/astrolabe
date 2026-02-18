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
    'date.cpp',

    'app/cli.cpp',
    'app/cli_cmd.cpp',
    'app/cli_server.cpp',
    'app/event.cpp',
    'app/devices.cpp',
    'panglos/app/cli.h',
    'panglos/app/cli_cmd.h',
    'panglos/app/cli_server.h',
    'panglos/app/event.h',
    'panglos/app/devices.h',

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
    'panglos/date.h',

    'drivers/motor.cpp',
    'drivers/pwm.cpp',

    'panglos/drivers/gpio.h',
    'panglos/dispatch.h',
    'panglos/drivers/uart.h',
    'panglos/drivers/timer.h',
    'panglos/drivers/motor.h',
    'panglos/drivers/pwm.h',
    'panglos/drivers/7-segment.h',
    'panglos/drivers/rtc.h',
    'panglos/drivers/ds3231.h',

    'panglos/hal.h',
    'panglos/esp32/hal.h',
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
    'esp32/timer.cpp',
    'esp32/mqtt.cpp',
    'esp32/pwm.cpp',
    'esp32/storage.cpp',
    'esp32/uart.cpp',
    'esp32/network.cpp',

    'panglos/esp32/gpio.h',
    'panglos/esp32/uart.h',
    'panglos/esp32/hal.h',
 
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
