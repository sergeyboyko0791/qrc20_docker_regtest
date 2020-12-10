To build test blockchain docker image (--no-cache flag is optional when you making some changes in deps mostly):

`docker build -f Dockerfile.blockchain --no-cache -t qtumregtest .`

Run as (exposes single node on port 7000 to connect to):

`docker run -p 127.0.0.1:7000:7000 -e CLIENTS=2 -e COIN_RPC_PORT=7000 -e ADDRESS_LABEL='your label' qtumregtest`

With startup params as in example above RPC will be available for qtum-cli on port 7000 with the `rpcuser=test` and `rpcpassword=test` credentials.

`qtum-cli --rpcconnect='127.0.0.1' --rpcport=7000 --rpcpassword=test --rpcuser=test help`

To create QRC20 token:

1. Copy and edit the token code at [QRC20Token](https://github.com/qtumproject/QRC20Token). After editing the Solidity file, use [Remix](http://remix.ethereum.org/) to compile the Solidity code into bytecode.

2. Use `ADDRESS_LABEL` passed into the `docker run` to get the assigned address with some spandable Qtum amount:

`qtum-cli --rpcconnect='127.0.0.1' --rpcport=7000 --rpcpassword=test --rpcuser=test getaddressesbylabel 'your label'`

3. Do `createcontract` call with the compiled bytecode using the address assigned to `ADDRESS_LABEL` as a sender.

`qtum-cli --rpcconnect='127.0.0.1' --rpcport=7000 --rpcpassword=test --rpcuser=test createcontract 2500000 0.0000004 qXxsj5RtciAby9T7m98AgAATL4zTi4UwDG`

Where the `gas_limit=2500000`, `gas_price=0.0000004`, `qXxsj5RtciAby9T7m98AgAATL4zTi4UwDG` assigned to `ADDRESS_LABEL`.

