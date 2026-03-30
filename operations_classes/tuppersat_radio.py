"""tuppersat.radio._tuppersat_radio.py
University College, Dublin

Provides class TupperSatRadio to handle transmitting TDRSS formatted data and
telemetry packets.

"""

# tuppersat imports
#from tuppersat.packets import TelemetryPacket, DataPacket
#from tuppersat.toolkit.misc import Counter

# local imports
from _utils import Counter
from _rhserial_radio import RHSerialRadio
from _packet_utils import TelemetryPacket, DataPacket

def format_callsign(callsign):
    #TODO: validate ascii characters?
    #TODO: validate length limit?
#    return callsign.ljust(8)[:8]
    callsign = callsign[:8]
    return f"{callsign:<8}"


class TupperSatRadio(RHSerialRadio):
    """API to send TDRSS telemetry & data messages with the T3."""
    
    def __init__(self, uart, address, callsign, user_callback=None):
        """Initialiser."""
        self.callsign = format_callsign(callsign)
        self.telemetry_count = Counter()
        
#        super().__init__(uart, address, user_callback)
        super().__init__(uart, address)

    def send_packet(self, packet):
        """Convert pkt to bytes and transmit."""
        #TODO: check pkt is a valid packet type?
        #TODO: catch exceptions when converting to bytes?
        # convert to bytes
        _pkt_bytes = bytes(packet)
        
        # transmit
        return self.send_bytes(_pkt_bytes)
        
    def send_telemetry(self, hhmmss=None, latitude=None, longitude=None, altitude=None, hdop=None,
                       t_internal=None, t_external=None, pressure=None):
        """Assemble and transmit a TupperSat telemetry packet, safely handling None values."""

        # Provide defaults for None values
        if hhmmss is None:
            import time
            class PacketTime:
                def __init__(self):
                    t = time.localtime()
                    self.hour = t[3]
                    self.minute = t[4]
                    self.second = t[5]
            hhmmss = PacketTime()
        print(latitude, longitude, hdop)
        latitude   = 0.0 if latitude is ' None' else float(latitude)
        longitude  = 0.0 if longitude is ' None' else float(longitude)
        altitude   = 0.0 if altitude is ' None' else float(altitude)
        hdop       = 0.0 if hdop is ' None' else float(hdop)
        t_internal = 0.0 if t_internal is None else float(t_internal)
        t_external = 0.0 if t_external is None else float(t_external)
        pressure   = 0.0 if pressure is None else float(pressure)

        # assemble and transmit
        _packet = TelemetryPacket(
            callsign   = self.callsign, 
            index      = self.telemetry_count(),
            hhmmss     = hhmmss,
            latitude   = latitude,
            longitude  = longitude,
            altitude   = altitude,
            hdop       = hdop,
            t_internal = t_internal,
            t_external = t_external,
            pressure   = pressure
        )

        return self.send_packet(_packet)

    def send_data(self, data=None, trig_status=None, trig_type=None, pressure = None, altitude=None):
        """Assemble and transmit a TupperSat data packet, handling None values safely"""

        #Assemble packet
        _packet = DataPacket(
            callsign    = self.callsign,
            data        = data,
            trig_status = trig_status,
            trig_type   = trig_type,
            pressure = pressure,
            altitude = altitude,
        )

        # Transmit
        return self.send_packet(_packet)

