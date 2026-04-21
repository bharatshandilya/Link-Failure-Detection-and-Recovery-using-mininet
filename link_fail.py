from pox.core import core                         #POX internal system
import pox.openflow.libopenflow_01 as of          #openflow control

log = core.getLogger()                            #used to print messages

mac_to_port = {}                                  #to store mac learning table

def _handle_ConnectionUp(event):                  #switch connected to controller
    log.info("Switch %s connected", event.dpid)   #logs switch ID (ex: switch 1 connected)

def _handle_PacketIn(event):                      #called when switch sends packet to controller
    packet = event.parsed                         #extract packet data, switch ID, incoming port
    dpid = event.dpid
    in_port = event.port

    if dpid not in mac_to_port:                   #create table for each switch
        mac_to_port[dpid] = {}

    mac_to_port[dpid][packet.src] = in_port       #learn source MAC

    if packet.dst in mac_to_port[dpid]:           #if dest known, forward directly, else flood to all ports
        out_port = mac_to_port[dpid][packet.dst]
    else:
        out_port = of.OFPP_FLOOD

    msg = of.ofp_flow_mod()                                     #create flow rules
    msg.match = of.ofp_match.from_packet(packet)                #match packet with same properties
    msg.actions.append(of.ofp_action_output(port=out_port))     #forward to selected port
    msg.idle_timeout = 10         #remove if idle for 10s
    msg.hard_timeout = 30         #always remove after 30s

    event.connection.send(msg)    #send flow rule to switch

    msg = of.ofp_packet_out()     #forward current packer
    msg.data = event.ofp          #raw packet data
    msg.actions.append(of.ofp_action_output(port=out_port))
    msg.in_port = in_port

    event.connection.send(msg)    #send packet out

def launch():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)  #switch connection events
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)          #packet arrival events