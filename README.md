To build test blockchain docker image (--no-cache flag is optional when you making some changes in deps mostly):

`docker build -f Dockerfile.blockchain --no-cache -t testblockchain .`

Run as (exposes single node on port 7000 to connect to):

`docker run -p 127.0.0.1:7000:7000 -p 127.0.0.1:8000:8000 -p 127.0.0.1:50002:50002 -p 127.0.0.1:50001:50001 -e CLIENTS=2 -e CHAIN=TESTCHAIN -e TEST_ADDY=R9imXLs1hEcU9KbFDQq2hJEEJ1P5UoekaF -e TEST_WIF=UqqW7f766rADem9heD8vSBvvrdfJb3zg5r8du9rJxPtccjWf7RG9 -e TEST_PUBKEY=021607076d7a2cb148d542fb9644c04ffc22d2cca752f80755a0402a24c567b17a -e DAEMON_URL=http://test:test@127.0.0.1:7000 -e COIN=Komodo -e CHAIN_MODE=REGULAR -d --mount src=/home/username/.zcash-params,target=/data/.zcash-params,type=bind testblockchain`

Now it also starting SPV on top of testing chain. 2 chain modes are availiable (setting via CHAIN_MODE env): REGTEST and REGULAR
With startup params as in example above SPV will be available for TCP interaction on port 50001

Note that you should mount zcash-params from somewhere! As an alternative you might add fetch-params.sh to your zip with daemon and execute it before start_blockchain.py script start. But note that it'll consume A LOT of network traffic.
