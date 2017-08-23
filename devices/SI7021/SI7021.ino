/*
	SI7021

	Basic sketch for ESP8266 with SI7021 sensor connected
	Device will push JSON formatted data to server using MQTT protocol
*/

#define MQTT_KEEPALIVE 10

#define DEBUG

#ifdef  DEBUG
#define DEBUG_PRINTLN(x) Serial.println(x)
#define DEBUG_PRINT(x) Serial.print(x)
#define DEBUG_JSON root.prettyPrintTo(Serial);
#else
#define DEBUG_PRINTLN(x)
#define DEBUG_PRINT(x)
#define DEBUG_JSON ;
#endif //  DEBUG


#include <ArduinoJson.h>
#include <Adafruit_Si7021.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

ADC_MODE(ADC_VCC);

// Update these with values suitable for your network.

const char* ssid = "wifi_name";
const char* password = "wifi_password";
const char* mqtt_server = "mqtt_server";
const char* clientID = "defalut_device_name";

const char* jsonMqttTopic = "sensor/JSON";

char* tempTopic;
char* humTopic;
char* telTopic;
char* inTopic;



Adafruit_Si7021 si;

float humidity, temp_c, vcc;  // Values read from sensor
uint32_t free_heap;


WiFiClient espClient;
PubSubClient client(espClient);
StaticJsonBuffer<256> jsonBuffer;
char msg[1024];
uint8_t mac_array[6];
char mac_str[12];

void setup_wifi() 
{
	WiFi.macAddress(mac_array);
	for (int i = 0; i < sizeof(mac_array); ++i)
		sprintf(mac_str, "%s%02x", mac_str, mac_array[i]);

	DEBUG_PRINT("MAC:");
	DEBUG_PRINTLN(mac_str);

	DEBUG_PRINTLN();
	DEBUG_PRINT("Connecting to ");
	DEBUG_PRINT(ssid);

	WiFi.begin(ssid, password);

	while (WiFi.status() != WL_CONNECTED)
	{
		delay(500);
		DEBUG_PRINT(".");
	}

	DEBUG_PRINTLN("");
	DEBUG_PRINTLN("WiFi connected");
	DEBUG_PRINTLN("IP address: ");
	DEBUG_PRINTLN(WiFi.localIP());
}

void setup_mqtt()
{
	DEBUG_PRINT("Publishing on topic: ");
	DEBUG_PRINTLN(jsonMqttTopic);

	client.setServer(mqtt_server, 1883);
	if (!client.connected())
		reconnect();
}

void reconnect()
{
	// Loop until we're reconnected
	while (!client.connected())
	{
		DEBUG_PRINT("Attempting MQTT connection...");
		// Attempt to connect
		if (client.connect(clientID))
		{
			DEBUG_PRINTLN("connected");
		}
		else
		{
			DEBUG_PRINT("failed, rc=");
			DEBUG_PRINT(client.state());
			DEBUG_PRINTLN(" try again in 1 seconds");
			delay(1000);
		}
	}
}

void setup()
{
	Serial.begin(115200);
	DEBUG_PRINTLN("SI7021 ESP8266 temperature/humidity sensor");

	setup_wifi();
	setup_mqtt();

	si.begin();

	getReadings();
	createMessage();

	DEBUG_PRINTLN("Entering deep sleep");
	ESP.deepSleep(1000 * 1000 * 60 * 5);

}

void loop()
{
}

void getReadings()
{
	humidity = si.readHumidity();
	temp_c = si.readTemperature();
	vcc = ESP.getVcc();
	free_heap = ESP.getFreeHeap();

	if (isnan(humidity) || isnan(temp_c))
		DEBUG_PRINTLN("Failed to read from SI sensor!");

	DEBUG_PRINT("temperature:");
	DEBUG_PRINTLN(temp_c);

	DEBUG_PRINT("humidity:");
	DEBUG_PRINTLN(humidity);

	DEBUG_PRINT("VCC: ");
	DEBUG_PRINTLN(vcc);

	DEBUG_PRINT("Free heap: ");
	DEBUG_PRINTLN(free_heap);
}

void createMessage()
{
	JsonObject& root = jsonBuffer.createObject();

	root["sensor"] = "SI7021";
	root["MAC"] = mac_str;
	root["temp"] = temp_c;
	root["hum"] = humidity;
	root["vcc"] = vcc;
	root["heap"] = free_heap;

	DEBUG_PRINTLN("Sending JSON:\n");
	DEBUG_JSON;
	root.printTo(msg);

	client.publish(jsonMqttTopic, msg);

}