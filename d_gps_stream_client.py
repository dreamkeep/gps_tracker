""" 
gps_stream_client.py should be executed from a gps client in order to send data
to gps_stream_server.py and therefore to be tracked. This script is daemonised.
"""

__author__ = "Konstantinos Kagiampakis"
__license__ = """ 
Creative Commons Attribution 4.0 International
https://creativecommons.org/licenses/by/4.0/
https://creativecommons.org/licenses/by/4.0/legalcode
"""

import json
import socket
import gpsd
import time
import sys
from daemon import Daemon

class MyDaemon(Daemon):
        
        IP_ADDR = '192.168.1.2'
        TCP_PORT = 2345
        
        def __init__(self, IP_ADDR='192.168.1.2', TCP_PORT='2345', pidfile='/tmp/daemon-example.pid', stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
                self.stdin = stdin
                self.stdout = stdout
                self.stderr = stderr
                self.pidfile = pidfile
                self.IP_ADDR = IP_ADDR
                self.TCP_PORT = int(TCP_PORT)
                                
        def run(self):
            BUFFER_SIZE = 20
            NO_FIX = bytes("NO-FIX","utf-8")
            out = NO_FIX
            
            # Connect to the local gpsd
            while True:
               try:
                  print("Connecting on GPSD...")
                  gpsd.connect()
               except:
                  print("Could not connect to GPSD.\nThis script is persistent and will try to reconnect to GPSD in 10 sec.",sys.exc_info()[0])
                  time.sleep(10)
               else:
                  print("GPSD connected!")
                  break
            
            # Connect somewhere else
            #gpsd.connect(host="127.0.0.1", port=2947)
            
            #the outside while is used for reconnects
            while True:
              while True:
                 try:
                    print("Connecting to remote server")
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((self.IP_ADDR, self.TCP_PORT))
                 except KeyboardInterrupt:
                    print("Script terminates.")
                    try:
                       s.close()
                    except:
                       raise
                    else:    
                        print("Socket closed.")
                    exit()        
                 except:
                    print("Could not connect to remote server.\nThis script is persistent and will try to reconnect in 10 sec.",sys.exc_info()[0])
                    try:
                       s.close()
                    except:
                       raise
                    else:    
                        print("Socket closed.")
                    time.sleep(10)
                 else:
                    print("Connected to server!")
                    break
              
              while True:
                  # Get gps position
                  try:
                    packet = gpsd.get_current()
                
                    print("Mode: " + str(packet.mode))
                    print("Satellites: " + str(packet.sats))
                    if packet.mode > 1:
                       if packet.mode >= 2:
                          print("Latitude: " + str(packet.lat))
                          print("Longitude: " + str(packet.lon))
                          print("Track: " + str(packet.track))
                          print("Horizontal Speed: " + str(packet.hspeed))
                          print("Time: " + str(packet.time))
                          print("Error: " + str(packet.error))
                       if packet.mode == 3:
                          print("Altitude: " + str(packet.alt))
                          print("Climb: " + str(packet.climb))
                    
                       data = {'lat': str(packet.lat), 'lon': str(packet.lon),  'track': str(packet.track), 'hspeed': str(packet.hspeed), 'time': str(packet.time)}
                       if packet.mode == 3:
                         data['alt'] = str(packet.alt)
                         data['climb'] = str(packet.climb)
              
                       str_data = json.dumps(data)
                       out = bytes(str_data,"utf-8")
                       print("data to send:#"+str_data+"# str len:"+str(len(str_data))+" byte len:"+str(len(out)))
              
                    else:
                       print("There is no GPS FIX yet.")
                       out = NO_FIX
                       time.sleep(10)
                
                  except Exception as e:
                    if str(e) == '\'sattelites\'':
                      print("There is no GPS FIX yet.")
                      time.sleep(10)
                    else:  
                      print(e)
                      time.sleep(3)
                    out = NO_FIX  
                      
                  try:
                     print("sending data to server!")
                     s.send(out)
                     s.recv(BUFFER_SIZE)
                  except socket.error:
                     print("Socket error. Socket drops and reconnects.",sys.exc_info()[0])
                     break
                  except:
                     print('Unknown exception. Socket drops and script terminates.')
                     try:
                       s.close()
                     except:
                       raise
                     else:
                       print("Socket closed.")    
                     raise                   
                  time.sleep(3)
              
              try:
                s.close()
              except:
                raise
              else:    
                print("Socket closed.")
 
if __name__ == "__main__":        
        if len(sys.argv) == 4:                
          if int(sys.argv[2]) <= 0 or int(sys.argv[2]) >= 65536:
            print ("Nooo!!! bad tcp port given in arg 3.")
            sys.exit(2)
          
          pid_id = '/tmp/d-gps-stream-client-'+sys.argv[1].replace('.','-')+'-'+sys.argv[2]+'.pid'          
          daemon = MyDaemon(sys.argv[1],sys.argv[2],pid_id,'/dev/null','/home/pi/stdout','/home/pi/stderr')    
          
          if 'start' == sys.argv[3]:
            daemon.start()                          
          elif 'stop' == sys.argv[3]:
            daemon.stop()
          elif 'restart' == sys.argv[3]:
            daemon.restart()
          else:
            print ("Unknown command")
            sys.exit(2)
          sys.exit(0)  
        else:
          print("usage: %s ip_v4_address tcp_port start|stop|restart" % sys.argv[0])
          print("Warning the ip address and port are also being used as a pid signature in order to let the tacker subscribe to multiple servers. When stop or restart have to be called that sould be done with the same ip address and port the start call was made.")          
          sys.exit(2)                 