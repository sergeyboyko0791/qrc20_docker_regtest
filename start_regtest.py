import json
import os
import sys
import subprocess
from subprocess import PIPE
import time
import threading

class Node:
    def __init__(self, node_root, bin_path, port, rpc_port):
        self.node_root = node_root
        self.bin_path = bin_path
        self.conf = self.node_root + '/qtum.conf'
        self.port = port
        self.rpc_user = 'test'
        self.rpc_password = 'test'
        self.rpc_port = rpc_port

    def cli_cmd(self, command, args = [], attempts = 4, interval_s = 1):
        assert attempts > 0
        result = None
        for attempt in range(attempts):
            result = self.__cli_cmd_impl(command, args[:])
            if result.returncode == 0:
                return result
            else:
                attempts_left = attempts - attempt - 1
                print("Client command error [command: {}] [args: {}] [attempts left: {}].\nstdout: {}\nstderr: {}".format(command, args, attempts_left, result.stdout, result.stderr))
                time.sleep(interval_s)
        return result

    def __cli_cmd_impl(self, command, args = None):
        if args is None:
            args = []
        args.insert(0, self.bin_path + '/qtum-cli')
        args.insert(1, '-rpcport=' + str(self.rpc_port))
        args.insert(2, '-conf=' + self.conf)
        args.insert(3, command)
        return subprocess.run(args, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def run(self, connect_to = None):
        qtumd = self.bin_path + '/qtumd'
        args = [qtumd, '-conf=' + self.conf,
                   '-port=' + str(self.port), '-datadir=' + self.node_root,
                   '-whitelist=127.0.0.1', '-regtest', '-daemon']
        if connect_to is not None:
            args.append('-addnode=' + connect_to)

        print("Run QTUM node [args={}]".format(args))
        return subprocess.run(args, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def prepare_config(self):
        os.mkdir(self.node_root)
        open(self.conf, 'a').close()
        with open(self.conf, 'a') as conf:
            conf.write("server=1\n")
            conf.write("rpcuser=" + self.rpc_user + '\n')
            conf.write("rpcpassword=" + self.rpc_password + '\n')
            conf.write("rpcallowip=0.0.0.0/0\n")
            conf.write("logevents=1\n")
            conf.write("addressindex=1\n")
            conf.write("txindex=1\n")
            conf.write("[regtest]\n")
            conf.write("rpcport=" + str(self.rpc_port) + '\n')
            conf.write("[regtest]\n")
            conf.write("rpcbind=0.0.0.0\n")

# Fill the blockchain mempool by periodically sending transactions
def fill_mempool_loop(node):
    print("Start fill_mempool_loop")
    while True:
        assert node.cli_cmd('sendtoaddress', ['qeUbAVgkPiF62syqd792VJeB9BaqMtLcZV', "0.01"])
        time.sleep(0.1)

def check_mempool_loop(node, interval_s):
    print("Start check_mempool_loop")
    while True:
        result = node.cli_cmd('getmempoolinfo')
        assert result.returncode == 0
        data = json.loads(result.stdout)
        print(">>>> Mempool <<<<")
        print(data)
        time.sleep(interval_s)

ROOT = sys.path[0]
CLIENTS_TO_START = int(os.environ['CLIENTS'])
COIN_RPC_PORT = int(os.environ['COIN_RPC_PORT'])
ADDRESS_LABEL = os.environ['ADDRESS_LABEL']
FILL_MEMPOOL = os.getenv('FILL_MEMPOOL', 'false').lower() == 'true'
CHECK_MEMPOOL = os.getenv('CHECK_MEMPOOL', 'false').lower() == 'true'

nodes = []
for i in range(CLIENTS_TO_START):
    node_root = ROOT + '/node_' + str(i) + '/'
    bin_path = ROOT + '/bin/'
    port = 6000 + i
    rpc_port = COIN_RPC_PORT + i

    node = Node(node_root, bin_path, port, rpc_port)
    node.prepare_config()
    nodes.append(node)

first_node_address = None
for i, node in enumerate(nodes):
    if i == 0:
        first_node_address = '127.0.0.1:' + str(node.port)
        assert node.run().returncode == 0
    else:
        assert node.run(first_node_address).returncode == 0

time.sleep(2)

# Generate an address with the specified ADDRESS_LABEL that can be used to create token and send its tokens
print("\nNOTE: There will be several attempts to get a new address as the wallet may not have loaded yet\n")
result = nodes[0].cli_cmd('getnewaddress', [ADDRESS_LABEL], 20, 0.5)
assert result.returncode == 0
address = result.stdout.splitlines()[0]

print('Generate to address ' + address)
# node[0] will be used by integration tests to send Qtum amounts and deploy smart contracts
# so we should generate more than 500 blocks for the given address.
# For some reason, the first 499 blocks don't give rewards.
nodes[0].cli_cmd('generatetoaddress', [str(600), address])

print('config is ready')
time.sleep(0.5)

# Spawn the 'fill_mempool_loop' if it is required
if FILL_MEMPOOL:
    threading.Thread(target=fill_mempool_loop, args=(nodes[0],), daemon=True).start()

if CHECK_MEMPOOL:
    threading.Thread(target=check_mempool_loop, args=(nodes[0], 5,), daemon=True).start()

# starting blocks creation on last node
result = nodes[-1].cli_cmd('getnewaddress')
assert result.returncode == 0
address = result.stdout.splitlines()[0]
print('Starting blocks generation to address ' + address)
while True:
    assert nodes[-1].cli_cmd('generatetoaddress', [str(1), address]).returncode == 0
    time.sleep(2)
