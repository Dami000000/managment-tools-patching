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

connect('{{ oam_wls_user }}', '{{ oam_wls_password }}', '{{ oam_admin_server_url }}:{{ oam_admin_server_port }}')

servers = ['{{ oam_managed_servers_node1[0].managed_server_node1 }}', '{{ oam_managed_servers_node1[1].managed_server_node1 }}']

threads = []
for server in servers:
    starter = ServerStarter(server)
    thread = Thread(starter)
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

disconnect()
