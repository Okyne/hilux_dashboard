"""
Source de données MQTT pour l'UI — remplace DummyDataSource.

Même contrat que DummyDataSource : expose un dict `values` (mêmes clés) que
l'UI lit à chaque tick. Ici, les valeurs sont poussées par les callbacks MQTT ;
`update()` est donc un no-op (les données arrivent de manière asynchrone).

Robustesse : reconnexion automatique gérée par paho ; si une valeur est NaN
ou absente, on garde la dernière connue.
"""
import paho.mqtt.client as mqtt
import telemetry


class MqttDataSource:
    def __init__(self, host=None, port=None):
        self.values = {k: 0.0 for k in telemetry.KEYS}
        self.connected = False
        self._client = mqtt.Client(client_id="hilux-ui")
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.reconnect_delay_set(min_delay=1, max_delay=10)
        self._client.connect_async(host or telemetry.BROKER_HOST,
                                   port or telemetry.BROKER_PORT, keepalive=30)
        self._client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = (rc == 0)
        client.subscribe(f"{telemetry.PREFIX}/#")
        print(f"[ui-mqtt] connecté (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("[ui-mqtt] déconnecté, tentative de reconnexion...")

    def _on_message(self, client, userdata, msg):
        key = telemetry.key_from_topic(msg.topic)
        if key not in self.values:
            return
        try:
            val = float(msg.payload.decode())
        except ValueError:
            return
        if val == val:                    # ignore NaN -> garde l'ancienne valeur
            self.values[key] = val

    def update(self, *_):
        pass                              # données poussées en asynchrone

    def close(self):
        self._client.loop_stop()
        self._client.disconnect()
