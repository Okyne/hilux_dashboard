"""
Petit wrapper MQTT partagé par tous les lecteurs.

Chaque lecteur reçoit un Publisher et appelle publish(key, value). Les
messages sont publiés en "retained" : un client (l'UI) qui se connecte
récupère immédiatement la dernière valeur connue de chaque topic.
"""
import math
import paho.mqtt.client as mqtt

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import telemetry


class Publisher:
    def __init__(self, host=None, port=None, client_id="hilux-acq"):
        self.host = host or telemetry.BROKER_HOST
        self.port = port or telemetry.BROKER_PORT
        self.client = mqtt.Client(client_id=client_id)
        self.client.connect(self.host, self.port, keepalive=30)
        self.client.loop_start()

    def publish(self, key: str, value):
        if value is None:
            payload = "nan"
        else:
            try:
                payload = "nan" if math.isnan(value) else f"{float(value):.3f}"
            except (TypeError, ValueError):
                payload = "nan"
        self.client.publish(telemetry.topic(key), payload, qos=0, retain=True)

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
