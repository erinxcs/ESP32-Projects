# Hardware and wiring

## Main board and display

The controller is the Seeed Studio XIAO ESP32C3, not the XIAO ESP32S3. These boards have different GPIO labels under the same D4/D5 silkscreen names. The working ESP32-C3 mapping is:

| Signal | GPIO / board label |
| --- | --- |
| I2C SDA | GPIO6 / D4 |
| I2C SCL | GPIO7 / D5 |
| Button | GPIO3 / D1 |

OLED wiring: 3V3 to VCC, GND to GND, GPIO6 to SDA, GPIO7 to SCL. The I2C scanner probes `0x3C` and `0x3D`; seeing no devices indicates a wiring, supply, soldering, or pin mapping issue rather than an animation problem.

For the button, connect a normally-open contact pair between GPIO3 and GND. The firmware enables the internal pull-up; add a 10 kΩ external pull-up from GPIO3 to 3V3 if wake reliability requires it. A four-legged tactile button typically has two internally connected legs on each side—verify continuity before soldering.

## OLED color regions

The 0.96-inch panel is a **monochrome** SSD1306 variant with a yellow upper region and blue lower region. Pixels cannot be assigned independent colors. Most such panels allocate the top 16 rows to yellow and the following 48 rows to blue. The converter supports either a reserved header or full-screen bitmap, and the panel determines the color by physical row position.

## Power and enclosure

The XIAO's battery pads and built-in charging circuitry require the cell polarity and permitted charging current to match the hardware specification. LiPo protection is a separate requirement. Do not assume that a salvaged 300 mAh cell is compatible solely because its nominal voltage is 3.7 V. Verify the cell specifications and protection, or use a known suitable protected LiPo.

USB-C access is on the right side of the case; the tactile button exits through the bottom panel. Keep conductor clearances and strain relief around the battery leads.
