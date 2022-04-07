# Run a a p2p network of 5 servers 
python3 server.py root $1 &
rootid=$!
python3 server.py server1 $1 &
server1id=$!
python3 server.py server2 $1 &
server2id=$!
python3 server.py server3 $1 &
server3id=$!
python3 server.py server4 $1 &
server4id=$!

sleep 1m

# Demonstrate root server failure
kill $rootid

# After 5 minutes stop the p2p network
sleep 10m

kill $server1id
kill $server2id
kill $server3id
kill $server4id