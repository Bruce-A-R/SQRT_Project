**Test Data for Triggering**

The triggering algorithm needs to be bench tested since it cannot be safely flight tested. Simulated text files for pressure sensor and GPS readings will be made to test the sensor with.

Cases of sensor data to make:

1. pressure sensor works and pressure is low enough
2. altitude is high, pressure values wierd (this will need to be tested in multiple cases (sensor has no readings, sensor readings are inconsistent)
3. pressure is higher than threshold, altitude is lower or higher and pressure sensor is good, and we are falling

   -BR 27/2
