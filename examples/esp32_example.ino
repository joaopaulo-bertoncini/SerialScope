/*
 * ESP32 Example Code for SerialScope
 * 
 * This example demonstrates how to output structured logs
 * that can be parsed by SerialScope.
 */

#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("[INFO] Boot complete");
  Serial.println("[INFO] ESP32 initialized");
}

void loop() {
  // Example 1: Plain text logs
  Serial.println("[INFO] System running");
  Serial.println("[WARN] Low battery warning");
  
  // Example 2: JSON metrics
  float temperature = 42.3;
  float voltage = 3.28;
  int rssi = -62;
  
  Serial.print("{\"type\":\"metric\",\"temp\":");
  Serial.print(temperature);
  Serial.print(",\"voltage\":");
  Serial.print(voltage);
  Serial.print(",\"rssi\":");
  Serial.print(rssi);
  Serial.println("}");
  
  // Example 3: Error logs
  if (random(100) < 5) {
    Serial.println("[ERROR] Random error occurred");
  }
  
  delay(1000);
}
