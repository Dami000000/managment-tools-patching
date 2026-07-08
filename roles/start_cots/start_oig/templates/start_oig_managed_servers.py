from java.lang import Thread, Runnable

class ServerStarter(Runnable):
    def __init__(self, server):
        self.server = server

    def run(self):
        try:
            print("Checking state of", self.server)
            server_state = state(self.server, 'Server', returnMap='true')
            if server_state[self.server] == 'RUNNING':
                print(self.server, "is already running.")
            else:
                print("Starting", self.server)
                start(self.server, 'Server')
        except:
            print("Error starting server:", self.server)

connect("{{ oig_wls_user }}", "{{ oig_wls_password }}", "{{ oig_admin_server_url }}:{{ oig_admin_server_port }}")

servers = ["{{ oig_managed_servers_node1[0].managed_server_node1 }}", "{{ oig_managed_servers_node2[0].managed_server_node2 }}"]

threads = []
for server in servers:
    starter = ServerStarter(server)
    thread = Thread(starter)
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

disconnect()
