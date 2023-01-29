# RoutingProtocolForRouters

Technologies and Skills: Socket Programming, Python, Multithreading, TCP sockets

Description:
In this project, I have implemented distance-vector routing protocol for routers in a network. I have used python to implement it.

Details:
The file "Node.py" is run separately for every node (router) in the network. The nodes will then start communication asynchronously using TCP sockets. When there are no more updates to be made in any of the distance vectors of the nodes, the algorithm will terminate. This will be done by "runner.sh".
Note: "runner.sh" file is for testing purposes. It is not implemented by me. It is provided as project tester by the teaching assistant. I have implement "Node.py" which is the project itself.
