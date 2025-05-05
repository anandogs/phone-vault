#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "<Enter your WiFi SSID>"; // Your network SSID (name)
const char* passkey = "<Enter your WiFi password>"; // Your network password

const char* mqtt_server = "192.168.68.123"; // MQTT server domain or IP
const char* topic = "switch/get";

const char* username = "username"; // Username for MQTT broker
const char* password = "password"; // Password for MQTT broker

unsigned long valveTurnedOnAt = 0;
bool valveState = false; // false means Valve is off, true means on


WiFiClient espClient;
PubSubClient client(espClient);

const char* checkin_topic = "nodemcu/checkin";


void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, passkey);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    randomSeed(micros());

    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    if (client.connected()) {
        client.publish(checkin_topic, "online", true);
    }
}

void callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");
    for (int i = 0; i < length; i++) {
        Serial.print((char)payload[i]);
    }
    Serial.println();

    if ((char)payload[0] == '0') {
        digitalWrite(D2, LOW);
        Serial.println("No need to water! Going to sleep for 5 mins now...");
        long long sleepTimeInMicroseconds = 30 * 60 * 1000000LL; 
        ESP.deepSleep(sleepTimeInMicroseconds);
    }

    if ((char)payload[0] == '1') {
        digitalWrite(D2, HIGH);
        valveState = true;
        valveTurnedOnAt = millis();
    }
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        String clientId = "lemonNode";
        if (client.connect(clientId.c_str(), username, password)) {
            Serial.println("connected");
            client.subscribe(topic);
            client.publish(checkin_topic, "online", true);  

        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}

void setup() {
    pinMode(D2, OUTPUT);
    Serial.begin(115200);
    setup_wifi();
    client.setServer(mqtt_server, 1887);
    client.setCallback(callback);
    reconnect();

}

void loop() {
    
    if (valveState && millis() - valveTurnedOnAt >= 600000) {
      digitalWrite(D2, LOW); 
      valveState = false;
      client.publish("switch/set", "0", true);
    }
    
    if (!client.connected()) {
        reconnect();
    }
    
    client.loop();
}
