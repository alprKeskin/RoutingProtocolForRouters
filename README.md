# RoutingProtocolForRouters

Technologies and Skills: Socket Programming, Python, Multithreading, TCP sockets

Description:
In this project, I have implemented distance-vector routing protocol for routers in a network. I have used python to implement it.

Details:
The file "Node.py" is run separately for every node (router) in the network. The nodes will then start communicating asynchronously using TCP sockets. When there are no more updates to be made in any of the distance vectors of the nodes, the algorithm will terminate. This will be done by "runner.sh".
