
PROJECT=ASTRO_CLOCK
#PROJECT=NOTHING

TARGET=esp32-s2-mini
#TARGET=esp32-dev

MODE = run
#MODE = debug

.PHONY: all flash

NAME=$(shell git config user.name)
COPYRIGHT='" (C) ${NAME} "'
BANNER=src/banner.cpp

all: 
	echo "//    ${PROJECT} banner. Auto generated, do not edit" > ${BANNER}
	echo "const char *banner = {" >> ${BANNER}
	echo ${PROJECT} | sed 's/_/ /g' | figlet | sed 's/\\/\\\\/g' | awk '//{printf "    \"%s\\r\\n\"\n", $$0}' >> ${BANNER}
	echo '"\\r\\n"' >> ${BANNER}
	date +"\"built %Y/%m/%d %H:%M:%S git=$$(git rev-parse --short HEAD) \"" >> ${BANNER}
	echo "\"esp-idf=\" IDF_VER" >> ${BANNER}
	echo ${COPYRIGHT} >> ${BANNER}
	date +"\"%Y\r\n\"" >> ${BANNER}
	echo "};" >> ${BANNER}
	PLATFORMIO_BUILD_FLAGS="-DPROJECT=${PROJECT} -D${PROJECT}" pio $(MODE) -e $(TARGET) 

flash:
	PLATFORMIO_BUILD_FLAGS="-DPROJECT=${PROJECT} -D${PROJECT}" pio $(MODE) -e $(TARGET) --target upload --verbose

debug:
	PLATFORMIO_BUILD_FLAGS="-DPROJECT=${PROJECT} -D${PROJECT}" pio debug -e $(TARGET)

ctags:
	ctags -R . \
		/home/dave/.platformio/packages/framework-espidf/components/freertos/ \
		/home/dave/.platformio/packages/framework-espidf/components/hal/include \
		/home/dave/.platformio/packages/framework-espidf/components/driver \
		/home/dave/.platformio/packages/framework-espidf/components/esp_common \
		/home/dave/.platformio/packages/framework-espidf/components/esp_wifi \
		/home/dave/.platformio/packages/framework-espidf/components/mqtt

clean:
	rm -rf .pio managed_components
	scons -c 
	find . -name "*~" | xargs rm -f

cleanx:
	find .pio -name "*.o" | grep panglos | xargs rm

dump:
	#~/.platformio/packages/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-objdump .pio/build/$(TARGET)/firmware.elf -d -S
	~/.platformio/packages/toolchain-xtensa-esp32s2/bin/xtensa-esp32s2-elf-objdump .pio/build/$(TARGET)/firmware.elf -d -S
	#~/.platformio/packages/toolchain-riscv32-esp/bin/riscv32-esp-elf-objdump .pio/build/$(TARGET)/firmware.elf -d -S

tdd:
	scons

test: tdd
	./tdd

clang: export CC=clang
clang: export CXX=clang++
clang: $(APP)
	scons

gdb:
	/opt/espressif/bin/openocd -f board/esp32c3-builtin.cfg

#	FIN
