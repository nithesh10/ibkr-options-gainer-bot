import random
from ib_insync import IB

def find_max_clients():
    clients = []
    max_clients = 0

    while True:
        try:
            random_id = random.randint(0, 9999)
            ib = IB()
            ib.connect('127.0.0.1', 7497, clientId=random_id) # Replace port_number with your port number
            clients.append(ib)
            max_clients += 1
            print(f"Connected client {max_clients}")
        except Exception as e:
            print(f"Failed to connect client {max_clients + 1}. Error: {e}")
            break

    # Optionally, disconnect all the clients
    for client in clients:
        client.disconnect()

    print(f"The maximum number of clients is {max_clients}")
    return max_clients

find_max_clients()
