
# priority

ssh-copy-id ikeshel@x86l-157

done-add threading

done-if node dead, disable menu otherwise enable menu


--- Register Dump ---:
###### SFP 0 DEV:0 :)
Channel enabled register 	0xffffffff
Channel trigger enabled register NOT READ, no TAMEX-PADI1 board!
Channel polarity register 	0xffffffff
Trigger window register 	0x80640064
Clock source register  	0x20
Tamex control register 	0x307c20c0
______________________________
   DAC threshold settings:    
Channel 	| PADI-0 	| PADI-1 
--------	+------  	+--------
  0    	| 0x3ff    	| 0x0 
  1    	| 0x3ff    	| 0x0 
  2    	| 0x3ff    	| 0x0 
  3    	| 0x3ff    	| 0x0 
  4    	| 0x3ff    	| 0x0 
  5    	| 0x3ff    	| 0x0 
  6    	| 0x3ff    	| 0x0 
  7    	| 0x3ff    	| 0x0 
Version	| 0x3ff    	| 0x0


[0] ikeshel@X86L-132: ~ > rgoc -h                                                                                                                                                    Thu 09.Apr.2026 15:16:48
***************************************************************************
 rgoc (remote gosipcmd) for dabc and mbspex library  
 v0.7 19-Jan-2023 by JAM (j.adamczewski@gsi.de)
***************************************************************************
  usage: rgoc [-h|-z] [[-i|-r|-w|-s|-u] [-b] | [-c|-v FILE] [-n DEVICE |-d|-x] node[:port] sfp slave [address [value [words]|[words]]]] 
         Options:
                 -h        : display this help
                 -z        : reset (zero) pexor/kinpex board 
                 -i        : initialize sfp chain 
                 -r        : read from register 
                 -w        : write to  register
                 -s        : set bits of given mask in  register
                 -u        : unset bits of given mask in  register
                 -b        : broadcast io operations to all slaves in range (0-sfp)(0-slave)
                 -c FILE   : configure registers with values from FILE.gos
                 -v FILE   : verify register contents (compare with FILE.gos)
                 -n DEVICE : specify device number N (/dev/pexorN, default:0) 
                 -d        : debug mode (verbose output) 
                 -x        : numbers in hex format (defaults: decimal, or defined by prefix 0x) 
         Arguments:
                 node:port - nodename of remote gosip command server (default port 12345)
                 sfp       - sfp chain- -1 to broadcast all registered chains 
                 slave     - slave id at chain, or total number of slaves. -1 for internal broadcast
                 address   - register on slave 
                 value     - value to write on slave 
                 words     - number of words to read/write/set incrementally
         Examples:
          rgoc -z -n 1 x86l-59                   : master gosip reset of board /dev/pexor1 at node x86l-59
          rgoc -i x86l-59 0 24                   : initialize chain at sfp 0 with 24 slave devices
          rgoc -r -x x86l-59 1 0 0x1000          : read from sfp 1, slave 0, address 0x1000 and printout value
          rgoc -r -x x86l-59 0 3 0x1000 5        : read from sfp 0, slave 3, address 0x1000 next 5 words
          rgoc -r -b  x86l-113 1 3 0x1000 10      : broadcast read from sfp (0..1), slave (0..3), address 0x1000 next 10 words
          rgoc -r --  x86l-42 -1 -1 0x1000 10     : broadcast read from address 0x1000, next 10 words from all registered slaves
          rgoc -w -x  x86l-113 0 3 0x1000 0x2A     : write value 0x2A to sfp 0, slave 3, address 0x1000
          rgoc -w -x  x86l-113 1 0 20000 AB FF     : write value 0xAB to sfp 1, slave 0, to addresses 0x20000-0x200FF
          rgoc -w -b  localhost 1  3 0x20004c 1    : broadcast write value 1 to address 0x20004c on sfp (0..1) slaves (0..3)
          rgoc -w --  x86l-113 -1 -1 0x20004c 1    : write value 1 to address 0x20004c on all registered slaves (internal driver broadcast)
          rgoc -s     x86l-113 0 0 0x200000 0x4      : set bit 100 on sfp0, slave 0, address 0x200000
          rgoc -u     x86l-113 0 0 0x200000 0x4 0xFF : unset bit 100 on sfp0, slave 0, address 0x200000-0x2000FF
          rgoc x86l-113  -x -c run42.gos           : write configuration values from file run42.gos to slaves 
*****************************************************************************
