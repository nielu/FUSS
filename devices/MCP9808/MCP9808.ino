/*		
	MCP9808

	Basic sketch for ESP8266 with MCP9808 sensor connected
	Device will push data to server using MQTT protocol
*/

#include <Adafruit_MCP9808.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Update these with values suitable for your network.

const char* ssid = "SSID";
const char* password = "PASSWORD";
const char* mqtt_server = "mqtt_broker_ip";
const char* clientID = "mcp9808";
char* tempTopic;
char* inTopic;

//those have to be global because of wierd stack behaviour on EPS8266
String tempTopicStr = "sensor/mcp9808/[MAC]/temperature";
String inTopicStr = "master/[MAC]";
String macString = "FFFFFFFFFFFF";


Adafruit_MCP9808 mcp;

float temp_c;  // Values read from sensor


WiFiClient espClient;
PubSubClient client(espClient);
char msg[50];
uint8_t mac_array[6];
char mac_str[12];


void setup_topics()
{
	WiFi.macAddress(mac_array);
	for (int i = 0; i < sizeof(mac_array); ++i)
		sprintf(mac_str, "%s%02x", mac_str, mac_array[i]);
	macString = mac_str;

	Serial.print("MAC:");
	Serial.println(macString);

	tempTopicStr.replace("[MAC]", macString);
	inTopicStr.replace("[MAC]", macString);

	tempTopic = new char[tempTopicStr.length() + 1]; //make space for '\0'
	inTopic = new char[inTopicStr.length() + 1];

	tempTopicStr.toCharArray(tempTopic, tempTopicStr.length() + 1);
	inTopicStr.toCharArray(inTopic, inTopicStr.length() + 1);

	Serial.println("Publishing on topics:");
	Serial.print("\t1. ");
	Serial.println(tempTopic);

	Serial.println();
	Serial.print("Listening on: ");
	Serial.println(inTopic);

}

void setup_wifi()
{
	delay(10);

	setup_topics();

	Serial.println();
	Serial.print("Connecting to ");
	Serial.print(ssid);

	WiFi.begin(ssid, password);

	while (WiFi.status() != WL_CONNECTED)
	{
		delay(500);
		Serial.print(".");
	}

	Serial.println("");
	Serial.println("WiFi connected");
	Serial.println("IP address: ");
	Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length)
{
	// Conver the incoming byte array to a string
	payload[length] = '\0'; // Null terminator used to terminate the char array
	String message = (char*)payload;

	Serial.print("Message arrived on topic: [");
	Serial.print(topic);
	Serial.print("], ");
	Serial.println(message);

	if (message == "temperature")
	{
		gettemperature();
		Serial.print("Sending temperature:");
		Serial.println(temp_c);
		dtostrf(temp_c, 2, 2, msg);
		client.publish(tempTopic, msg);
	}
	else
	{
		Serial.print("Got message on unknown topic:");
		Serial.println(topic);
	}

}

void reconnect()
{
	// Loop until we're reconnected
	while (!client.connected())
	{
		Serial.print("Attempting MQTT connection...");
		// Attempt to connect
		if (client.connect(clientID))
		{
			Serial.println("connected");
			// Once connected, publish an announcement...
			//client.publish(outTopic, clientID);
			// ... and resubscribe
			client.subscribe(inTopic);
		}
		else
		{
			Serial.print("failed, rc=");
			Serial.print(client.state());
			Serial.println(" try again in 5 seconds");
			delay(5000);
		}
	}
}

void setup() {
	Serial.begin(115200);
	setup_wifi();
	client.setServer(mqtt_server, 1883);
	client.setCallback(callback);

	mcp.begin();

}

void loop() {

	if (!client.connected())
	{
		reconnect();
	}
	gettemperature();

	Serial.print("Sending temperature:");
	Serial.println(temp_c);
	dtostrf(temp_c, 2, 2, msg);
	client.publish(tempTopic, msg);

	client.loop();
	delay(1000 * 60 * 5);
}

void gettemperature()
{
	temp_c = mcp.readTempC();
	// Check if any reads failed and exit early (to try again).
	if (isnan(temp_c))
		Serial.println("Failed to read from MCP sensor!");
}