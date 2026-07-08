from java.lang import Thread, Runnable

class ServerStopper(Runnable):
    def __init__(self, server):
        self.server = server

    def run(self):
        try:
            print("Checking state of", self.server)
            server_state = state(self.server, 'Server', returnMap='true')
            if server_state[self.server] == 'SHUTDOWN':
                print(self.server, "is already shut down.")
            else:
                print("Stopping", self.server, "with force flag")
                shutdown(self.server, 'Server', force='true')
        except:
            print("Error stopping server:", self.server)

connect("{{ oig_wls_user }}", "{{ oig_wls_password }}", "{{ oig_admin_server_url }}:{{ oig_admin_server_port }}")

servers = ["{{ oig_managed_servers_node1[1].managed_server_node1 }}", "{{ oig_managed_servers_node2[1].managed_server_node2 }}"]

threads = []
for server in servers:
    stopper = ServerStopper(server)
    thread = Thread(stopper)
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

disconnect()
