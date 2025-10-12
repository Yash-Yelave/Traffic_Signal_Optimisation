// traffic_globals.h

#ifndef TRAFFIC_GLOBALS_H
#define TRAFFIC_GLOBALS_H

#include "Arduino.h" // For 'volatile' and 'unsigned long'

// This file DECLARES our shared global variables.
// The actual variables are DEFINED in CameraWebServer.ino

extern volatile unsigned long greenLightEndTime;
extern volatile bool isGreenLightActive;
extern const int greenLedPin;
extern const int redLedPin;

#endif