import hashlib
import bisect

class ConsistentHashing:
    def __init__(self, servers, num_replicas=3):
        self.num_replicas = num_replicas
        self.servers = set()
        self.ring = {}
        self.sorted_keys = []
        for server in servers:
            self._add_server(server)

    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_server(self, server):
        if server in self.servers:
            return
        self.servers.add(server)
        for i in range(self.num_replicas):
            key = f"{server}-{i}"
            hash_value = self._hash(key)
            bisect.insort(self.sorted_keys, hash_value)
            self.ring[hash_value] = server

    def remove_server(self, server):
        if server not in self.servers:
            return
        self.servers.remove(server)
        for i in range(self.num_replicas):
            key = f"{server}-{i}"
            hash_value = self._hash(key)
            self.sorted_keys.remove(hash_value)
            del self.ring[hash_value]
        print(f"Server {server} removed from the ring")

    def get_server(self, key):
        if not self.sorted_keys:
            return None
        hash_value = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, hash_value) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]

    def get_all_servers(self):
        return list(self.servers)

    def get_server_keys(self):
        return self.sorted_keys


if __name__ == "__main__":
# Initialize with servers
    servers = ["server1", "server2", "server3"]
    ch = ConsistentHashing(servers)
    print(ch.get_all_servers())
    print(ch.get_server_keys())
    ch.add_server("server4")
    print(ch.get_all_servers())
    print(ch.get_server_keys())
    ch.remove_server("server2")
    print(ch.get_all_servers())
    print(ch.get_server_keys())
