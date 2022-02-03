import os
import time
import sys
import threading
import subprocess
from subprocess import PIPE

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

ROOT = sys.path[0]
CLIENTS_TO_START = int(os.environ['CLIENTS'])
COIN_RPC_PORT = int(os.environ['COIN_RPC_PORT'])
ADDRESS_LABEL = os.environ['ADDRESS_LABEL']
FILL_MEMPOOL = os.getenv('FILL_MEMPOOL', 'false').lower() == 'true'

nodes = []
for i in range(CLIENTS_TO_START):
    node_root = ROOT + '/node_' + str(i) + '/'
    bin_path = ROOT + '/bin/'
    port = 6000 + i
    rpc_port = COIN_RPC_PORT + i

    node = Node(node_root, bin_path, port, rpc_port)
    node.prepare_config()
    nodes.append(node)

print('config is ready')

first_node_address = None
for i, node in enumerate(nodes):
    if i == 0:
        first_node_address = '127.0.0.1:' + str(node.port)
        assert node.run().returncode == 0
    else:
        assert node.run(first_node_address).returncode == 0
    time.sleep(5)

# Generate an address with the specified ADDRESS_LABEL that can be used to create token and send its tokens
result = nodes[0].cli_cmd('getnewaddress', [ADDRESS_LABEL])
assert result.returncode == 0
address = result.stdout.splitlines()[0]
print('Generate to address ' + address)

# node[0] will be used by integration tests to send Qtum amounts and deploy a smart contract
# so we should generate more than 2000 blocks for the given address.
# For some reason, the first 1999 blocks don't give rewards.
nodes[0].cli_cmd('generatetoaddress', [str(2100), address])

time.sleep(0.5)

# Spawn the 'fill_mempool_loop' if it is required
if FILL_MEMPOOL:
    threading.Thread(target=fill_mempool_loop, args=(nodes[0],), daemon=True).start()

# starting blocks creation on last node
result = nodes[-1].cli_cmd('getnewaddress')
assert result.returncode == 0
address = result.stdout.splitlines()[0]
print('Starting blocks generation to address ' + address)
while True:
    assert nodes[-1].cli_cmd('generatetoaddress', [str(1), address]).returncode == 0
    time.sleep(2)
